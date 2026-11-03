"""Part 5b: ML early-warning model.

Input : feature rows + labels from the TRAINING partition only.
Output: a fitted model that gives a risk probability per minute, and a warning
        threshold chosen on the VALIDATION partition.

Thursday version: logistic regression only (Week 8 adds random forest and
gradient boosting). Scaling is fitted inside the pipeline on training data only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config as C


def train(X: pd.DataFrame, y: pd.Series, seed: int = C.SEED):
    model = make_pipeline(StandardScaler(),
                          LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed))
    model.fit(X, y)
    return model


def predict_proba(model, X: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def choose_threshold(score_fn, candidates=np.round(np.arange(0.05, 0.96, 0.05), 2)) -> tuple[float, pd.DataFrame]:
    """Pick the operating point on validation data (Section III-D):
    fewest false episodes subject to miss rate <= MAX_MISS_RATE; ties -> longest median lead time.
    `score_fn(threshold)` must return a dict with miss_rate, false_per_shift and median_lead.
    If no threshold meets the constraint, the lowest-miss threshold is returned and flagged."""
    table = pd.DataFrame([{"threshold": t, **score_fn(t)} for t in candidates])
    ok = table[table["miss_rate"] <= C.MAX_MISS_RATE]
    if len(ok):
        best = ok.sort_values(["false_per_shift", "median_lead"], ascending=[True, False]).iloc[0]
        table["constraint_met"] = True
    else:
        best = table.sort_values(["miss_rate", "false_per_shift"]).iloc[0]
        table["constraint_met"] = False
    return float(best["threshold"]), table
