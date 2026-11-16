"""Week 9: simulate the confirmation set (brand-new workers on unused summer dates).

    python make_confirmation_set.py --weather data/weather_hourly.csv --run outputs/full

Run it ONCE after run_pilot.py. run_week9.py --confirm scores it once, at the very end.
Output: <run>/confirm/ (workers.csv, split.csv, shift_index.csv, trajectories.csv.gz).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from heatguard import weather, week9
from run_pilot import log, simulate_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weather", required=True)
    ap.add_argument("--run", required=True, help="the main run folder (to know which dates were used)")
    args = ap.parse_args()
    run = Path(args.run)
    out = run / "confirm"
    out.mkdir(exist_ok=True)

    hourly = weather.load_hourly(args.weather)
    used = sorted(pd.read_csv(run / "split.csv")["date"].unique())
    dates = week9.confirmation_dates(hourly, used)
    wk = week9.confirmation_workers()
    split = pd.DataFrame([(w, d, "confirm") for w in wk["worker_id"] for d in dates],
                         columns=["worker_id", "date", "partition"])
    wk.to_csv(out / "workers.csv", index=False)
    split.to_csv(out / "split.csv", index=False)
    log(f"confirmation set: {len(wk)} new workers x {len(dates)} unused dates = {len(split)} shifts")
    log("dates: " + ", ".join(dates))
    _, index = simulate_all(hourly, split, wk, out)
    log(f"danger events in the confirmation set: {int(index['onset'].notna().sum())} of {len(index)} shifts")


if __name__ == "__main__":
    main()
