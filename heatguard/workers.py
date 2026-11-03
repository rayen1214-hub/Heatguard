"""Part 2: Worker and shift generator.

Input : number of workers, seed.
Output: worker profiles, the work/rest schedule, and the train/validation/test split.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def make_workers(n: int, seed: int = C.SEED) -> pd.DataFrame:
    """Virtual workers. Acclimatisation and work rate are balanced, then shuffled."""
    rng = np.random.default_rng(seed)
    acclim = np.resize([True, False], n)
    rates = np.resize(C.WORK_RATES_WM2, n)
    rng.shuffle(acclim)
    rng.shuffle(rates)
    return pd.DataFrame({
        "worker_id": [f"W{i + 1:03d}" for i in range(n)],
        "mass_kg": rng.uniform(*C.MASS_RANGE_KG, n).round(1),
        "height_m": rng.uniform(*C.HEIGHT_RANGE_M, n).round(2),
        "acclimatised": acclim,
        "work_rate_wm2": rates,
        # Wearable generator settings (worker-specific variation in heart rate)
        "hr_rest": rng.normal(70, 6, n).round(1),
        "hr_work_gain": rng.uniform(0.18, 0.30, n).round(3),   # bpm per W/m2 above rest
    })


def danger_limit(acclimatised: bool) -> float:
    return C.DANGER_LIMIT_ACCLIMATISED if acclimatised else C.DANGER_LIMIT_UNACCLIMATISED


def schedule(work_rate_wm2: float) -> pd.DataFrame:
    """45 min exposed work + 15 min shaded rest, each hour of the shift."""
    minute = np.arange(C.SHIFT_MINUTES)
    working = (minute % 60) < C.WORK_MINUTES_PER_HOUR
    return pd.DataFrame({
        "minute": minute,
        "phase": np.where(working, "work", "rest"),
        "met_wm2": np.where(working, work_rate_wm2, C.REST_MET_WM2),
        "tr_offset": np.where(working, C.TR_OFFSET_EXPOSED, C.TR_OFFSET_SHADE),
    })


def partition(items: list, sizes: tuple[int, int, int], seed: int) -> dict[str, list]:
    """Assign items to train/val/test. Dates are passed in sorted order and split
    chronologically; workers are shuffled first."""
    assert sum(sizes) == len(items), "split sizes must add up to the number of items"
    a, b, _ = sizes
    return {"train": items[:a], "val": items[a:a + b], "test": items[a + b:]}


def _alternate_by_acclimatisation(worker_ids: list[str], seed: int) -> list[str]:
    """Shuffle, then alternate acclimatised / unacclimatised workers so every
    partition gets both groups (stratified split)."""
    wk = make_workers(len(worker_ids), seed).set_index("worker_id").loc[worker_ids]
    rng = np.random.default_rng(seed + 1)
    acc = list(rng.permutation(wk.index[wk["acclimatised"]]))
    una = list(rng.permutation(wk.index[~wk["acclimatised"]]))
    order = []
    while acc or una:
        if una:
            order.append(una.pop())
        if acc:
            order.append(acc.pop())
    return order


def make_split(worker_ids: list[str], dates: list[str], design: dict, seed: int = C.SEED) -> pd.DataFrame:
    """Only worker/date pairs from the SAME partition are simulated, so no worker
    or date leaks across train, validation and test."""
    wp = partition(_alternate_by_acclimatisation(worker_ids, seed), design["worker_split"], seed)
    dp = partition(sorted(dates), design["date_split"], seed)
    rows = [(w, d, part) for part in ("train", "val", "test") for w in wp[part] for d in dp[part]]
    return pd.DataFrame(rows, columns=["worker_id", "date", "partition"])
