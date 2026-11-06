"""Feature builder and labels (feeds Part 5).

Input : the message stream, minute weather/WBGT, worker profile.
Output: one feature row per minute using ONLY information available at that minute.

Rules (Section III-D): no centred windows, no backward filling from the future,
no reference-temperature columns. tests/test_core.py checks causality.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

PHYSIO = ["hr_last", "hr_mean5", "hr_mean15", "hr_slope15", "skin_mean5", "skin_mean15", "skin_slope15"]
ACTIVITY = ["act_mean5", "act_mean15"]
ENV = ["wbgt", "wbgt_mean60", "tdb", "rh"]
PERSONAL = ["mass_kg", "height_m", "acclimatised"]
WORKLOAD = ["work_rate_wm2"]
QUALITY = ["hr_age", "hr_stuck"]
FEATURE_GROUPS = {"environmental": ENV, "physiological": PHYSIO, "workload": WORKLOAD + ACTIVITY,
                  "personal": PERSONAL, "quality": QUALITY}
ALL_FEATURES = PHYSIO + ACTIVITY + ENV + PERSONAL + WORKLOAD + QUALITY
ENV_ONLY_FEATURES = ENV + PERSONAL + WORKLOAD


def _slope(s: pd.Series, window: int) -> pd.Series:
    """Change per minute over the trailing window (current minute minus `window` minutes ago)."""
    return (s - s.shift(window)) / window


def build_features(msgs: pd.DataFrame, weather_min: pd.DataFrame, worker: pd.Series) -> pd.DataFrame:
    f = pd.DataFrame({"minute": msgs["minute"].to_numpy()})
    hr = msgs["hr"].reset_index(drop=True)
    hr = hr.where(hr.between(*C.HR_VALID_RANGE))         # implausible readings count as missing (F2)
    skin = msgs["skin_temp"].reset_index(drop=True)
    act = msgs["activity"].reset_index(drop=True)
    hr_ff = hr.ffill()                                   # forward fill = past values only
    f["hr_last"] = hr_ff
    f["hr_mean5"] = hr.rolling(5, min_periods=1).mean().fillna(hr_ff)
    f["hr_mean15"] = hr.rolling(15, min_periods=1).mean().fillna(hr_ff)
    f["hr_slope15"] = _slope(hr_ff, 15).fillna(0)
    f["skin_mean5"] = skin.rolling(5, min_periods=1).mean()
    f["skin_mean15"] = skin.rolling(15, min_periods=1).mean()
    f["skin_slope15"] = _slope(skin.ffill(), 15).fillna(0)
    f["act_mean5"] = act.rolling(5, min_periods=1).mean()
    f["act_mean15"] = act.rolling(15, min_periods=1).mean()
    w = weather_min.reset_index(drop=True)
    f["wbgt"] = w["wbgt"]
    f["wbgt_mean60"] = w["wbgt"].rolling(60, min_periods=1).mean()
    f["tdb"] = w["tdb"]
    f["rh"] = w["rh"]
    for col in PERSONAL + WORKLOAD:
        f[col] = float(worker[col])
    # Reading quality: minutes since the last valid HR, and a stuck-sensor flag
    valid_idx = pd.Series(np.where(hr.notna(), np.arange(len(hr)), np.nan)).ffill()
    f["hr_age"] = (np.arange(len(hr)) - valid_idx).fillna(len(hr)).to_numpy()
    same = hr_ff.diff().eq(0).astype(int)
    run = same.groupby((same == 0).cumsum()).cumsum()
    f["hr_stuck"] = (run >= C.HR_STUCK_AFTER_MIN - 1).astype(int) * hr.notna().astype(int)
    return f


def make_labels(n_minutes: int, onset: int | None, horizon: int) -> pd.Series:
    """1 if the first danger event starts within the next `horizon` minutes, 0 if not.
    NaN = not usable: at/after onset (excluded) or end-of-shift with an incomplete horizon (censored)."""
    t = np.arange(n_minutes, dtype=float)
    y = np.full(n_minutes, np.nan)
    if onset is None:
        y[t + horizon <= n_minutes - 1] = 0
    else:
        before = t < onset
        y[before] = ((onset - t[before]) <= horizon).astype(float)
    return pd.Series(y, name=f"y{horizon}")
