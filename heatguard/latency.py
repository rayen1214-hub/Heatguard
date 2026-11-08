"""Latency measures (answers tutor feedback of 29 Oct 2026).

Two kinds of latency, both measured on TEST shifts:

1. Decision latency: wall-clock time from one wearable message arriving to the alert
   decision for that minute. Each shift is replayed message by message, as an edge
   device would see it: features are rebuilt from the history so far, then the model
   and alert engine run. Network and broker delays are NOT included (there is no broker,
   decision D6), so this is processing time only.

2. Fault-detection delay: minutes from the first faulty heart-rate reading to the
   minute the system switches to WBGT fallback, and from the end of the fault back to ML.
   Read from the per-minute policy logs.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import alerts, features, model

# Fault windows as injected by wearables.inject_fault (first and last faulty minute)
FAULT_WINDOWS = {"S5_dropout": (60, 69), "S6_stuck": (60, 74)}


def decision_latency(clf, threshold: float, shifts: list, max_shifts: int = 10) -> dict:
    """shifts: list of (msgs, weather_min, worker, rule) for test shifts.
    Returns per-message processing time in milliseconds."""
    times = []
    for msgs, weather_min, worker, rule in shifts[:max_shifts]:
        msgs = msgs.reset_index(drop=True)
        weather_min = weather_min.reset_index(drop=True)
        for t in range(len(msgs)):
            start = time.perf_counter()
            f = features.build_features(msgs.iloc[: t + 1], weather_min.iloc[: t + 1], worker)
            last = f.iloc[[-1]]
            p = model.predict_proba(clf, last[features.ALL_FEATURES])
            alerts.run_policies(p, threshold, rule["wbgt_alert"].iloc[[t]].reset_index(drop=True), last)
            times.append((time.perf_counter() - start) * 1000)
    a = np.array(times)
    return {"messages": int(a.size), "shifts": min(len(shifts), max_shifts),
            "median_ms": round(float(np.median(a)), 2), "p95_ms": round(float(np.percentile(a, 95)), 2),
            "max_ms": round(float(a.max()), 2), "budget_ms": 60_000,
            "note": "processing time per one-minute message on the run machine; excludes network"}


def fault_detection_delay(policy_logs: pd.DataFrame) -> dict:
    """Minutes from fault start to FALLBACK_WBGT, and from fault end back to ML, per scenario."""
    out = {}
    for scenario, (first, last) in FAULT_WINDOWS.items():
        g = policy_logs[policy_logs["scenario"] == scenario]
        detect, recover = [], []
        for _, s in g.groupby(["worker_id", "date"]):
            s = s.sort_values("minute")
            fb = s.loc[(s["minute"] >= first) & (s["mode"] != "ML"), "minute"]
            if len(fb):
                detect.append(int(fb.iloc[0]) - first)
            back = s.loc[(s["minute"] > last) & (s["mode"] == "ML"), "minute"]
            if len(back):
                recover.append(int(back.iloc[0]) - last)
        out[scenario] = {
            "fault_minutes": f"{first}-{last}", "shifts": len(detect),
            "detect_delay_min_median": float(np.median(detect)) if detect else None,
            "detect_delay_min_max": int(max(detect)) if detect else None,
            "recover_delay_min_median": float(np.median(recover)) if recover else None,
            "minutes_in_fallback_per_shift": round(float(
                (g["mode"] != "ML").sum() / max(len(detect), 1)), 1),
        }
    return out
