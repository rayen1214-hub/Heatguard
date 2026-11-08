"""Week 8 experiments, run AFTER run_pilot.py (it reuses the simulated shifts).

    python run_week8.py --run outputs/full            # real weather results
    python run_week8.py --run outputs/full_TEST_SYNTHETIC --quick   # code check only

What it adds to Week 7 (nothing in the Week 7 files changes):
  1. Three models: logistic regression, random forest, gradient boosting.
  2. A second fold: validation and test swap roles (threshold on one, score on the other),
     so every unseen danger event is scored once. Training data never changes.
  3. All sensor scenarios from Table III: clean, S5 dropout / 10% / 30% missing, S6 stuck, S7 noise.
  4. Lead-time difference (ML minus WBGT, and each model minus logistic regression) per
     danger event, with a bootstrap 95% interval.
  5. Sensitivity: weaker heart-rate link (HR_THERMAL_GAIN 25 -> 10 -> 0 bpm per deg C).
  6. E5: which factor groups the models rely on (grouped permutation importance).

Outputs go to <run>/week8/.
"""
from __future__ import annotations

import argparse
import json
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from heatguard import alerts, baseline, evaluate, features, model, wearables, week8
from heatguard import config as C

SCENARIOS = ["clean", "S5_dropout", "S5_missing10", "S5_missing30", "S6_stuck", "S7_noise"]
FOLDS = {"A": ("val", "test"), "B": ("test", "val")}   # (tune threshold on, score on)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="output folder of a finished run_pilot.py run")
    ap.add_argument("--gains", default="25,10,0", help="heart-rate link strengths to test")
    ap.add_argument("--horizon", type=int, default=C.HORIZONS_MIN[0])
    ap.add_argument("--quick", action="store_true", help="clean + S5_dropout only, gain 25 only")
    args = ap.parse_args()

    run = Path(args.run)
    out = run / "week8"
    out.mkdir(exist_ok=True)
    wk = pd.read_csv(run / "workers.csv").set_index("worker_id")
    index = pd.read_csv(run / "shift_index.csv")
    index["onset"] = index["onset"].astype("Int64")
    trajs = pd.read_csv(run / "trajectories.csv.gz", parse_dates=["timestamp"])
    groups = {k: g.reset_index(drop=True) for k, g in trajs.groupby(["worker_id", "date"])}
    synthetic = "SYNTHETIC" in run.name
    gains = [25.0] if args.quick else [float(g) for g in args.gains.split(",")]
    scenarios = ["clean", "S5_dropout"] if args.quick else SCENARIOS
    H = args.horizon
    log(f"run {run} ({'SYNTHETIC: code check only' if synthetic else 'real weather'}), horizon {H} min")

    def worker_of(wid):
        w = wk.loc[wid].copy()
        w["worker_id"] = wid
        return w

    def shifts(part, scenario, gain):
        """Features, labels and the WBGT rule for every valid shift in one partition."""
        rows = []
        for r in index[(index["partition"] == part) & index["valid"]].itertuples(index=False):
            traj, worker = groups[(r.worker_id, r.date)], worker_of(r.worker_id)
            seed = C.SEED + zlib.crc32(f"{r.worker_id}|{r.date}".encode()) % 10_000   # same seeds as Week 7
            clean = wearables.make_messages(traj, worker, seed, thermal_gain=gain)
            if scenario == "S7_noise":
                msgs = wearables.make_messages(traj, worker, seed, hr_noise=8.0, skin_noise=0.5, thermal_gain=gain)
            else:
                msgs = wearables.inject_fault(clean, scenario, seed, worker=worker, traj=traj)
            feats = features.build_features(msgs, traj[["wbgt", "tdb", "rh"]], worker)
            rule = baseline.wbgt_rule(traj["wbgt"], traj["met_wm2"], worker)
            onset = None if pd.isna(r.onset) else int(r.onset)
            rows.append(dict(worker_id=r.worker_id, date=r.date, onset=onset, feats=feats, rule=rule,
                             y=features.make_labels(len(feats), onset, H)))
        return rows

    all_scores, thresholds, importance = [], [], []
    for gain in gains:
        log(f"--- heart-rate link {gain:g} bpm per deg C ---")
        train = shifts("train", "clean", gain)
        X = pd.concat([s["feats"] for s in train], ignore_index=True)
        y = pd.concat([s["y"] for s in train], ignore_index=True)
        keep = y.notna()
        if y[keep].nunique() < 2:
            log("STOP: no danger events in training data")
            return
        clean_eval = {p: shifts(p, "clean", gain) for p in ("val", "test")}
        fitted = {}
        for name in week8.MODELS:
            t0 = time.time()
            fitted[name] = week8.make_model(name).fit(X.loc[keep, features.ALL_FEATURES], y[keep])
            log(f"trained {name} on {int(keep.sum())} minutes ({int(y[keep].sum())} positive) in {time.time() - t0:.0f} s")

        for fold, (tune, score_on) in FOLDS.items():
            # Thresholds: tuned on clean data of the tuning partition only
            thr = {}
            for name, clf in fitted.items():
                probs = [(model.predict_proba(clf, s["feats"][features.ALL_FEATURES]), s["onset"])
                         for s in clean_eval[tune]]

                def score_fn(t, probs=probs):
                    return evaluate.summarise(pd.DataFrame(
                        [evaluate.score_shift((p >= t).astype(int), o, H) for p, o in probs]))
                thr[name], table = model.choose_threshold(score_fn)
                thresholds.append({"gain": gain, "fold": fold, "model": name, "tuned_on": tune,
                                   "threshold": thr[name], "constraint_met": bool(table["constraint_met"].iloc[0])})
            for scenario in scenarios:
                ev = clean_eval[score_on] if scenario == "clean" else shifts(score_on, scenario, gain)
                for s in ev:
                    base = dict(gain=gain, fold=fold, scenario=scenario, worker_id=s["worker_id"], date=s["date"])
                    all_scores.append({**base, "policy": "wbgt_rule",
                                       **evaluate.score_shift(s["rule"]["wbgt_alert"].clip(lower=0).to_numpy(),
                                                              s["onset"], H)})
                    for name, clf in fitted.items():
                        prob = model.predict_proba(clf, s["feats"][features.ALL_FEATURES])
                        pol = alerts.run_policies(prob, thr[name], s["rule"]["wbgt_alert"], s["feats"])
                        all_scores.append({**base, "policy": f"ml_{name}",
                                           **evaluate.score_shift(pol["ml"].to_numpy(), s["onset"], H)})
                        all_scores.append({**base, "policy": f"fallback_{name}",
                                           **evaluate.score_shift(pol["ml_fallback"].to_numpy(), s["onset"], H)})
            log(f"fold {fold}: thresholds tuned on {tune}, scored on {score_on}: "
                + ", ".join(f"{k} {v}" for k, v in thr.items()))

        # E5 on the full design only (main heart-rate link), pooled unseen data, clean sensors
        if gain == gains[0]:
            Xe = pd.concat([s["feats"] for p in ("val", "test") for s in clean_eval[p]], ignore_index=True)
            ye = pd.concat([s["y"] for p in ("val", "test") for s in clean_eval[p]], ignore_index=True)
            ok = ye.notna()
            for name, clf in fitted.items():
                imp = week8.grouped_importance(clf, Xe[ok].reset_index(drop=True), ye[ok].reset_index(drop=True))
                imp.insert(0, "model", name)
                importance.append(imp)

    scores = pd.DataFrame(all_scores)
    scores.to_csv(out / "scores_week8.csv", index=False)
    pd.DataFrame(thresholds).to_csv(out / "thresholds_week8.csv", index=False)
    if importance:
        pd.concat(importance).to_csv(out / "importance_E5.csv", index=False)

    # Summary per heart-rate link x scenario x policy, both folds pooled (every unseen event once)
    summ = (scores.groupby(["gain", "scenario", "policy"])
            .apply(lambda g: pd.Series(evaluate.summarise(g)), include_groups=False).reset_index())
    summ = summ.drop(columns=["lead_iqr"])
    summ.to_csv(out / "summary_week8.csv", index=False)

    # Paired lead-time differences with bootstrap 95% intervals
    diffs = []
    for (gain, scenario), g in scores.groupby(["gain", "scenario"]):
        for name in week8.MODELS:
            for a, b in ((f"ml_{name}", "wbgt_rule"), (f"fallback_{name}", "wbgt_rule"), (f"ml_{name}", "ml_logreg")):
                if a == b:
                    continue
                d = week8.paired_differences(g, a, b)
                lo, hi = week8.bootstrap_ci(d)
                diffs.append({"gain": gain, "scenario": scenario, "a": a, "b": b, "events": len(d),
                              "median_diff_min": float(d.median()) if len(d) else float("nan"),
                              "ci95_low": lo, "ci95_high": hi})
    diffs = pd.DataFrame(diffs)
    diffs.to_csv(out / "lead_differences.csv", index=False)

    info = {"run": str(run), "synthetic_weather": synthetic, "horizon_min": H, "gains": gains,
            "scenarios": scenarios, "folds": FOLDS, "models": list(week8.MODELS),
            "events_scored": int(scores[(scores["policy"] == "wbgt_rule") & scores["event"]]
                                 .drop_duplicates(["gain", "scenario", "fold", "worker_id", "date"])
                                 .query("scenario == 'clean'").shape[0] / max(len(gains), 1))}
    (out / "week8_info.json").write_text(json.dumps(info, indent=2))

    show = summ[(summ["scenario"] == "clean")][["gain", "policy", "events", "missed", "median_lead",
                                                  "false_per_shift", "warning_min_per_shift"]]
    pd.set_option("display.width", 160)
    log("RESULTS, clean sensors, both folds pooled" + (" (SYNTHETIC: code check only)" if synthetic else "")
        + ":\n" + show.round(2).to_string(index=False))
    dshow = diffs[(diffs["scenario"] == "clean") & (diffs["b"] == "wbgt_rule") & diffs["a"].str.startswith("ml_")]
    log("Lead time, ML minus WBGT (minutes, median and 95% interval):\n"
        + dshow[["gain", "a", "events", "median_diff_min", "ci95_low", "ci95_high"]].round(1).to_string(index=False))
    if importance:
        log("E5, drop in average precision when a factor group is shuffled:\n"
            + pd.concat(importance)[["model", "group", "ap_drop_mean"]].to_string(index=False))
    log(f"all tables written to {out}/")


if __name__ == "__main__":
    main()
