"""Part 4: Wearable messages and faults.

Input : a simulated trajectory + worker profile.
Output: one JSON message per minute on an MQTT-style topic, e.g.
        heatguard/worker/W001/vitals  {"ts": ..., "hr": 112.4, "skin_temp": 35.6, "activity": 3.9}

No broker is used: messages are replayed in timestamp order in Python. Faults are
injected into the messages only; the body trajectory and labels never change.

Known limitation: heart rate is generated from the same simulated body that produces
the labels (HR_THERMAL_GAIN). Lower that gain to test how much the ML result depends on it.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C


def make_messages(traj: pd.DataFrame, worker: pd.Series, seed: int,
                  hr_noise=C.HR_NOISE_SD, skin_noise=C.SKIN_NOISE_SD,
                  thermal_gain=C.HR_THERMAL_GAIN, recovery_fraction=0.5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    target = (worker["hr_rest"]
              + worker["hr_work_gain"] * (traj["met_wm2"] - C.REST_MET_WM2)
              + thermal_gain * (traj["t_cr"].ffill() - 36.8).clip(lower=0))
    hr = np.empty(len(traj))
    hr_now = float(worker["hr_rest"])
    resting = traj["met_wm2"].to_numpy() <= C.REST_MET_WM2
    for i, t in enumerate(target.to_numpy()):
        if resting[i]:
            hr_now += (t - hr_now) * recovery_fraction
        else:
            hr_now += (t - hr_now) / 2.0
        hr[i] = hr_now
    msgs = pd.DataFrame({
        "ts": traj["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "minute": traj["minute"],
        "topic": f"heatguard/worker/{worker['worker_id']}/vitals",
        "worker_id": worker["worker_id"],
        "device_id": f"D-{worker['worker_id']}",
        "hr": (hr + rng.normal(0, hr_noise, len(hr))).round(1),
        "skin_temp": (traj["t_sk"].ffill() + rng.normal(0, skin_noise, len(hr))).round(2),
        "activity": (traj["met_wm2"] * (1 / 58.15) + rng.normal(0, 0.15, len(hr))).round(2),
    })
    return msgs


# --- Fault scenarios from Table III -------------------------------------------------
def inject_fault(msgs: pd.DataFrame, scenario: str, seed: int, worker: pd.Series | None = None,
                 traj: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return a faulty copy of the messages. Timing never depends on the danger onset."""
    m = msgs.copy()
    rng = np.random.default_rng(seed + 7)
    if scenario == "clean":
        return m
    if scenario == "S5_dropout":            # 10-minute HR dropout from minute 60
        m.loc[m["minute"].between(60, 69), "hr"] = np.nan
    elif scenario == "S5_missing10":        # 10% random missing HR
        m.loc[rng.random(len(m)) < 0.10, "hr"] = np.nan
    elif scenario == "S5_missing30":
        m.loc[rng.random(len(m)) < 0.30, "hr"] = np.nan
    elif scenario == "S6_stuck":            # HR held at its last value for 15 minutes from minute 60
        m.loc[m["minute"].between(60, 74), "hr"] = m.loc[m["minute"] == 59, "hr"].iloc[0]
    elif scenario == "S7_noise":            # noise raised to 8 bpm / 0.5 C (needs traj + worker)
        assert traj is not None and worker is not None
        return make_messages(traj, worker, seed, hr_noise=8.0, skin_noise=0.5)
    else:
        raise ValueError(f"unknown scenario {scenario}")
    return m


def to_jsonl(msgs: pd.DataFrame, path: str | Path) -> None:
    """Write the stream as JSON lines, one MQTT-style message per line (missing HR -> null)."""
    with open(path, "w") as f:
        for rec in msgs.to_dict("records"):
            topic = rec.pop("topic")
            payload = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in rec.items()}
            f.write(json.dumps({"topic": topic, "payload": payload}) + "\n")
