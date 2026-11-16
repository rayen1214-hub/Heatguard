"""Extra checks after the locked run. Plan: docs/posthoc_plan_v5.md (committed before running).

EXPLORATORY ONLY. The locked run of 16 Nov 2026 and its verdict are not touched:
this script never writes to outputs/v5 and never calls the locked run on it.

    python posthoc_v5.py data       # simulate the stress-test (P6) and other-seed (P7) sets
    python posthoc_v5.py analyse    # P1-P5 and P8 on the locked sets (no new simulation)
    python posthoc_v5.py f15        # P6: person-to-person differences x0.5 and x1.5
    python posthoc_v5.py f11        # P7: whole pipeline for 3 other seeds (smaller size)
    python posthoc_v5.py latency    # P9: time per message of the v0.5 engine
"""
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

import run_v5 as R
from heatguard import alerts, evaluate, features, v5, wearables, week8
from heatguard import config as C

PH = Path("outputs/v5_posthoc")
TRAIN_W, TEST_W = "data/weather_hourly.csv", "data/weather_hourly_2024.csv"
F15_SPREADS = (0.5, 1.5)
F11_SEEDS = (1305, 2305, 3305)
F11_SIZES = dict(train_workers=80, train_dates=20, test_workers=50, test_dates=20)
LOCKED_SCORES = Path("docs/results/v5_locked_2026-11-16/final_scores.csv.gz")
log = R.log


def _safe(out: Path) -> Path:
    assert out.resolve() != R.OUT.resolve(), "never write into the locked output folder"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _cached_twl(hourly: pd.DataFrame) -> pd.Series:
    """The TWL of each weather hour depends on the weather only, so reuse the values computed for
    the locked sets instead of recomputing them (saves several minutes per set)."""
    year = int(hourly["timestamp"].dt.year.iloc[0])
    f = R.OUT / ("train_twl_hourly.csv" if year == 2025 else "test_twl_hourly.csv")
    return pd.read_csv(f, parse_dates=["timestamp"]).set_index("timestamp")["twl"]


def humidex(tdb, rh):
    """The Dubai guideline's chart values (DM-HSD-GU38, Annex A) follow this formula:
    35 C / 50 % -> 45, 38/40 -> 47, 40/30 -> 47, 42/25 -> 48, 30/70 -> 41 (all five cells checked)."""
    e = 6.112 * 10 ** (7.5 * tdb / (237.7 + tdb)) * rh / 100
    return tdb + 0.5555 * (e - 10)


def locked_model():
    wk, ix, groups, _ = R.load_set("train", R.OUT)
    shifts = R.rows(wk, ix, groups)
    sel = pd.read_csv(R.OUT / "select_summary.csv").set_index("model").loc["logreg"]
    return R.fit("logreg", shifts), float(sel["threshold"]), int(sel["hold"]), shifts


# ------------------------------------------------------------------ data for P6 and P7
def stage_data():
    v5.twl_hourly = _cached_twl
    for f in F15_SPREADS:
        out = _safe(PH / f"f15_{int(f * 100):03d}")
        if not (out / "test_traj.parquet").exists():
            log(f"P6: test workers with differences x{f}")
            R.make_set("test", TEST_W, 100, 40, R.TEST_SEED, "X", out, spread=f)
    for seed in F11_SEEDS:
        out = _safe(PH / f"f11_seed{seed}")
        s = F11_SIZES
        if not (out / "train_traj.parquet").exists():
            log(f"P7 seed {seed}: training set")
            R.make_set("train", TRAIN_W, s["train_workers"], s["train_dates"], seed + 500, "T", out)
        if not (out / "test_traj.parquet").exists():
            log(f"P7 seed {seed}: test set")
            R.make_set("test", TEST_W, s["test_workers"], s["test_dates"], seed + 700, "X", out)
    log("data done")


# ------------------------------------------------------------------ P1-P5, P8
def _summ(df):
    d = evaluate.summarise(df)
    d.pop("lead_iqr", None)
    return d


def stage_analyse():
    out = _safe(PH / "analyse")
    res = {}
    model, thr, hold, tr = locked_model()
    wk_t, ix_t, groups_t, twl_t = R.load_set("test", R.OUT)
    te = R.rows(wk_t, ix_t, groups_t)
    locked = pd.read_csv(LOCKED_SCORES)
    lc = locked[locked["scenario"] == "clean"]

    # --- P1: Dubai chart rule (C2b) on the locked test set, and reproduction check of HG
    rows_b, rows_hg, probs_te = [], [], []
    for s in te:
        t = s["traj"]
        working = (t["phase"] != "break").to_numpy()
        c2b = ((humidex(t["tdb"].to_numpy(), t["rh"].to_numpy()) >= v5.HI_WARN) & working).astype(int)
        key = {"worker_id": s["worker_id"], "date": s["date"]}
        rows_b.append({**key, **evaluate.score_shift(c2b, s["onset"], R.HORIZON)})
        p = model.predict_proba(s["feats"][R.FEATS])[:, 1]
        probs_te.append(p)
        rows_hg.append({**key, **evaluate.score_shift(R.hg_alert(p, thr, s, hold), s["onset"], R.HORIZON)})
    c2b, hg = pd.DataFrame(rows_b), pd.DataFrame(rows_hg)
    ref = lc[lc["policy"] == "hg"].set_index(["worker_id", "date"])
    chk = hg.set_index(["worker_id", "date"])
    same = int((chk["warning_minutes"] == ref["warning_minutes"].reindex(chk.index)).sum())
    res["reproduction"] = {"shifts": len(chk), "hg_shifts_identical_to_locked_scores": same}
    log(f"reproduction check: {same}/{len(chk)} HG shifts identical to the locked scores")
    swapped = []
    for sc in R.SCENARIOS:
        d = locked[(locked["scenario"] == sc) & (locked["policy"] != "c2_heat_index")]
        b = c2b.copy()
        b["scenario"], b["policy"] = sc, "c2_heat_index"      # C2b takes C2's place for the judge
        swapped.append(pd.concat([d, b[d.columns]], ignore_index=True))
    verdict_b = R.judge(pd.concat(swapped, ignore_index=True))
    res["P1_dubai_chart_rule"] = {"summary": _summ(c2b), "vs_hg": verdict_b["c2_heat_index"],
                                  "verdict_if_c2b_replaces_c2": verdict_b["verdict"],
                                  "locked_c2_summary": _summ(lc[lc["policy"] == "c2_heat_index"])}
    c2b.to_csv(out / "c2b_scores.csv", index=False)
    log(f"P1: {res['P1_dubai_chart_rule']['summary']}  verdict with C2b: {verdict_b['verdict']}")

    # --- P2: events nobody can catch (whole pre-event window inside the legal break)
    unc = set()
    for s in te:
        if s["onset"] is not None:
            w = s["traj"]["phase"].to_numpy()[max(0, s["onset"] - R.HORIZON):s["onset"]]
            if len(w) and (w == "break").all():
                unc.add((s["worker_id"], s["date"]))
    ev = lc[lc["event"]].copy()
    ev["uncatchable"] = [(a, b) in unc for a, b in zip(ev["worker_id"], ev["date"])]
    res["P2_uncatchable"] = {"events": int(ev[ev.policy == "hg"].shape[0]), "uncatchable": len(unc), "missed": {
        p: {"all": int(g["missed"].sum()), "catchable_only": int(g.loc[~g["uncatchable"], "missed"].sum())}
        for p, g in ev.groupby("policy")}}
    log(f"P2: {res['P2_uncatchable']}")

    # --- P3: alarm burden
    avail = {}
    for s in te:
        work = int((s["traj"]["phase"] != "break").sum())
        avail[(s["worker_id"], s["date"])] = s["onset"] if s["onset"] is not None else work
    tot = sum(avail.values())
    burden = {}
    for p, g in pd.concat([lc, c2b.assign(policy="c2b_dubai_chart", scenario="clean")]).groupby("policy"):
        caught = int((g["event"] & (g["missed"] == False)).sum())             # noqa: E712
        fe = int(g["false_episodes"].sum())
        burden[p] = {"share_of_working_minutes_in_warning": round(float(g["warning_minutes"].sum() / tot), 3),
                     "episodes_followed_by_event": round(caught / max(caught + fe, 1), 3),
                     "shifts_with_no_warning": round(float((g["warning_minutes"] == 0).mean()), 3)}
    res["P3_burden"] = burden
    log(f"P3: {burden}")

    # --- P8: sensor-fault finding from the locked scores
    base = lc[lc["policy"] == "hg"].set_index(["worker_id", "date"])["warning_minutes"]
    res["P8_fault_warning_growth"] = {}
    for sc in R.SCENARIOS[1:]:
        f = locked[(locked["scenario"] == sc) & (locked["policy"] == "hg")].set_index(["worker_id", "date"])["warning_minutes"]
        d = f - base.reindex(f.index)
        res["P8_fault_warning_growth"][sc] = {"shifts": len(d), "more_than_60_min": int((d > 60).sum()),
                                              "more_than_240_min": int((d > 240).sum()),
                                              "median_change": float(d.median()), "max_change": float(d.max())}
    log(f"P8: {res['P8_fault_warning_growth']}")

    # --- P5: simulated workers against field averages (training set)
    wk, ix, groups, _ = R.load_set("train", R.OUT)
    mx, hot, n_work, hr_sum, hr_n, hr_grp = [], 0, 0, 0.0, 0, {}
    per_worker = {}
    for s in tr:
        t = s["traj"]
        core = t["t_re"].to_numpy()
        work = (t["phase"] == "work").to_numpy()
        mx.append(np.nanmax(core))
        per_worker.setdefault(s["worker_id"], []).append(np.nanmax(core))
        hot += int(((core >= 38.0) & (core < 38.5) & work).sum())
        n_work += int(work.sum())
        h = s["feats"]["hr_last"].to_numpy()[work]
        hr_sum += float(np.nansum(h)); hr_n += int(np.isfinite(h).sum())
        g = hr_grp.setdefault(int(s["worker"]["work_rate_wm2"]), [0.0, 0])
        g[0] += float(np.nansum(h)); g[1] += int(np.isfinite(h).sum())
    mx = np.array(mx)
    res["P5_reference"] = {
        "worker_days": len(mx),
        "share_passing_38.0": round(float((mx >= 38.0).mean()), 3),
        "share_passing_38.3": round(float((mx >= 38.3).mean()), 3),
        "share_passing_38.5": round(float((mx >= 38.5).mean()), 3),
        "share_of_work_time_38.0_to_38.4": round(hot / n_work, 3),
        "workers_never_reaching_38.0": round(float(np.mean([max(v) < 38.0 for v in per_worker.values()])), 3),
        "mean_working_hr": round(hr_sum / hr_n, 1),
        "mean_working_hr_by_work_rate": {k: round(v[0] / v[1], 1) for k, v in sorted(hr_grp.items())},
        "mean_wbgt_08_16": round(float(np.mean([s["traj"]["wbgt"].to_numpy()[120:600].mean() for s in tr[::5]])), 1),
        "body_mass_loss_pct_end_of_day_median": round(float(np.median([s["traj"]["body_loss_pct"].iloc[-1] for s in tr])), 2),
    }
    log(f"P5: {res['P5_reference']}")

    # --- P4a: standardised coefficients of the locked model
    coef = pd.Series(model[-1].coef_[0], index=R.FEATS)
    group_of = {f: g for g, fs in features.FEATURE_GROUPS.items() for f in fs}
    group_of.update({"minute_of_day": "time", "heat_index": "environmental", "heat_index_mean60": "environmental",
                     "pace_gap15": "workload", "hr_rise": "physiological", "skin_rise": "physiological"})
    ct = pd.DataFrame({"feature": coef.index, "coef_per_sd": coef.round(3).values,
                       "group": [group_of[f] for f in coef.index]}).sort_values("coef_per_sd", key=abs, ascending=False)
    ct.to_csv(out / "coefficients.csv", index=False)
    share = ct.assign(a=ct["coef_per_sd"].abs()).groupby("group")["a"].sum()
    res["P4a_coefficient_share_by_group"] = (share / share.sum()).round(3).to_dict()
    res["P4a_top5"] = ct.head(5)[["feature", "coef_per_sd"]].values.tolist()
    log(f"P4a: {res['P4a_coefficient_share_by_group']}")
    (out / "analyse.json").write_text(json.dumps(res, indent=2, default=str))

    # --- P4b: variants, tuned on training workers with the locked rule (hold fixed at the locked 30 min)
    EXTRA_ENV = ["minute_of_day", "heat_index", "heat_index_mean60"]
    variants = {
        "full (locked inputs, re-tuned as a check)": R.FEATS,
        "weather + personal only (no wearable)": features.ENV + features.PERSONAL + features.WORKLOAD + EXTRA_ENV,
        "wearable + personal only (no weather)": features.PHYSIO + features.ACTIVITY + features.QUALITY
                                                 + features.PERSONAL + features.WORKLOAD
                                                 + ["minute_of_day", "pace_gap15", "hr_rise", "skin_rise"],
        "full without pace and activity inputs": [f for f in R.FEATS if f not in ("pace_gap15", "act_mean5", "act_mean15")],
    }
    max_miss = json.loads((R.OUT / "select.json").read_text())["max_miss"]
    R.HOLDS = (hold,)
    wids = np.array([s["worker_id"] for s in tr])
    res["P4b_variants"] = {}
    for name, cols in variants.items():
        def fit(shifts, cols=cols):
            X = pd.concat([s["feats"].iloc[::R.TRAIN_EVERY] for s in shifts], ignore_index=True)
            y = pd.concat([s["y"].iloc[::R.TRAIN_EVERY] for s in shifts], ignore_index=True)
            keep = y.notna()
            m = week8.make_model("logreg")
            m.fit(X.loc[keep, cols], y[keep])
            return m
        probs = [None] * len(tr)
        for trn, tst in GroupKFold(n_splits=5).split(wids, groups=wids):
            m = fit([tr[i] for i in trn])
            for i in tst:
                probs[i] = m.predict_proba(tr[i]["feats"][cols])[:, 1]
        (t, h), met, table = R.choose_threshold(probs, tr, max_miss)
        m = fit(tr)
        sc = pd.DataFrame([{"worker_id": s["worker_id"], "date": s["date"],
                            **evaluate.score_shift(R.hg_alert(m.predict_proba(s["feats"][cols])[:, 1], t, s, h),
                                                   s["onset"], R.HORIZON)} for s in te])
        best = table[(table["threshold"] == t) & (table["hold"] == h)].iloc[0]
        res["P4b_variants"][name] = {"inputs": len(cols), "threshold": t, "tuning_limit_met": bool(met),
                                     "train_oof": {"miss_rate": float(best["miss_rate"]),
                                                   "warning_min_per_shift": float(best["warning_min_per_shift"])},
                                     "test": _summ(sc)}
        log(f"P4b {name}: thr {t} met {met} test {res['P4b_variants'][name]['test']}")
        (out / "analyse.json").write_text(json.dumps(res, indent=2, default=str))
    log("analyse done")


# ------------------------------------------------------------------ P6
def stage_f15():
    model, thr, hold, _ = locked_model()
    res = {}
    for f in F15_SPREADS:
        out = PH / f"f15_{int(f * 100):03d}"
        wk, ix, groups, twl_h = R.load_set("test", out)
        scores = R.score_set(wk, ix, groups, twl_h, model, thr, hold)
        scores.to_csv(out / "scores.csv", index=False)
        v = R.judge(scores)
        summ = {p: _summ(g) for p, g in scores[scores["scenario"] == "clean"].groupby("policy")}
        res[str(f)] = {"verdict": v["verdict"], "judge": v, "summary": summ}
        (out / "result.json").write_text(json.dumps(res[str(f)], indent=2, default=str))
        log(f"P6 spread x{f}: {v['verdict']}; events {v['events']}; "
            + "; ".join(f"{p} missed {s['missed']} warn {s['warning_min_per_shift']:.0f}" for p, s in summ.items()))


# ------------------------------------------------------------------ P7
def stage_f11():
    for seed in F11_SEEDS:
        out = _safe(PH / f"f11_seed{seed}")
        log(f"P7 seed {seed}: tuning on its own training workers, then one scoring of its own test workers")
        R.stage_select(out)
        R.stage_final(out, smoke=True)     # smoke=True only skips the lock; `out` is never the locked folder


# ------------------------------------------------------------------ P9
def stage_latency():
    model, thr, hold, _ = locked_model()
    wk_t, ix_t, groups_t, _ = R.load_set("test", R.OUT)
    times = []
    for r in ix_t[ix_t["valid"]].iloc[:5].itertuples(index=False):
        traj, worker = groups_t[(r.worker_id, r.date)], R.worker_row(wk_t, r.worker_id)
        seed = C.SEED + zlib.crc32(f"{r.worker_id}|{r.date}".encode()) % 10_000
        msgs = wearables.make_messages(traj, worker, seed).reset_index(drop=True)
        from heatguard import baseline
        rule = baseline.wbgt_rule(traj["wbgt"], traj["met_wm2"], worker)
        latch = 0
        for t in range(len(msgs)):
            start = time.perf_counter()
            lo = max(0, t - 60)                       # the engine keeps the last hour of readings
            f = R.add_extra(features.build_features(msgs.iloc[lo:t + 1], traj[["wbgt", "tdb", "rh"]].iloc[lo:t + 1], worker),
                            traj.iloc[lo:t + 1], worker).iloc[[-1]]
            p = model.predict_proba(f[R.FEATS])[:, 1]
            pol = alerts.run_policies(p, thr, rule["wbgt_alert"].iloc[[t]].reset_index(drop=True), f)
            latch = hold if int(pol["ml_fallback"].iloc[0]) else max(0, latch - 1)
            _ = (latch > 0 or traj["heat_index"].iloc[t] >= v5.HI_CEILING) and traj["phase"].iloc[t] != "break"
            times.append((time.perf_counter() - start) * 1000)
    a = np.array(times)
    out = _safe(PH / "analyse")
    res = {"messages": int(a.size), "median_ms": round(float(np.median(a)), 2), "p95_ms": round(float(np.percentile(a, 95)), 2),
           "max_ms": round(float(a.max()), 2), "budget_ms": 60000, "machine": "cloud build machine, 1 thread"}
    (out / "latency.json").write_text(json.dumps(res, indent=2))
    log(f"P9: {res}")


def stage_faultdiag():
    """NOT in the committed plan: added on 17 Nov after P8 showed extra warnings after sensor faults.
    Splits the extra warning minutes of every 8th test shift into three windows after the fault starts
    at minute 60: (a) the fault itself plus the 30-minute hold, (b) the next 15 minutes plus hold, while
    the 15-minute heart-rate trend still contains stale readings, (c) the rest of the day, where only
    the lowered 'lowest heart rate so far today' baseline can still act."""
    model, thr, hold, _ = locked_model()
    wk_t, ix_t, groups_t, _ = R.load_set("test", R.OUT)
    rows, fault_len = [], {"S5_dropout": 10, "S6_stuck": 15}
    for r in ix_t[ix_t["valid"]].iloc[::8].itertuples(index=False):
        traj, worker = groups_t[(r.worker_id, r.date)], R.worker_row(wk_t, r.worker_id)
        end = len(traj) if pd.isna(r.onset) else int(r.onset)
        got = {}
        for scen in ("clean", "S5_dropout", "S6_stuck"):
            feats, rule = R.shift_inputs(traj, worker, scen)
            prob = model.predict_proba(feats[R.FEATS])[:, 1]
            got[scen] = (np.asarray(R.hg_alert(prob, thr, dict(traj=traj, worker=worker, feats=feats, rule=rule), hold)),
                         float(feats["hr_mean15"].min()))
        for scen, n in fault_len.items():
            extra = (got[scen][0] - got["clean"][0])[:end]
            a_end, b_end = 60 + n + hold, 60 + n + 15 + hold
            rows.append({"scenario": scen, "total": extra.sum(), "fault_and_hold": extra[60:a_end].sum(),
                         "stale_trend": extra[a_end:b_end].sum(), "rest_of_day": extra[b_end:].sum(),
                         "baseline_drop_bpm": got["clean"][1] - got[scen][1]})
    d = pd.DataFrame(rows)
    res = {}
    for scen, g in d.groupby("scenario"):
        low = g["baseline_drop_bpm"] > 1.0
        res[scen] = {"shifts": int(len(g)), "mean_extra_minutes": round(float(g["total"].mean()), 1),
                     "of_which_fault_and_hold": round(float(g["fault_and_hold"].mean()), 1),
                     "of_which_stale_trend_window": round(float(g["stale_trend"].mean()), 1),
                     "of_which_rest_of_day": round(float(g["rest_of_day"].mean()), 1),
                     "share_of_shifts_with_baseline_lowered_by_more_than_1_bpm": round(float(low.mean()), 3),
                     "rest_of_day_extra_when_baseline_lowered": round(float(g.loc[low, "rest_of_day"].mean()), 1),
                     "rest_of_day_extra_when_not": round(float(g.loc[~low, "rest_of_day"].mean()), 1)}
    out = _safe(PH / "analyse")
    d.to_csv(out / "fault_diagnostic.csv", index=False)
    (out / "fault_diagnostic.json").write_text(json.dumps(res, indent=2))
    log(f"fault diagnostic (not in the plan): {res}")


if __name__ == "__main__":
    {"data": stage_data, "analyse": stage_analyse, "f15": stage_f15, "f11": stage_f11,
     "latency": stage_latency, "faultdiag": stage_faultdiag}[sys.argv[1]]()
