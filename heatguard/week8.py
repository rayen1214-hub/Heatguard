"""Week 8 additions: more models, uncertainty, factor importance (E5).

New file on purpose: nothing in the Week 7 modules changes. run_week8.py uses this file
together with the existing parts (features, baseline, alerts, evaluate).

- make_model: logistic regression (Week 7), random forest, gradient boosting.
- bootstrap_ci: 95% interval for a median, by resampling danger events.
- paired_differences: per-event lead-time difference between two policies.
- grouped_importance: E5, how much each factor group matters (drop in average precision
  when that group's columns are shuffled together).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config as C
from . import features

MODELS = ("logreg", "random_forest", "grad_boost")


def make_model(name: str, seed: int = C.SEED):
    """All three handle the rare danger class with balanced class weights.
    A median imputer (fitted on training data) covers minutes before the first heart-rate
    reading arrives; without it the Week 7 model crashes on such shifts (finding F1,
    docs/test_cases.md). The fallback to WBGT still decides during those minutes."""
    if name == "logreg":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed))
    if name == "random_forest":
        return make_pipeline(SimpleImputer(strategy="median"),
                             RandomForestClassifier(n_estimators=200, min_samples_leaf=20,
                                                    class_weight="balanced_subsample", n_jobs=-1, random_state=seed))
    if name == "grad_boost":
        # handles missing values itself, so no imputer is needed
        return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, class_weight="balanced",
                                              random_state=seed)
    raise ValueError(name)


def bootstrap_ci(values, stat=np.median, n_boot: int = 2000, seed: int = C.SEED) -> tuple[float, float]:
    """95% percentile interval for `stat` by resampling the values with replacement."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    boots = [stat(rng.choice(v, len(v), replace=True)) for _ in range(n_boot)]
    return (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))


def paired_differences(scores: pd.DataFrame, policy_a: str, policy_b: str) -> pd.Series:
    """Lead time of a minus lead time of b, for each danger event both policies saw."""
    keys = ["worker_id", "date", "scenario", "fold"]
    a = scores[(scores["policy"] == policy_a) & scores["event"]]
    b = scores[(scores["policy"] == policy_b) & scores["event"]]
    m = a.merge(b, on=keys, suffixes=("_a", "_b"))
    return (m["lead_min_a"] - m["lead_min_b"]).astype(float)


def grouped_importance(model, X: pd.DataFrame, y: pd.Series, n_repeats: int = 5,
                       seed: int = C.SEED) -> pd.DataFrame:
    """E5: drop in average precision when one factor group is shuffled (all its columns
    moved together, rows kept intact). Bigger drop = the model relies more on that group."""
    rng = np.random.default_rng(seed)
    base = average_precision_score(y, model.predict_proba(X[features.ALL_FEATURES])[:, 1])
    rows = []
    for group, cols in features.FEATURE_GROUPS.items():
        drops = []
        for _ in range(n_repeats):
            Xp = X.copy()
            idx = rng.permutation(len(Xp))
            Xp[cols] = Xp[cols].to_numpy()[idx]
            drops.append(base - average_precision_score(y, model.predict_proba(Xp[features.ALL_FEATURES])[:, 1]))
        rows.append({"group": group, "features": ", ".join(cols), "baseline_ap": round(base, 4),
                     "ap_drop_mean": round(float(np.mean(drops)), 4), "ap_drop_sd": round(float(np.std(drops)), 4)})
    return pd.DataFrame(rows).sort_values("ap_drop_mean", ascending=False)
