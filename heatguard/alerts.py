"""Part 5c: Alert engine with sensor-offline fallback.

Input : ML probability, WBGT rule state, and reading-quality flags per minute.
Output: three separate policy logs, so the scorer can tell them apart:
    ml          - ML warning only (stale features during dropouts)
    wbgt_rule   - WBGT rule only
    ml_fallback - ML normally; WBGT rule while HR is offline or stuck;
                  "unavailable" if environmental input is also missing (never shows "safe" when blind)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def run_policies(prob: np.ndarray, threshold: float, wbgt_alert: pd.Series, feats: pd.DataFrame) -> pd.DataFrame:
    ml = (prob >= threshold).astype(int)
    degraded = (feats["hr_age"] >= C.HR_OFFLINE_AFTER_MIN) | (feats["hr_stuck"] == 1)
    env_missing = wbgt_alert.to_numpy() == -1
    mode = np.where(degraded, "FALLBACK_WBGT", "ML")
    mode = np.where(degraded & env_missing, "UNAVAILABLE", mode)
    fused = np.where(degraded, wbgt_alert.clip(lower=0), ml)
    fused = np.where(mode == "UNAVAILABLE", 1, fused)   # unknown risk is treated as a warning + manual check
    return pd.DataFrame({
        "prob": prob, "ml": ml, "wbgt_rule": wbgt_alert.clip(lower=0).to_numpy(),
        "ml_fallback": fused, "mode": mode,
    })
