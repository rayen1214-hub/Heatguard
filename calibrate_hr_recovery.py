"""Exploratory calibration using PROSPIE (doi:10.17028/rd.lboro.26076577.v1).

Run from the repository root with the v0.5 requirements plus openpyxl.
Results go to outputs/prospie_recovery. The v0.5 locked runner is independent.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import zlib

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from heatguard import baseline, config, evaluate, features, v5, wearables, weather
from run_v5 import FEATS, HORIZON, add_extra, fit, hg_alert

WINDOW = 10
ORIGINAL_FRACTION = 0.5
THRESHOLD = 0.32
HOLD = 30


def recovery_windows(workbook):
    # Two header rows. PROSPIE defines work/rest as 1/2 and initial rest as activity 4.
    lab = pd.read_excel(workbook, sheet_name="Data", header=None, skiprows=2,
                        usecols=[0, 1, 2, 3, 20, 29, 45])
    lab.columns = ["condition", "time", "activity", "participant", "work_rest", "rectal", "hr"]
    lab["minute"] = lab["time"].map(lambda t: t.hour * 60 + t.minute + t.second / 60)
    lab["hr"] = lab["hr"].where(lab["hr"].between(*config.HR_VALID_RANGE))
    lab["rectal"] = lab["rectal"].where(lab["rectal"].between(34, 43))

    windows = []
    for (participant, condition), trial in lab.groupby(["participant", "condition"]):
        trial = trial.sort_values("minute").reset_index(drop=True)
        baseline = trial[(trial["minute"] < 10) & (trial["activity"] == 4)]
        if baseline["hr"].count() < 5 or baseline["rectal"].count() < 5:
            continue
        rest_hr = baseline["hr"].median()
        rest_core = baseline["rectal"].median()
        starts = trial.index[(trial["work_rest"] == 2) & (trial["work_rest"].shift() == 1)]
        for start in starts:
            segment = trial.iloc[start - 5:start + WINDOW]
            if len(segment) != 5 + WINDOW or not segment["minute"].diff().iloc[1:].eq(1).all():
                continue
            if not segment["work_rest"].iloc[:5].eq(1).all() or not segment["work_rest"].iloc[5:].eq(2).all():
                continue
            observed = segment["hr"].iloc[4:].to_numpy()
            core = segment["rectal"].iloc[5:].to_numpy()
            if not np.isfinite(observed).all() or not np.isfinite(core).all() or observed[0] <= rest_hr:
                continue
            target = rest_hr + config.HR_THERMAL_GAIN * np.maximum(core - rest_core, 0)
            windows.append((int(participant), int(condition), float(trial.loc[start, "minute"]), observed, target))
    return windows


def recovery_prediction(observed, target, fraction):
    current = observed[0]
    predicted = []
    for bpm in target:
        current += fraction * (bpm - current)
        predicted.append(current)
    return np.asarray(predicted)


def recovery_errors(windows, fraction):
    rows = []
    for participant, condition, start, observed, target in windows:
        predicted = recovery_prediction(observed, target, fraction)
        rows.append({"participant": participant, "condition": condition, "rest_start_min": start,
                     "mae_bpm": float(np.abs(predicted - observed[1:]).mean()),
                     "observed_drop_bpm": float(observed[0] - observed[-1]),
                     "predicted_drop_bpm": float(observed[0] - predicted[-1])})
    return pd.DataFrame(rows)


def mean_participant_error(errors):
    return errors.groupby("participant")["mae_bpm"].mean().mean()


def calibrate(workbook, out):
    windows = recovery_windows(workbook)
    ids = np.random.default_rng(config.SEED).permutation(sorted({s[0] for s in windows}))
    if len(ids) < 5:
        raise ValueError("Need at least five participants with usable recovery windows.")
    holdout = set(ids[:max(1, round(len(ids) * 0.25))])
    training = [s for s in windows if s[0] not in holdout]
    testing = [s for s in windows if s[0] in holdout]
    result = minimize_scalar(lambda a: mean_participant_error(recovery_errors(training, a)),
                             bounds=(0.01, 1.0), method="bounded")
    if not result.success:
        raise RuntimeError(result.message)
    fraction = float(result.x)
    summary = {"fraction": fraction, "fit_participants": sorted(set(int(p) for p in ids) - holdout),
               "held_out_participants": sorted(int(p) for p in holdout),
               "fit_windows": len(training), "test_windows": len(testing)}
    for label, rate in (("original", ORIGINAL_FRACTION), ("calibrated", fraction)):
        errors = recovery_errors(testing, rate)
        errors.to_csv(out / f"prospie_holdout_{label}.csv", index=False)
        summary[f"{label}_holdout_mae_bpm"] = float(mean_participant_error(errors))
    (out / "calibration.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    return fraction


def simulate_worker(job):
    weather_path, worker, dates = job
    hourly = weather.load_hourly(weather_path)
    rows = []
    for date in dates:
        traj, onset = v5.simulate_day(worker, v5.day_minutes(hourly, date), date)
        if traj["valid"].all():
            rows.append((worker, date, traj, onset))
    return rows


def simulated_shifts(pool, weather_path, count, seed, prefix):
    hourly = weather.load_hourly(weather_path)
    dates = sorted(hourly["timestamp"].dt.strftime("%Y-%m-%d").unique())
    rng = np.random.default_rng(seed + 1)
    workers = v5.make_workers_v5(count, seed, prefix=prefix)
    jobs = [(weather_path, worker, sorted(rng.choice(dates, size=4, replace=False).tolist()))
            for _, worker in workers.iterrows()]
    return [shift for rows in pool.map(simulate_worker, jobs) for shift in rows]


def inputs(shift, fraction):
    worker, date, traj, onset = shift
    seed = config.SEED + zlib.crc32(f"{worker['worker_id']}|{date}".encode()) % 10_000
    messages = wearables.make_messages(traj, worker, seed, recovery_fraction=fraction)
    built = features.build_features(messages, traj[["wbgt", "tdb", "rh"]], worker)
    return {"feats": add_extra(built, traj, worker), "traj": traj,
            "rule": baseline.wbgt_rule(traj["wbgt"], traj["met_wm2"], worker), "onset": onset,
            "y": features.make_labels(len(traj), onset, HORIZON)}


def dubai_followup(fraction, out):
    with ProcessPoolExecutor(max_workers=6) as pool:
        training = simulated_shifts(pool, "data/weather_hourly.csv", 48, config.SEED + 1000, "R")
        print(f"Valid 2025 training shifts: {len(training)}", flush=True)
        testing = simulated_shifts(pool, "data/weather_hourly_2024.csv", 36, config.SEED + 1100, "Q")
    print(f"Valid Dubai shifts: {len(training)} training and {len(testing)} test", flush=True)
    # Freeze one model trained with the original generator, and the published threshold/hold.
    model = fit("logreg", [inputs(s, ORIGINAL_FRACTION) for s in training])
    scores = []
    for shift in testing:
        worker, date, _, onset = shift
        for name, rate in (("original", ORIGINAL_FRACTION), ("calibrated", fraction)):
            prepared = inputs(shift, rate)
            probabilities = model.predict_proba(prepared["feats"][FEATS])[:, 1]
            warning = hg_alert(probabilities, THRESHOLD, prepared, HOLD)
            scores.append({"variant": name, "worker_id": worker["worker_id"], "date": date,
                           **evaluate.score_shift(warning, onset, HORIZON)})
    frame = pd.DataFrame(scores)
    frame.to_csv(out / "dubai_scores.csv", index=False)
    summary = {name: evaluate.summarise(group) for name, group in frame.groupby("variant")}
    (out / "dubai_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--lab-only", action="store_true")
    args = parser.parse_args()
    out = Path("outputs/prospie_recovery")
    out.mkdir(parents=True, exist_ok=True)
    fraction = calibrate(args.workbook, out)
    if not args.lab_only:
        dubai_followup(fraction, out)


if __name__ == "__main__":
    main()
