"""Part 3: Simulator ("the body").

Input : one worker profile + one shift of minute weather.
Output: a minute-by-minute trajectory with predicted rectal temperature (the hidden
        reference), skin temperature, WBGT, and the minute the danger limit is first crossed.

PHS (ISO 7933:2023) is run one minute at a time. After each minute, the body state
(core, skin and rectal temperature, sweat rate, evaporative load) is passed in as the
starting point of the next minute, so changing weather can be followed.
tests/test_core.py checks that this chained version matches one steady-condition run.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from pythermalcomfort.models import phs

from . import config as C
from .workers import danger_limit, schedule

STATE_KEYS = ("t_sk", "t_cr", "t_re", "t_cr_eq", "t_sk_t_cr_wg", "sweat_rate_watt", "evap_load_wm2_min")
INITIAL_STATE = dict(t_sk=34.1, t_cr=36.8, t_re=36.8, t_cr_eq=36.8, t_sk_t_cr_wg=0.3,
                     sweat_rate_watt=0.0, evap_load_wm2_min=0.0)
MET_PER_WM2 = 1 / 58.15


def phs_step(state: dict, *, tdb, tr, v, rh, met_wm2, worker) -> dict:
    """Advance the body by one minute. Returns the new state (NaN if inputs are outside ISO limits)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = phs(tdb=tdb, tr=tr, v=v, rh=rh, met=met_wm2 * MET_PER_WM2, clo=C.CLOTHING_CLO,
                posture="standing", duration=1, round_output=False,
                acclimatized=100 if worker["acclimatised"] else 0,
                weight=float(worker["mass_kg"]), height=float(worker["height_m"]), **state)
    return {k: float(getattr(r, k)) for k in STATE_KEYS}


def simulate_shift(worker: pd.Series, weather_min: pd.DataFrame) -> tuple[pd.DataFrame, int | None]:
    """Run one shift. Returns (trajectory, danger onset minute or None)."""
    sched = schedule(worker["work_rate_wm2"])
    traj = pd.concat([sched, weather_min.reset_index(drop=True)], axis=1)
    traj["tr"] = traj["tdb"] + traj["tr_offset"]
    state = dict(INITIAL_STATE)
    rows = []
    for r in traj.itertuples(index=False):
        new = phs_step(state, tdb=r.tdb, tr=r.tr, v=r.v, rh=r.rh, met_wm2=r.met_wm2, worker=worker)
        valid = all(np.isfinite(list(new.values())))
        rows.append({**new, "valid": valid})
        if valid:
            state = new
    traj = pd.concat([traj, pd.DataFrame(rows)], axis=1)
    limit = danger_limit(worker["acclimatised"])
    crossed = np.flatnonzero((traj["t_re"] >= limit).to_numpy())
    onset = int(crossed[0]) if len(crossed) else None
    traj["worker_id"] = worker["worker_id"]
    traj["danger_limit"] = limit
    return traj, onset


def steady_vs_chained(tdb=36.0, rh=50.0, met_wm2=230.0, minutes=120, acclimatised=False) -> tuple[float, float]:
    """Reference check: one PHS run for `minutes` vs `minutes` chained one-minute steps."""
    worker = {"acclimatised": acclimatised, "mass_kg": 75.0, "height_m": 1.8}
    common = dict(tdb=tdb, tr=tdb + C.TR_OFFSET_EXPOSED, v=0.5, rh=rh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        steady = phs(**common, met=met_wm2 * MET_PER_WM2, clo=C.CLOTHING_CLO, posture="standing",
                     duration=minutes, round_output=False, acclimatized=100 if acclimatised else 0,
                     weight=75.0, height=1.8).t_re
    state = dict(INITIAL_STATE)
    for _ in range(minutes):
        state = phs_step(state, met_wm2=met_wm2, worker=worker, **common)
    return float(steady), state["t_re"]
