"""Run the whole HeatGuard pipeline end to end.

    python run_pilot.py --fetch                 # download real weather, then run the pilot
    python run_pilot.py --weather data/weather_hourly.csv
    python run_pilot.py --test-weather          # code test only: SYNTHETIC weather, never report these numbers

Outputs go to outputs/<run name>/ and are read by dashboard.py.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
import zlib
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from heatguard import config as C
from heatguard import alerts, baseline, evaluate, features, model, simulator, wearables, weather, workers

TEST_SCENARIOS = ["clean", "S5_dropout", "S6_stuck"]
HORIZON = C.HORIZONS_MIN[0]   # 30-minute primary horizon


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def simulate_all(hourly, split, wk, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    traj_path, idx_path = out / "trajectories.csv.gz", out / "shift_index.csv"
    if traj_path.exists() and idx_path.exists():
        old = pd.read_csv(idx_path)
        same = old[["worker_id", "date", "partition"]].reset_index(drop=True).equals(split.reset_index(drop=True))
        if same:
            log("re-using simulated shifts from a previous run")
            return pd.read_csv(traj_path, parse_dates=["timestamp"]), old
        log("split has changed since the last run: simulating again")
    weather_cache, trajs, index = {}, [], []
    for i, row in enumerate(split.itertuples(index=False)):
        if row.date not in weather_cache:
            weather_cache[row.date] = weather.shift_minutes(hourly, row.date)
        worker = wk.set_index("worker_id").loc[row.worker_id].copy()
        worker["worker_id"] = row.worker_id
        traj, onset = simulator.simulate_shift(worker, weather_cache[row.date])
        traj["date"], traj["partition"] = row.date, row.partition
        trajs.append(traj)
        index.append({"worker_id": row.worker_id, "date": row.date, "partition": row.partition,
                      "onset": onset, "valid": bool(traj["valid"].all()),
                      "acclimatised": bool(worker["acclimatised"]), "work_rate_wm2": int(worker["work_rate_wm2"])})
        if (i + 1) % 10 == 0:
            log(f"simulated {i + 1}/{len(split)} shifts")
    trajs, index = pd.concat(trajs, ignore_index=True), pd.DataFrame(index)
    trajs.to_csv(traj_path, index=False)
    index.to_csv(idx_path, index=False)
    return trajs, index


def shift_inputs(traj, worker, scenario, seed):
    clean = wearables.make_messages(traj, worker, seed)
    msgs = wearables.inject_fault(clean, scenario, seed, worker=worker, traj=traj)
    feats = features.build_features(msgs, traj[["wbgt", "tdb", "rh"]], worker)
    rule = baseline.wbgt_rule(traj["wbgt"].reset_index(drop=True), traj["met_wm2"].reset_index(drop=True), worker)
    return msgs, feats, rule


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--fetch", action="store_true", help="download real Open-Meteo weather first")
    g.add_argument("--weather", help="path to an existing weather_hourly.csv")
    g.add_argument("--test-weather", action="store_true", help="SYNTHETIC weather for code testing only")
    ap.add_argument("--design", choices=["pilot", "full"], default="pilot")
    ap.add_argument("--name", default=None, help="output folder name")
    args = ap.parse_args()

    if args.fetch:
        wpath = weather.fetch_weather("data")
    elif args.test_weather:
        wpath = weather.make_test_weather("data")
    else:
        wpath = Path(args.weather)
    hourly = weather.load_hourly(wpath)
    synthetic = (hourly["source"] == "SYNTHETIC_TEST").any()
    design = C.PILOT if args.design == "pilot" else C.FULL
    name = args.name or f"{args.design}{'_TEST_SYNTHETIC' if synthetic else ''}"
    out = Path("outputs") / name
    out.mkdir(parents=True, exist_ok=True)
    log(f"weather: {wpath} ({'SYNTHETIC TEST DATA' if synthetic else 'real'}) -> outputs/{name}")

    # Part 2: workers, dates and the leakage-safe split
    wk = workers.make_workers(design["n_workers"])
    dates = weather.sample_dates(hourly, design["n_dates"])
    split = workers.make_split(wk["worker_id"].tolist(), dates, design)
    wk.to_csv(out / "workers.csv", index=False)
    split.to_csv(out / "split.csv", index=False)
    log(f"{len(wk)} workers x {len(dates)} dates -> {len(split)} same-partition shifts")

    # Part 3: simulate every shift (the hidden reference)
    trajs, index = simulate_all(hourly, split, wk, out)
    index["onset"] = index["onset"].astype("Int64")
    counts = index.groupby(["partition", "acclimatised"])["onset"].apply(lambda s: f"{s.notna().sum()}/{len(s)}")
    log("danger events per partition (events/shifts):\n" + counts.to_string())

    wk_idx = wk.set_index("worker_id")
    groups = {k: g.reset_index(drop=True) for k, g in trajs.groupby(["worker_id", "date"])}

    def worker_of(wid):
        w = wk_idx.loc[wid].copy()
        w["worker_id"] = wid
        return w

    # Parts 4-5: features and labels, train on TRAIN only
    def rows_for(part, scenario="clean"):
        X, Y, meta = [], [], []
        for r in index[(index["partition"] == part) & index["valid"]].itertuples(index=False):
            traj, worker = groups[(r.worker_id, r.date)], worker_of(r.worker_id)
            seed = C.SEED + zlib.crc32(f"{r.worker_id}|{r.date}".encode()) % 10_000  # stable across runs
            msgs, feats, rule = shift_inputs(traj, worker, scenario, seed)
            onset = None if pd.isna(r.onset) else int(r.onset)
            y = features.make_labels(len(feats), onset, HORIZON)
            X.append(feats)
            Y.append(y)
            meta.append((r.worker_id, r.date, onset, msgs, feats, rule, traj))
        return X, Y, meta

    Xtr, Ytr, _ = rows_for("train")
    X = pd.concat(Xtr, ignore_index=True)
    y = pd.concat(Ytr, ignore_index=True)
    keep = y.notna()
    if y[keep].nunique() < 2:
        log("STOP: training data has no danger events, so no model can be trained. Record this in the iteration log.")
        return
    clf = model.train(X.loc[keep, features.ALL_FEATURES], y[keep])
    log(f"trained logistic regression on {keep.sum()} minutes ({int(y[keep].sum())} positive)")

    # Threshold on VALIDATION
    _, _, val_meta = rows_for("val")
    val_probs = [(model.predict_proba(clf, f[features.ALL_FEATURES]), onset) for (_, _, onset, _, f, _, _) in val_meta]

    def val_score(t):
        sc = pd.DataFrame([evaluate.score_shift((p >= t).astype(int), o, HORIZON) for p, o in val_probs])
        return evaluate.summarise(sc)

    thr, thr_table = model.choose_threshold(val_score)
    thr_table.to_csv(out / "threshold_table.csv", index=False)
    log(f"threshold chosen on validation: {thr} (constraint met: {bool(thr_table['constraint_met'].iloc[0])})")

    # TEST: each scenario, three policies
    scores, logs = [], []
    for scenario in TEST_SCENARIOS:
        _, _, meta = rows_for("test", scenario)
        for wid, date, onset, msgs, feats, rule, traj in meta:
            prob = model.predict_proba(clf, feats[features.ALL_FEATURES])
            pol = alerts.run_policies(prob, thr, rule["wbgt_alert"], feats)
            for p in ("wbgt_rule", "ml", "ml_fallback"):
                scores.append({"worker_id": wid, "date": date, "scenario": scenario, "policy": p,
                               **evaluate.score_shift(pol[p].to_numpy(), onset, HORIZON)})
            logs.append(pd.DataFrame({
                "worker_id": wid, "date": date, "scenario": scenario, "minute": traj["minute"],
                "timestamp": traj["timestamp"], "phase": traj["phase"], "wbgt": traj["wbgt"],
                "wbgt_limit": rule["wbgt_limit"], "hr": msgs["hr"], "skin_temp": msgs["skin_temp"],
                "t_re_reference": traj["t_re"], "danger_limit": traj["danger_limit"],
                "onset": onset if onset is not None else -1, **pol}))
    scores = pd.DataFrame(scores)
    scores.to_csv(out / "scores.csv", index=False)
    pd.concat(logs, ignore_index=True).to_csv(out / "policy_logs.csv.gz", index=False)
    wearables.to_jsonl(meta[0][3], out / "sample_messages.jsonl")

    summary = {}
    for (scenario, policy), g in scores.groupby(["scenario", "policy"]):
        summary.setdefault(scenario, {})[policy] = evaluate.summarise(g)
    for scenario in TEST_SCENARIOS:
        s = scores[scores["scenario"] == scenario]
        summary[scenario]["paired_median_lead_ml_minus_wbgt"] = evaluate.paired_lead_difference(
            s[s["policy"] == "ml"], s[s["policy"] == "wbgt_rule"])
    run_info = {
        "weather_file": str(wpath), "synthetic_weather": bool(synthetic), "design": args.design,
        "threshold": thr, "horizon_min": HORIZON, "dates": dates,
        "events": index.groupby("partition")["onset"].apply(lambda s: int(s.notna().sum())).to_dict(),
        "invalid_shifts": int((~index["valid"]).sum()),
        "python": platform.python_version(),
        "versions": {p: version(p) for p in ["pythermalcomfort", "thermofeel", "scikit-learn", "pandas", "numpy"]},
    }
    (out / "summary.json").write_text(json.dumps({"run_info": run_info, "results": summary}, indent=2, default=str))
    table = scores.groupby(["scenario", "policy"]).apply(lambda g: pd.Series(evaluate.summarise(g)), include_groups=False)
    log("TEST results" + (" (SYNTHETIC WEATHER: pipeline check only)" if synthetic else "") + ":\n"
        + table[["events", "missed", "median_lead", "false_per_shift", "warning_min_per_shift"]].to_string())


if __name__ == "__main__":
    main()
