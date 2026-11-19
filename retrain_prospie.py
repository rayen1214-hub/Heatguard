"""Exploratory retraining with PROSPIE recovery and independent Australian comparison."""
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import zlib

import joblib
import numpy as np
import pandas as pd

from calibrate_hr_recovery import calibrate, inputs, ORIGINAL_FRACTION
from heatguard import config as C, evaluate, v5, wearables, weather
from run_v5 import fit, FEATS, hg_alert, choose_threshold, HORIZON


OUT = Path("outputs/prospie_retrained")
RAW = Path("data/external")


def simulate(job):
    worker, dates, path = job
    hourly = weather.load_hourly(path)
    rows = []
    for date in dates:
        trajectory, onset = v5.simulate_day(worker, v5.day_minutes(hourly, date), date)
        rows.append((worker, date, trajectory, onset))
    return rows


def cohort(pool, name, count, seed, year):
    path = f"data/weather_hourly{'_2024' if year == 2024 else ''}.csv"
    available = sorted(weather.load_hourly(path).timestamp.dt.strftime("%Y-%m-%d").unique())
    profiles = v5.make_workers_v5(count, seed, prefix=name)
    rng = np.random.default_rng(seed + 1)
    jobs = [(worker, sorted(rng.choice(available, 8, replace=False).tolist()), path)
            for _, worker in profiles.iterrows()]
    shifts = [shift for rows in pool.map(simulate, jobs) for shift in rows]
    valid = [shift for shift in shifts if shift[2].valid.all()]
    print(name, len(valid), "valid shifts of", len(shifts), flush=True)
    return valid, len(shifts) - len(valid)


def field_comparison(testing, fraction):
    field = pd.read_excel(RAW / "western-australia-mine-workers/pone.0292436.s003.xlsx")
    field = field.query("season == 'summer' and occupation == 'maintenance'")
    trace = pd.read_excel(RAW / "western-australia-mine-workers/pone.0292436.s008.xlsx")
    rows = []
    for shift in testing:
        worker, date, trajectory, _ = shift
        seed = C.SEED + zlib.crc32(f"{worker['worker_id']}|{date}".encode()) % 10_000
        for variant, rate in (("original", ORIGINAL_FRACTION), ("calibrated", fraction)):
            readings = wearables.make_messages(trajectory, worker, seed, recovery_fraction=rate)
            rows.append(dict(variant=variant, worker_id=worker["worker_id"], date=date,
                             first6h_mean_hr=float(readings.hr.iloc[:360].mean()),
                             midday_hr=float(readings.hr.iloc[359]),
                             midday_rectal=float(trajectory.t_re.iloc[359]),
                             first6h_mean_wbgt=float(trajectory.wbgt.iloc[:360].mean())))
    pd.DataFrame(rows).to_csv(OUT / "australia_simulated_comparison.csv", index=False)
    field_mid = field[field["shift timepoint"] == 2]
    summary = {"australia": {
        "maintenance_workers": int(field.id.nunique()),
        "midday_temperature_observations": int(field_mid.tc.count()),
        "workers_with_midday_temperature": int(field_mid.dropna(subset=["tc"]).id.nunique()),
        "midday_core_median_C": float(field_mid.tc.median()),
        "midday_hr_median_bpm": float(field_mid.hr.median()),
        "first6h_group_trace_mean_bpm": float(trace.loc[trace.Min.between(0, 359), "Maintenance worker"].mean())}}
    for variant, group in pd.DataFrame(rows).groupby("variant"):
        summary[variant] = {key: float(group[key].median()) for key in
                            ["midday_hr", "midday_rectal", "first6h_mean_wbgt"]}
        summary[variant]["first6h_population_mean_hr"] = float(group.first6h_mean_hr.mean())
    return summary


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fraction = calibrate(RAW / "prospie-lab/PROSPIE-original.xlsx", OUT)
    with ProcessPoolExecutor(max_workers=6) as pool:
        train, train_bad = cohort(pool, "TR", 96, 2305, 2025)
        validation, val_bad = cohort(pool, "VA", 36, 2405, 2025)
        test, test_bad = cohort(pool, "TE", 60, 2505, 2024)
    records, settings = [], {}
    for variant, rate in (("original", ORIGINAL_FRACTION), ("calibrated", fraction)):
        training = [inputs(shift, rate) for shift in train]
        clf = fit("logreg", training)
        del training
        val = [inputs(shift, rate) for shift in validation]
        probabilities = [clf.predict_proba(row["feats"][FEATS])[:, 1] for row in val]
        base_scores = pd.DataFrame([evaluate.score_shift(
            (row["rule"]["wbgt_alert"].clip(lower=0).to_numpy() * (row["traj"]["phase"] != "break").to_numpy()),
            row["onset"], HORIZON) for row in val])
        # Same v0.5 tuning principle, evaluated on separate validation workers.
        max_miss = evaluate.summarise(base_scores)["miss_rate"] + 0.01
        (threshold, hold), met, table = choose_threshold(probabilities, val, max_miss)
        table.to_csv(OUT / f"{variant}_validation_thresholds.csv", index=False)
        settings[variant] = dict(recovery_fraction=rate, threshold=threshold, hold=hold,
                                 validation_constraint_met=met, validation_max_miss=max_miss)
        joblib.dump(dict(model=clf, features=FEATS, **settings[variant]), OUT / f"{variant}_model.joblib")
        for shift in test:
            worker, date, trajectory, onset = shift
            row = inputs(shift, rate)
            probability = clf.predict_proba(row["feats"][FEATS])[:, 1]
            warning = hg_alert(probability, threshold, row, hold)
            records.append(dict(variant=variant, worker_id=worker["worker_id"], date=date,
                                **evaluate.score_shift(warning, onset, HORIZON)))
            if variant == "original":
                rule = row["rule"]["wbgt_alert"].clip(lower=0).to_numpy() * (trajectory["phase"] != "break").to_numpy()
                records.append(dict(variant="wbgt", worker_id=worker["worker_id"], date=date,
                                    **evaluate.score_shift(rule, onset, HORIZON)))
        print("Finished", variant, settings[variant], flush=True)
    scores = pd.DataFrame(records)
    scores.to_csv(OUT / "test_scores.csv", index=False)
    summary = {name: evaluate.summarise(group) for name, group in scores.groupby("variant")}
    manifest = dict(base_commit="559b0f2", train_shifts=len(train), validation_shifts=len(validation),
                    test_shifts=len(test), invalid_shifts=[train_bad, val_bad, test_bad],
                    seeds=[2305,2405,2505], settings=settings, results=summary,
                    australian_comparison=field_comparison(test, fraction))
    manifest["source_sha256"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
        RAW / "prospie-lab/PROSPIE-original.xlsx",
        RAW / "western-australia-mine-workers/pone.0292436.s003.xlsx",
        RAW / "western-australia-mine-workers/pone.0292436.s008.xlsx",
        Path("data/weather_hourly.csv"), Path("data/weather_hourly_2024.csv")]}
    (OUT / "results.json").write_text(json.dumps(manifest, indent=2, default=lambda x: x.item()) + "\n")
    print(json.dumps(manifest, indent=2, default=lambda x: x.item()), flush=True)


if __name__ == "__main__":
    main()
