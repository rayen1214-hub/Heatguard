"""Week 9 frame v2 (v0.5): data, model choice on training workers, and the single locked run.

Stages, in this order (each one only reads what the stage before wrote):

    # STAGE 1 - simulate the data (no scoring of anything)
    python run_v5.py data   --train-weather data/weather_hourly.csv --test-weather data/weather_hourly_2024.csv

    # STAGE 2 - choose the model and threshold on TRAINING workers only (out-of-fold, 2025)
    python run_v5.py select

    # STAGE 3 - the single locked run on the 2024 test workers. Refuses to start unless the
    #           pre-registration file is committed, and refuses to run a second time.
    python run_v5.py final

    # Code check only (synthetic weather, tiny sizes, numbers mean nothing):
    python run_v5.py smoke

Decisions this follows (CR, 16 Nov 2026): comparators C1-C4, hypotheses H1-H6, safety
margin M = 2 points, ~200 training workers on summer 2025, ~100 new test workers on
summer 2024, full UAE day with the legal break, TWL rule, Heat Index 54+ ceiling.
"""
from __future__ import annotations

import os

if __name__ != "__main__":      # simulation worker processes: one thread each, so 4 processes do not fight
    for _v in ("OMP_NUM_THREADS", "NUMBA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[_v] = "1"

import argparse
import json
import multiprocessing
import subprocess
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.model_selection import GroupKFold

from heatguard import alerts, baseline, evaluate, features, v5, weather, week8, wearables
from heatguard import config as C

OUT = Path("outputs/v5")
PREREG = Path("docs/preregistration_v5.md")
HORIZON = 30
SIZES = {   # decision 2: the big data set
    "full":  dict(train_workers=200, train_dates=30, test_workers=100, test_dates=40),
    "smoke": dict(train_workers=12, train_dates=4, test_workers=6, test_dates=4),
}
TRAIN_SEED, TEST_SEED = C.SEED + 500, C.SEED + 700       # different people in train and test
MARGIN_M = 0.02                  # decision 2: sensitivity may be at most 2 points lower (CI bound)
LEAD_MARGIN = 5.0                # H4
H3_REDUCTION = 0.50              # H3: at least 50% fewer warning minutes
TUNE_MAX_MISS = 0.01             # threshold rule: catch at least 99% of training events (out-of-fold)
CANDIDATES = np.round(np.arange(0.02, 0.99, 0.02), 2)
TRAIN_EVERY = 3                  # fit on every 3rd minute (neighbouring minutes are near copies)
N_BOOT = 2000
SCENARIOS = ["clean", "S5_dropout", "S6_stuck"]
TRAJ_COLS = ["worker_id", "date", "minute", "timestamp", "phase", "met_wm2", "tdb", "rh", "wbgt",
             "heat_index", "wet_bulb", "t_cr", "t_sk", "t_re", "t_re_iso", "body_loss_pct", "valid"]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ---------------------------------------------------------------- STAGE 1: data
def _simulate_job(args):
    """One worker, all of their dates (runs in a separate process)."""
    hourly_path, worker, dates = args
    hourly = weather.load_hourly(hourly_path)
    trajs, index = [], []
    for d in dates:
        traj, onset = v5.simulate_day(worker, v5.day_minutes(hourly, d), d)
        traj["date"] = d
        trajs.append(traj[TRAJ_COLS])
        index.append({"worker_id": worker["worker_id"], "date": d, "onset": onset,
                      "valid": bool(traj["valid"].all()), "ban_day": v5.ban_applies(d),
                      "acclimatised": bool(worker["acclimatised"]), "work_rate_wm2": int(worker["work_rate_wm2"])})
    return pd.concat(trajs, ignore_index=True), pd.DataFrame(index)


def make_set(name, hourly_path, n_workers, n_dates, seed, prefix, out, spread=1.0):
    hourly = weather.load_hourly(hourly_path)
    wk = v5.scale_spread(v5.make_workers_v5(n_workers, seed=seed, prefix=prefix), spread)
    all_dates = sorted(hourly["timestamp"].dt.strftime("%Y-%m-%d").unique())
    rng = np.random.default_rng(seed + 1)
    jobs = []
    for _, w in wk.iterrows():           # each worker gets their own random set of dates
        jobs.append((str(hourly_path), w, sorted(rng.choice(all_dates, size=n_dates, replace=False).tolist())))
    trajs, index = [], []
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
        for i, (t, ix) in enumerate(pool.map(_simulate_job, jobs)):
            trajs.append(t)
            index.append(ix)
            if (i + 1) % 10 == 0:
                log(f"{name}: simulated {i + 1}/{len(jobs)} workers")
    out.mkdir(parents=True, exist_ok=True)
    wk.to_csv(out / f"{name}_workers.csv", index=False)
    pd.concat(index, ignore_index=True).to_csv(out / f"{name}_index.csv", index=False)
    pd.concat(trajs, ignore_index=True).to_parquet(out / f"{name}_traj.parquet", index=False)
    twl = v5.twl_hourly(hourly)
    twl.rename_axis("timestamp").reset_index().to_csv(out / f"{name}_twl_hourly.csv", index=False)


def stage_data(args, sizes, out):
    s = sizes
    log(f"TRAIN set: {s['train_workers']} workers x {s['train_dates']} dates, weather {args.train_weather}")
    make_set("train", args.train_weather, s["train_workers"], s["train_dates"], TRAIN_SEED, "T", out)
    log(f"TEST set (locked, not scored here): {s['test_workers']} workers x {s['test_dates']} dates, "
        f"weather {args.test_weather}")
    make_set("test", args.test_weather, s["test_workers"], s["test_dates"], TEST_SEED, "X", out)
    ix = pd.read_csv(out / "train_index.csv")
    log(f"TRAIN: {len(ix)} shifts, {int(ix['onset'].notna().sum())} danger events "
        f"({int((~ix['valid']).sum())} invalid shifts). Test event counts are not shown until the final run.")


# ---------------------------------------------------------------- shared: one shift -> features and policies
def load_set(name, out):
    wk = pd.read_csv(out / f"{name}_workers.csv").set_index("worker_id")
    ix = pd.read_csv(out / f"{name}_index.csv")
    ix["onset"] = ix["onset"].astype("Int64")
    traj = pd.read_parquet(out / f"{name}_traj.parquet")
    twl_h = pd.read_csv(out / f"{name}_twl_hourly.csv", parse_dates=["timestamp"]).set_index("timestamp")["twl"]
    groups = {k: g.reset_index(drop=True) for k, g in traj.groupby(["worker_id", "date"])}
    return wk, ix, groups, twl_h


def worker_row(wk, wid):
    w = wk.loc[wid].copy()
    w["worker_id"] = wid
    return w


def shift_inputs(traj, worker, scenario):
    seed = C.SEED + zlib.crc32(f"{worker['worker_id']}|{traj['date'].iloc[0]}".encode()) % 10_000
    msgs = wearables.inject_fault(wearables.make_messages(traj, worker, seed), scenario, seed, worker=worker, traj=traj)
    feats = features.build_features(msgs, traj[["wbgt", "tdb", "rh"]], worker)
    rule = baseline.wbgt_rule(traj["wbgt"], traj["met_wm2"], worker)
    return feats, rule


def rows(wk, ix, groups, scenario="clean"):
    out = []
    for r in ix[ix["valid"]].itertuples(index=False):
        traj, worker = groups[(r.worker_id, r.date)], worker_row(wk, r.worker_id)
        feats, rule = shift_inputs(traj, worker, scenario)
        onset = None if pd.isna(r.onset) else int(r.onset)
        out.append(dict(worker_id=r.worker_id, date=r.date, onset=onset, traj=traj, worker=worker,
                        feats=feats, rule=rule, y=features.make_labels(len(feats), onset, HORIZON)))
    return out


def fit(model_name, shifts):
    X = pd.concat([s["feats"].iloc[::TRAIN_EVERY] for s in shifts], ignore_index=True)
    y = pd.concat([s["y"].iloc[::TRAIN_EVERY] for s in shifts], ignore_index=True)
    keep = y.notna()
    m = week8.make_model(model_name)
    m.fit(X.loc[keep, features.ALL_FEATURES], y[keep])
    return m


def hg_alert(prob, thr, s):
    pol = alerts.run_policies(prob, thr, s["rule"]["wbgt_alert"], s["feats"])
    return v5.heatguard_alert(pol["ml_fallback"].to_numpy(), s["traj"])


def choose_threshold(probs, shifts):
    """Fewest false episodes (then fewest warning minutes) among thresholds that catch at least
    99% of tuning events with median lead >= 25 min. Same idea as Week 9, written before any test run."""
    rows_ = []
    for t in CANDIDATES:
        sc = pd.DataFrame([evaluate.score_shift(hg_alert(p, t, s), s["onset"], HORIZON) for p, s in zip(probs, shifts)])
        rows_.append({"threshold": t, **evaluate.summarise(sc)})
    table = pd.DataFrame(rows_).drop(columns=["lead_iqr"])
    ok = table[(table["miss_rate"] <= TUNE_MAX_MISS) & (table["median_lead"] >= HORIZON - LEAD_MARGIN)]
    if len(ok):
        best, met = ok.sort_values(["false_per_shift", "warning_min_per_shift"]).iloc[0], True
    else:
        best, met = table.sort_values(["miss_rate", "median_lead"], ascending=[True, False]).iloc[0], False
    return float(best["threshold"]), met, table


# ---------------------------------------------------------------- STAGE 2: model choice (training workers only)
def stage_select(out):
    wk, ix, groups, _ = load_set("train", out)
    shifts = rows(wk, ix, groups)
    wids = np.array([s["worker_id"] for s in shifts])
    log(f"out-of-fold selection on {len(shifts)} training shifts, {sum(s['onset'] is not None for s in shifts)} events")
    results, oof_all = [], {}
    for name in week8.MODELS:
        probs = [None] * len(shifts)
        for k, (tr, te) in enumerate(GroupKFold(n_splits=5).split(wids, groups=wids)):
            m = fit(name, [shifts[i] for i in tr])
            for i in te:
                probs[i] = m.predict_proba(shifts[i]["feats"][features.ALL_FEATURES])[:, 1]
            log(f"  {name}: fold {k + 1}/5 done")
        thr, met, table = choose_threshold(probs, shifts)
        table.insert(0, "model", name)
        table.to_csv(out / f"select_{name}_thresholds.csv", index=False)
        best = table[table["threshold"] == thr].iloc[0].to_dict()
        results.append({"model": name, "threshold": thr, "constraint_met": met, **best})
        oof_all[name] = probs
    res = pd.DataFrame(results)
    # Rule written before running: among models meeting the constraint, fewest warning minutes per shift
    ok = res[res["constraint_met"]]
    primary = (ok if len(ok) else res).sort_values("warning_min_per_shift").iloc[0]
    res["primary"] = res["model"] == primary["model"]
    res.to_csv(out / "select_summary.csv", index=False)
    (out / "select.json").write_text(json.dumps({"primary_model": primary["model"]}, indent=2))
    log("selection (training workers only, out-of-fold):\n" + res[["model", "threshold", "constraint_met", "missed",
        "events", "median_lead", "false_per_shift", "warning_min_per_shift", "primary"]].to_string(index=False))


# ---------------------------------------------------------------- STAGE 3: the single locked run
def worker_bootstrap(df, stat, n=N_BOOT, seed=C.SEED):
    """95% interval by resampling WORKERS (their shifts move together), so repeated shifts of
    one person do not count as independent evidence."""
    ids = df["worker_id"].unique()
    by = {w: g for w, g in df.groupby("worker_id")}
    rng = np.random.default_rng(seed)
    vals = [stat(pd.concat([by[w] for w in rng.choice(ids, len(ids), replace=True)])) for _ in range(n)]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def judge(scores):
    """H1-H6 exactly as in docs/preregistration_v5.md."""
    clean = scores[scores["scenario"] == "clean"]
    wide = clean.pivot_table(index=["worker_id", "date"], columns="policy",
                             values=["event", "missed", "lead_min", "warning_minutes", "false_episodes"],
                             aggfunc="first").reset_index()
    wide.columns = ["_".join(c).strip("_") for c in wide.columns]
    ev = wide[wide["event_hg"] == True].copy()     # noqa: E712
    caught = lambda p: (~ev[f"missed_{p}"].astype(bool)).astype(float)  # noqa: E731
    out = {"events": int(len(ev)), "shifts": int(len(wide))}
    sens = {p: float(caught(p).mean()) for p in ("hg", "c1_ban", "c2_heat_index", "c3_twl", "c4_wbgt")}
    out["sensitivity"] = sens
    d1 = lambda df: (~df["missed_hg"].astype(bool)).mean() - (~df["missed_c1_ban"].astype(bool)).mean()  # noqa: E731
    lo, hi = worker_bootstrap(ev, d1)
    out["H1"] = {"diff": sens["hg"] - sens["c1_ban"], "ci95": (lo, hi), "pass": lo > 0}
    for c in ("c2_heat_index", "c3_twl", "c4_wbgt"):
        res = {}
        f2 = lambda df, c=c: (~df["missed_hg"].astype(bool)).mean() - (~df[f"missed_{c}"].astype(bool)).mean()  # noqa: E731
        lo, hi = worker_bootstrap(ev, f2)
        res["H2"] = {"diff": sens["hg"] - sens[c], "ci95": (lo, hi), "pass": lo >= -MARGIN_M}
        f3 = lambda df, c=c: 1 - df["warning_minutes_hg"].sum() / max(df[f"warning_minutes_{c}"].sum(), 1)  # noqa: E731
        lo, hi = worker_bootstrap(wide, f3)
        fe = float(wide["false_episodes_hg"].mean() - wide[f"false_episodes_{c}"].mean())
        res["H3"] = {"reduction": f3(wide), "ci95": (lo, hi), "false_ep_diff": fe,
                     "pass": lo >= H3_REDUCTION and fe <= 0}
        f4 = lambda df, c=c: float((df["lead_min_hg"] - df[f"lead_min_{c}"]).median())  # noqa: E731
        lo, hi = worker_bootstrap(ev, f4)
        res["H4"] = {"median_diff": f4(ev), "ci95": (lo, hi), "pass": lo >= -LEAD_MARGIN}
        a = int(((ev[f"missed_{c}"].astype(bool)) & (~ev["missed_hg"].astype(bool))).sum())
        b = int(((~ev[f"missed_{c}"].astype(bool)) & (ev["missed_hg"].astype(bool))).sum())
        rule_missed = int(ev[f"missed_{c}"].astype(bool).sum())
        if rule_missed == 0:
            res["H6"] = {"a": a, "b": b, "p": None, "pass": "not testable"}
        else:
            p = binomtest(a, a + b, 0.5, alternative="greater").pvalue if a + b else 1.0
            res["H6"] = {"a": a, "b": b, "p": float(p), "pass": bool(a > b and p < 0.05)}
        out[c] = res
    # H5: H2 still holds with sensor faults
    out["H5"] = {}
    for sc in SCENARIOS[1:]:
        s = scores[scores["scenario"] == sc].pivot_table(index=["worker_id", "date"], columns="policy",
                                                         values=["event", "missed"], aggfunc="first").reset_index()
        s.columns = ["_".join(c).strip("_") for c in s.columns]
        e = s[s["event_hg"] == True]                   # noqa: E712
        res = {}
        for c in ("c2_heat_index", "c3_twl", "c4_wbgt"):
            f = lambda df, c=c: (~df["missed_hg"].astype(bool)).mean() - (~df[f"missed_{c}"].astype(bool)).mean()  # noqa: E731
            lo, hi = worker_bootstrap(e, f)
            res[c] = {"ci95": (lo, hi), "pass": lo >= -MARGIN_M}
        out["H5"][sc] = res
    rules = ("c2_heat_index", "c3_twl", "c4_wbgt")
    for c in rules:
        # A rule that warns rarely and misses many events cannot be beaten on "fewer warnings".
        # Against such a rule HG wins on safety instead: its sensitivity is clearly higher.
        out[c]["clearly_safer"] = out[c]["H2"]["ci95"][0] > 0
        out[c]["precision_or_safety"] = bool(out[c]["H3"]["pass"] or out[c]["clearly_safer"])
    h2 = all(out[c]["H2"]["pass"] for c in rules)
    h3 = all(out[c]["precision_or_safety"] for c in rules)
    out["verdict"] = ("GAP CLOSED" if out["H1"]["pass"] and h2 and h3 else
                      "PARTLY CLOSED" if out["H1"]["pass"] and h3 else "NOT CLOSED")
    return out


def score_set(wk, ix, groups, twl_h, model, thr):
    scores = []
    for sc in SCENARIOS:
        for s in rows(wk, ix, groups, sc):
            prob = model.predict_proba(s["feats"][features.ALL_FEATURES])[:, 1]
            comp = v5.comparator_alerts(s["traj"], s["worker"], v5.twl_minutes(twl_h, s["traj"]["timestamp"]),
                                        s["rule"]["wbgt_alert"].to_numpy())
            pols = {"hg": hg_alert(prob, thr, s), **{c: comp[c].to_numpy() for c in
                    ("c1_ban", "c2_heat_index", "c3_twl", "c4_wbgt")}}
            for p, a in pols.items():
                scores.append({"worker_id": s["worker_id"], "date": s["date"], "scenario": sc, "policy": p,
                               **evaluate.score_shift(a, s["onset"], HORIZON)})
    return pd.DataFrame(scores)


def prereg_committed():
    if not PREREG.exists():
        return False
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(PREREG)], capture_output=True).returncode == 0
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(PREREG)]).returncode == 0
    return tracked and clean


def stage_final(out, smoke=False):
    lock = out / "FINAL_RUN_DONE.json"
    if not smoke:
        if not prereg_committed():
            sys.exit(f"STOP: {PREREG} must be committed (and unchanged) before the locked run.")
        if lock.exists():
            sys.exit(f"STOP: the locked run already happened ({lock}). It is run once only.")
    sel = json.loads((out / "select.json").read_text())
    name = sel["primary_model"]
    wk, ix, groups, _ = load_set("train", out)
    shifts = rows(wk, ix, groups)
    # Threshold: the out-of-fold choice from stage 2 (training workers only); final model fitted on all of them
    thr = float(pd.read_csv(out / "select_summary.csv").set_index("model").loc[name, "threshold"])
    model = fit(name, shifts)
    log(f"primary model {name}, threshold {thr}; scoring the locked 2024 test set (once)")
    wk_t, ix_t, groups_t, twl_t = load_set("test", out)
    scores = score_set(wk_t, ix_t, groups_t, twl_t, model, thr)
    scores.to_csv(out / "final_scores.csv", index=False)
    res = judge(scores)
    (out / "final_verdict.json").write_text(json.dumps(res, indent=2, default=str))
    summ = scores.groupby(["scenario", "policy"]).apply(lambda d: pd.Series(evaluate.summarise(d)),
                                                         include_groups=False).drop(columns=["lead_iqr"])
    summ.to_csv(out / "final_summary.csv")
    if not smoke:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        lock.write_text(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "commit": commit,
                                    "model": name, "threshold": thr}, indent=2))
    log("RESULT:\n" + summ.loc["clean"][["events", "missed", "median_lead", "false_per_shift",
                                          "warning_min_per_shift"]].to_string())
    log(f"VERDICT: {res['verdict']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["data", "select", "final", "smoke"])
    ap.add_argument("--train-weather", default="data/weather_hourly.csv")
    ap.add_argument("--test-weather", default="data/weather_hourly_2024.csv")
    args = ap.parse_args()
    if args.stage == "smoke":           # code check only: synthetic weather, tiny sizes
        out = Path("outputs/v5_SMOKE_SYNTHETIC")
        wpath = weather.make_test_weather("data")
        args.train_weather = args.test_weather = wpath
        stage_data(args, SIZES["smoke"], out)
        stage_select(out)
        stage_final(out, smoke=True)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    {"data": lambda: stage_data(args, SIZES["full"], OUT), "select": lambda: stage_select(OUT),
     "final": lambda: stage_final(OUT)}[args.stage]()


if __name__ == "__main__":
    main()
