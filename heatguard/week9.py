"""Week 9 additions (v0.4). New file on purpose: the Week 7 and Week 8 modules do not change.

- FEATURES_V2 / build_features_v2: the Week 8 inputs minus body mass and height, plus two
  "rise since shift start" signals. Reason: Week 8 error analysis showed nearly every miss was
  one worker (W018) whose body build was unlike any training worker. Mass and height never
  change during a shift, so with 18 training workers they act like a name tag; the models
  learned WHO gets hot instead of WHY. Rises are relative to the person, so they transfer.
- Confirmation set: brand-new workers (different seed) on summer dates the study never used,
  scored once at the end, because Week 9 design choices were informed by Week 8 test results.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from . import features, workers

RISE = ["hr_rise", "skin_rise"]
PERSONAL_V2 = ["acclimatised"]
FEATURES_V2 = features.PHYSIO + RISE + features.ACTIVITY + features.ENV + PERSONAL_V2 + features.WORKLOAD + features.QUALITY
# v1 without the constant body measures (no rises): isolates the "name tag" effect
FEATURES_V1B = [c for c in features.ALL_FEATURES if c not in ("mass_kg", "height_m")]
FEATURE_GROUPS_V2 = {"environmental": features.ENV, "physiological": features.PHYSIO + RISE,
                     "workload": features.WORKLOAD + features.ACTIVITY, "personal": PERSONAL_V2,
                     "quality": features.QUALITY}

CONFIRM_SEED = C.SEED + 100
CONFIRM_WORKERS = 12        # 2 per acclimatisation x work-rate group
CONFIRM_DATES = 20


def build_features_v2(msgs: pd.DataFrame, weather_min: pd.DataFrame, worker: pd.Series) -> pd.DataFrame:
    """Week 8 features plus rises since the start of the shift. Only past values are used:
    the reference is the lowest 15-minute average seen SO FAR in this shift (running minimum)."""
    f = features.build_features(msgs, weather_min, worker)
    f["hr_rise"] = (f["hr_mean15"] - f["hr_mean15"].cummin()).fillna(0)
    f["skin_rise"] = (f["skin_mean15"] - f["skin_mean15"].cummin()).fillna(0)
    return f


def confirmation_workers() -> pd.DataFrame:
    wk = workers.make_workers(CONFIRM_WORKERS, seed=CONFIRM_SEED)
    wk["worker_id"] = [f"C{i + 1:03d}" for i in range(len(wk))]
    return wk


def confirmation_dates(hourly: pd.DataFrame, used: list[str]) -> list[str]:
    """Summer dates the main study never used (none of train, validation or test)."""
    all_dates = sorted(hourly["timestamp"].dt.strftime("%Y-%m-%d").unique())
    free = [d for d in all_dates if d not in set(used)]
    rng = np.random.default_rng(CONFIRM_SEED)
    return sorted(rng.choice(free, size=min(CONFIRM_DATES, len(free)), replace=False).tolist())
