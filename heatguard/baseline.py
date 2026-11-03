"""Part 5a: WBGT threshold rule (the baseline).

Input : minute WBGT, the worker's metabolic rate, body size and acclimatisation.
Output: warning on/off for each minute.

NIOSH (2016) limits, with metabolic rate M in watts (whole body):
    unacclimatised -> Recommended Alert Limit     RAL = 59.9 - 14.1 * log10(M)
    acclimatised   -> Recommended Exposure Limit  REL = 56.7 - 11.5 * log10(M)
Both WBGT and M are 60-minute trailing time-weighted averages (elapsed time in the
first hour). Clothing adjustment is 0 for conventional single-layer clothing.
This is a research comparator, not a certified safety programme.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def body_surface_area(mass_kg: float, height_m: float) -> float:
    """DuBois formula, m2."""
    return 0.202 * mass_kg ** 0.425 * height_m ** 0.725


def niosh_limit(m_watts, acclimatised: bool):
    m = np.asarray(m_watts, dtype=float)
    return 56.7 - 11.5 * np.log10(m) if acclimatised else 59.9 - 14.1 * np.log10(m)


def wbgt_rule(wbgt: pd.Series, met_wm2: pd.Series, worker: pd.Series, clothing_adj: float = 0.0) -> pd.DataFrame:
    m_watts = met_wm2 * body_surface_area(worker["mass_kg"], worker["height_m"])
    wbgt_twa = (wbgt + clothing_adj).rolling(60, min_periods=1).mean()
    m_twa = m_watts.rolling(60, min_periods=1).mean()
    limit = niosh_limit(m_twa, bool(worker["acclimatised"]))
    alert = (wbgt_twa > limit).astype(int)
    alert[wbgt.isna()] = -1          # -1 = risk unavailable (no environmental input)
    return pd.DataFrame({"wbgt_twa": wbgt_twa, "wbgt_limit": limit, "wbgt_alert": alert})
