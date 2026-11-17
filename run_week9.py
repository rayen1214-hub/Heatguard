"""Week 9 iteration (v0.4), run AFTER run_pilot.py. Nothing in the Week 7 or Week 8 files changes.

    python run_week9.py --run outputs/full                         # real weather results
    python run_week9.py --run outputs/full_TEST_SYNTHETIC --quick  # code check only

What changes compared with Week 8 (reasons in docs/analysis_plan_week9.md):
  1. More events to pick each threshold. Week 8 tuned on 4 or 22 events; every miss came from the
     fold tuned on 4. Week 9 adds out-of-fold predictions for the TRAINING shifts (5 groups of
     workers, each predicted by a model that never saw them), so the threshold is tuned on the
     training events + the other unseen partition. The scored partition is never used for tuning.
  2. A threshold rule that matches the question: among thresholds that miss NO tuning event
     AND keep the median lead within LEAD_MARGIN of the 30-minute horizon, take the one with the
     fewest false episodes (then fewest warning minutes).
  2b. Primary model fixed in advance on TRAINING workers only (--oof-only): logistic regression with the
     Week 8 inputs. Alternative inputs (v1b, v2 in heatguard/week9.py) were tested and not adopted.
  3. Judged by the pre-declared rule (docs/analysis_plan_week9.md): SAFETY gate (no more missed
     events than WBGT, lead time within 5 min) + PRECISION win (fewer warning minutes, 95% CI above 0,
     and no more false episodes). WBGT always reaches the 30-minute lead cap, so "earlier" can't be shown.
  5. --confirm: brand-new workers on unused dates, scored once at the end (make_confirmation_set.py).
  4. Reference check: the simulated workers compared with published field studies (reference_check.py).

Outputs go to <run>/week9/.
"""
from __future__ import annotations

import argparse
import json
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from heatguard import alerts, baseline, evaluate, features, model, wearables, week8, week9
from heatguard import config as C

SCENARIOS = ["clean", "S5_dropout", "S5_missing10", "S5_missing30", "S6_stuck", "S7_noise"]
FOLDS = {"A": (["val"], "test"), "B": (["test"], "val")}   # (unseen partitions added to tuning, scored partition)
CONFIRM = {"confirm": (["val", "test"], "confirm")}       # final check: tune on everything, score new workers
N_GROUPS = 5            # worker groups for the out-of-fold training predictions
MAX_MISS = 0.0          # safety first: the tuning threshold must catch every tuning event (Week 8 used 5%)
LEAD_MARGIN = 5.0       # minutes; same margin as the non-inferiority rule
CANDIDATES = np.round(np.arange(0.02, 0.99, 0.02), 2)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def choose_threshold_v2(score_fn, horizon):
    """Fewest false episodes among thresholds that miss no tuning event (MAX_MISS) and keep the median lead
    >= horizon - margin.
    If none qualifies: fewest misses, then longest lead, then fewest false episodes (flagged)."""
    table = pd.DataFrame([{"threshold": t, **score_fn(t)} for t in CANDIDATES])
    ok = table[(table["miss_rate"] <= MAX_MISS) & (table["median_lead"] >= horizon - LEAD_MARGIN)]
    if len(ok):
        best = ok.sort_values(["false_per_shift", "warning_min_per_shift"]).iloc[0]
        met = True
    else:
        best = table.sort_values(["miss_rate", "median_lead", "false_per_shift"],
                                 ascending=[True, False, True]).iloc[0]
        met = False
    return float(best["threshold"]), met, table


def summarise_and_judge(scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summary per scenario x policy, and the pre-declared verdict (docs/analysis_plan_week9.md):
    each model + fallback vs WBGT, clean sensors."""
    summ = (scores.groupby(["scenario", "policy"])
            .apply(lambda d: pd.Series(evaluate.summarise(d)), include_groups=False).reset_index())
    summ = summ.drop(columns=["lead_iqr"])
    clean = scores[scores["scenario"] == "clean"]
    s_all = summ[summ["scenario"] == "clean"].set_index("policy")
    w = s_all.loc["wbgt_rule"]
    verdicts = []
    for name in week8.MODELS:
        p = f"fallback_{name}"
        d = week8.paired_differences(clean, p, "wbgt_rule")
        lo, hi = week8.bootstrap_ci(d)
        r = s_all.loc[p]
        checks = {
            "no_more_misses": int(r["missed"]) <= int(w["missed"]),
            "lead_noninferior": lo >= -LEAD_MARGIN,
        }
        # Precision: paired per-shift reductions vs WBGT (WBGT minus policy), mean with bootstrap 95% CI
        both = clean[clean["policy"].isin([p, "wbgt_rule"])].pivot_table(
            index=["fold", "worker_id", "date"], columns="policy", values=["warning_minutes", "false_episodes"])
        wm_red = (both[("warning_minutes", "wbgt_rule")] - both[("warning_minutes", p)]).astype(float)
        fe_red = (both[("false_episodes", "wbgt_rule")] - both[("false_episodes", p)]).astype(float)
        wm_lo, wm_hi = week8.bootstrap_ci(wm_red, stat=np.mean)
        fe_lo, fe_hi = week8.bootstrap_ci(fe_red, stat=np.mean)
        caught = max(int(r["events"]) - int(r["missed"]), 1)
        caught_w = max(int(w["events"]) - int(w["missed"]), 1)
        n_shifts = int(r["shifts"])
        checks["fewer_warning_minutes"] = wm_lo > 0             # precision win: CI of the reduction above 0
        checks["no_more_false_episodes"] = fe_red.mean() >= 0   # and not more false alarm episodes
        safety = checks["no_more_misses"] and checks["lead_noninferior"]
        verdict = ("SUPPORTED" if all(checks.values()) else
                   "PARTLY SUPPORTED" if safety and checks["fewer_warning_minutes"] else "NOT SUPPORTED")
        extra = {"warning_min_reduction_mean": float(wm_red.mean()), "warning_min_reduction_ci95": (wm_lo, wm_hi),
                 "false_ep_reduction_mean": float(fe_red.mean()), "false_ep_reduction_ci95": (fe_lo, fe_hi),
                 "warning_min_per_caught_event": r["warning_min_per_shift"] * n_shifts / caught,
                 "wbgt_warning_min_per_caught_event": w["warning_min_per_shift"] * n_shifts / caught_w}
        verdicts.append({"policy": p, "events": len(d), "missed": int(r["missed"]), "wbgt_missed": int(w["missed"]),
                         "median_lead": r["median_lead"], "lead_diff_median": float(d.median()) if len(d) else np.nan,
                         "lead_diff_ci95_low": lo, "lead_diff_ci95_high": hi,
                         "false_per_shift": r["false_per_shift"], "wbgt_false_per_shift": w["false_per_shift"],
                         "warning_min_per_shift": r["warning_min_per_shift"],
                         "wbgt_warning_min_per_shift": w["warning_min_per_shift"], **extra, **checks, "verdict": verdict})
    return summ, pd.DataFrame(verdicts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="output folder of a finished run_pilot.py run")
    ap.add_argument("--horizon", type=int, default=C.HORIZONS_MIN[0])
    ap.add_argument("--quick", action="store_true", help="clean + S5_dropout only")
    ap.add_argument("--features", choices=["v1", "v1b", "v2"], default="v1",
                    help="v1 = Week 8 inputs; v1b = v1 without mass/height; v2 = v1b + rises (heatguard/week9.py)")
    ap.add_argument("--confirm", action="store_true",
                    help="ALSO score the confirmation set (make_confirmation_set.py). Do this once, at the end.")
    ap.add_argument("--oof-only", action="store_true",
                    help="model selection on TRAINING data only (out-of-fold); never looks at val/test")
    args = ap.parse_args()
    FEATS = {"v1": features.ALL_FEATURES, "v1b": week9.FEATURES_V1B, "v2": week9.FEATURES_V2}[args.features]
    build = week9.build_features_v2 if args.features == "v2" else features.build_features

    run = Path(args.run)
    out = run / f"week9_{args.features}"
    out.mkdir(exist_ok=True)
    wk = pd.read_csv(run / "workers.csv").set_index("worker_id")
    index = pd.read_csv(run / "shift_index.csv")
    trajs = pd.read_csv(run / "trajectories.csv.gz", parse_dates=["timestamp"])
    if args.confirm:
        c = run / "confirm"
        wk = pd.concat([wk, pd.read_csv(c / "workers.csv").set_index("worker_id")])
        index = pd.concat([index, pd.read_csv(c / "shift_index.csv")], ignore_index=True)
        trajs = pd.concat([trajs, pd.read_csv(c / "trajectories.csv.gz", parse_dates=["timestamp"])], ignore_index=True)
    index["onset"] = index["onset"].astype("Int64")
    groups = {k: g.reset_index(drop=True) for k, g in trajs.groupby(["worker_id", "date"])}
    synthetic = "SYNTHETIC" in run.name
    scenarios = ["clean", "S5_dropout"] if args.quick else SCENARIOS
    H, gain = args.horizon, C.HR_THERMAL_GAIN
    log(f"features {args.features}; run {run} ({'SYNTHETIC: code check only' if synthetic else 'real weather'}), horizon {H} min")

    def worker_of(wid):
        w = wk.loc[wid].copy()
        w["worker_id"] = wid
        return w

    def shifts(part, scenario):
        """Features, labels and the WBGT rule for every valid shift in one partition (same seeds as Week 7/8)."""
        rows = []
        for r in index[(index["partition"] == part) & index["valid"]].itertuples(index=False):
            traj, worker = groups[(r.worker_id, r.date)], worker_of(r.worker_id)
            seed = C.SEED + zlib.crc32(f"{r.worker_id}|{r.date}".encode()) % 10_000
            clean = wearables.make_messages(traj, worker, seed, thermal_gain=gain)
            if scenario == "S7_noise":
                msgs = wearables.make_messages(traj, worker, seed, hr_noise=8.0, skin_noise=0.5, thermal_gain=gain)
            else:
                msgs = wearables.inject_fault(clean, scenario, seed, worker=worker, traj=traj)
            feats = build(msgs, traj[["wbgt", "tdb", "rh"]], worker)
            rule = baseline.wbgt_rule(traj["wbgt"], traj["met_wm2"], worker)
            onset = None if pd.isna(r.onset) else int(r.onset)
            rows.append(dict(worker_id=r.worker_id, date=r.date, onset=onset, feats=feats, rule=rule,
                             y=features.make_labels(len(feats), onset, H)))
        return rows

    def stack(rows):
        X = pd.concat([s["feats"] for s in rows], ignore_index=True)
        y = pd.concat([s["y"] for s in rows], ignore_index=True)
        g = np.concatenate([[s["worker_id"]] * len(s["feats"]) for s in rows])
        keep = y.notna().to_numpy()
        return X.loc[keep, FEATS], y[keep], g[keep]

    train = shifts("train", "clean")
    X, y, g = stack(train)
    if y.nunique() < 2:
        log("STOP: no danger events in training data")
        return
    parts = ("val", "test", "confirm") if args.confirm else ("val", "test")
    clean_eval = {p: shifts(p, "clean") for p in parts}
    n_ev = {"train": sum(s["onset"] is not None for s in train),
            **{p: sum(s["onset"] is not None for s in clean_eval[p]) for p in parts}}
    log("danger events: " + ", ".join(f"{k} {v}" for k, v in n_ev.items()))

    # Out-of-fold probabilities for every training shift: each one predicted by a model that never saw its worker
    worker_ids = np.array(sorted({s["worker_id"] for s in train}))
    gkf = GroupKFold(n_splits=min(N_GROUPS, len(worker_ids)))
    oof = {name: {} for name in week8.MODELS}
    for k, (tr_w, ho_w) in enumerate(gkf.split(worker_ids, groups=worker_ids)):
        held = set(worker_ids[ho_w])
        m = ~np.isin(g, list(held))
        for name in week8.MODELS:
            clf = week8.make_model(name).fit(X[m], y[m])
            for s in train:
                if s["worker_id"] in held:
                    oof[name][(s["worker_id"], s["date"])] = model.predict_proba(clf, s["feats"][FEATS])
        log(f"out-of-fold group {k + 1}: {len(held)} workers predicted")

    if args.oof_only:
        rows = []
        for name in week8.MODELS:
            probs = [(oof[name][(s["worker_id"], s["date"])], s["onset"]) for s in train]

            def score_fn(t, probs=probs):
                return evaluate.summarise(pd.DataFrame(
                    [evaluate.score_shift((p >= t).astype(int), o, H) for p, o in probs]))
            t, met, table = choose_threshold_v2(score_fn, H)
            best = table[table["threshold"] == t].iloc[0]
            rows.append({"features": args.features, "model": name, "threshold": t, "constraint_met": met,
                         **{k: best[k] for k in ("events", "missed", "median_lead", "false_per_shift",
                                                 "warning_min_per_shift")}})
        res = pd.DataFrame(rows)
        res.to_csv(out / "oof_selection.csv", index=False)
        log("OUT-OF-FOLD (training workers only):\n" + res.round(2).to_string(index=False))
        return

    fitted = {}
    for name in week8.MODELS:
        t0 = time.time()
        fitted[name] = week8.make_model(name).fit(X, y)
        log(f"trained {name} on {len(y)} minutes ({int(y.sum())} positive) in {time.time() - t0:.0f} s")

    all_scores, thresholds, tables = [], [], []
    designs = {**FOLDS, **(CONFIRM if args.confirm else {})}
    for fold, (extra, score_on) in designs.items():
        thr = {}
        for name, clf in fitted.items():
            probs = [(oof[name][(s["worker_id"], s["date"])], s["onset"]) for s in train]
            probs += [(model.predict_proba(clf, s["feats"][FEATS]), s["onset"])
                      for e in extra for s in clean_eval[e]]
            n_tune = sum(o is not None for _, o in probs)

            def score_fn(t, probs=probs):
                return evaluate.summarise(pd.DataFrame(
                    [evaluate.score_shift((p >= t).astype(int), o, H) for p, o in probs]))
            thr[name], met, table = choose_threshold_v2(score_fn, H)
            table.insert(0, "model", name)
            table.insert(0, "fold", fold)
            tables.append(table)
            thresholds.append({"fold": fold, "model": name, "tuned_on": "train (out-of-fold) + " + " + ".join(extra),
                               "tuning_events": n_tune, "threshold": thr[name], "constraint_met": met})
        for scenario in scenarios:
            ev = clean_eval[score_on] if scenario == "clean" else shifts(score_on, scenario)
            for s in ev:
                base = dict(fold=fold, scenario=scenario, worker_id=s["worker_id"], date=s["date"])
                all_scores.append({**base, "policy": "wbgt_rule",
                                   **evaluate.score_shift(s["rule"]["wbgt_alert"].clip(lower=0).to_numpy(),
                                                          s["onset"], H)})
                for name, clf in fitted.items():
                    prob = model.predict_proba(clf, s["feats"][FEATS])
                    pol = alerts.run_policies(prob, thr[name], s["rule"]["wbgt_alert"], s["feats"])
                    all_scores.append({**base, "policy": f"ml_{name}",
                                       **evaluate.score_shift(pol["ml"].to_numpy(), s["onset"], H)})
                    all_scores.append({**base, "policy": f"fallback_{name}",
                                       **evaluate.score_shift(pol["ml_fallback"].to_numpy(), s["onset"], H)})
        log(f"{fold}: tuned on train (out-of-fold) + {'+'.join(extra)}, scored on {score_on}: "
            + ", ".join(f"{k} {v}" for k, v in thr.items()))

    scores = pd.DataFrame(all_scores)
    scores.to_csv(out / "scores_week9.csv", index=False)
    pd.DataFrame(thresholds).to_csv(out / "thresholds_week9.csv", index=False)
    pd.concat(tables).to_csv(out / "threshold_tables_week9.csv", index=False)

    main_scores = scores[scores["fold"].isin(list(FOLDS))]
    summ, verdicts = summarise_and_judge(main_scores)
    summ.to_csv(out / "summary_week9.csv", index=False)
    verdicts.to_csv(out / "verdict_week9.csv", index=False)
    if args.confirm:
        csumm, cverdicts = summarise_and_judge(scores[scores["fold"] == "confirm"])
        csumm.to_csv(out / "summary_confirm.csv", index=False)
        cverdicts.to_csv(out / "verdict_confirm.csv", index=False)

    info = {"run": str(run), "synthetic_weather": synthetic, "horizon_min": H, "hr_gain": gain,
            "lead_margin_min": LEAD_MARGIN, "max_miss_rate": MAX_MISS, "events": n_ev,
            "folds": designs, "models": list(week8.MODELS), "scenarios": scenarios}
    (out / "week9_info.json").write_text(json.dumps(info, indent=2))

    pd.set_option("display.width", 200)
    log("THRESHOLDS:\n" + pd.DataFrame(thresholds).to_string(index=False))
    show = summ[summ["scenario"] == "clean"][["policy", "events", "missed", "median_lead",
                                               "false_per_shift", "warning_min_per_shift"]]
    log("RESULTS, clean sensors, both folds pooled" + (" (SYNTHETIC: code check only)" if synthetic else "")
        + ":\n" + show.round(2).to_string(index=False))
    log("VERDICT (pre-declared, docs/analysis_plan_week9.md):\n"
        + verdicts[["policy", "events", "missed", "wbgt_missed", "lead_diff_median", "lead_diff_ci95_low",
                    "false_per_shift", "warning_min_per_shift", "verdict"]].round(2).to_string(index=False))
    if args.confirm:
        log("CONFIRMATION SET (new workers, unused dates), verdict:\n"
            + cverdicts[["policy", "events", "missed", "wbgt_missed", "lead_diff_median", "lead_diff_ci95_low",
                         "false_per_shift", "warning_min_per_shift", "verdict"]].round(2).to_string(index=False))
    log(f"all tables written to {out}/")


if __name__ == "__main__":
    main()
