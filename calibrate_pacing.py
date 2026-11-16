"""Tune self-pacing so simulated worker-days match real field studies (F3).

    python calibrate_pacing.py

Uses its OWN calibration workers (seed SEED+900) on 2025 weather only. Never touches the 2024
test set. Targets: share of worker-days passing 38.0 / 38.3 / 38.5 C = 44 / 16 / 6 %
(Guatemala field workers, Adgate et al. 2025). Writes outputs/v5/pacing_calibration.csv.
"""
from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
from itertools import product

if __name__ != "__main__":
    for _v in ("OMP_NUM_THREADS", "NUMBA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[_v] = "1"

import numpy as np
import pandas as pd

from heatguard import config as C
from heatguard import v5, weather

TARGET = {38.0: 0.44, 38.3: 0.16, 38.5: 0.06}
GRID = list(product([37.7, 37.8, 37.9, 38.0], [0.4, 0.55, 0.7])) + [(37.7, 0.62), (37.7, 0.65), (37.8, 0.62), (37.8, 0.65)]
GRID = GRID[-4:] if os.environ.get("REFINE") else GRID
N_WORKERS, N_DATES = 48, 3


def job(args):
    worker, dates, mean, factor = args
    hourly = weather.load_hourly("data/weather_hourly.csv")
    return [float(v5.simulate_day(worker, v5.day_minutes(hourly, d), d, pace_mean=mean, pace_factor=factor)[0]["t_re"].max())
            for d in dates]


def main():
    hourly = weather.load_hourly("data/weather_hourly.csv")
    wk = v5.make_workers_v5(N_WORKERS, seed=C.SEED + 900, prefix="K")
    days = sorted(hourly["timestamp"].dt.strftime("%Y-%m-%d").unique())
    rng = np.random.default_rng(C.SEED + 901)
    plan = [(w, sorted(rng.choice(days, N_DATES, replace=False).tolist())) for _, w in wk.iterrows()]
    rows = []
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
        for mean, factor in GRID:
            tmax = np.concatenate(list(pool.map(job, [(w, d, mean, factor) for w, d in plan])))
            shares = {k: float((tmax > k).mean()) for k in TARGET}
            err = sum((shares[k] - TARGET[k]) ** 2 for k in TARGET)
            rows.append({"pace_mean": mean, "pace_factor": factor, **{f"share_{k}": round(v, 3) for k, v in shares.items()},
                         "error": round(err, 4)})
            print(rows[-1], flush=True)
    out = pd.DataFrame(rows).sort_values("error")
    out.to_csv("outputs/v5/pacing_calibration.csv", index=False)
    print("best:\n", out.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
