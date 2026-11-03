"""Part 6a: Scorer (E1-E4).

Input : one policy's warning log per shift + the hidden danger onset minute.
Output: lead time, missed events, false warning episodes and warning minutes.

Rules (Section III-E):
- An episode = consecutive warning minutes; a new episode needs EPISODE_GAP_MIN clear minutes.
- Valid warning window = the `horizon` minutes before onset. Lead time is counted from the
  earliest warning minute in that window, capped at the horizon. No warning there = missed.
- False episode = an episode with no overlap with the pre-event window.
- Scoring stops at the first danger onset. Without an event, episodes that start in the
  last `horizon` minutes are not scored (their outcome horizon is incomplete).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def episodes(alert: np.ndarray, gap: int = C.EPISODE_GAP_MIN) -> list[tuple[int, int]]:
    """(start, end) minute pairs, inclusive."""
    on = np.flatnonzero(np.asarray(alert) > 0)
    if len(on) == 0:
        return []
    eps, start, prev = [], on[0], on[0]
    for m in on[1:]:
        if m - prev > gap:
            eps.append((start, prev))
            start = m
        prev = m
    eps.append((start, prev))
    return eps


def score_shift(alert: np.ndarray, onset: int | None, horizon: int) -> dict:
    alert = np.asarray(alert)
    n = len(alert)
    end = onset if onset is not None else n
    scored = alert[:end]
    eps = episodes(scored)
    out = {"event": onset is not None, "warning_minutes": int((scored > 0).sum())}
    if onset is not None:
        w0 = max(0, onset - horizon)
        hits = np.flatnonzero(alert[w0:onset] > 0)
        out["missed"] = len(hits) == 0
        out["lead_min"] = 0.0 if out["missed"] else float(onset - (w0 + hits[0]))
        out["false_episodes"] = sum(1 for s, e in eps if e < w0)
    else:
        out["missed"], out["lead_min"] = None, None
        out["false_episodes"] = sum(1 for s, e in eps if s <= n - 1 - horizon)
    return out


def summarise(scores: pd.DataFrame) -> dict:
    """E1-E3 for one policy over many shifts (misses count as zero lead time)."""
    ev = scores[scores["event"]]
    n_ev = len(ev)
    return {
        "shifts": len(scores),
        "events": n_ev,
        "missed": int(ev["missed"].sum()) if n_ev else 0,
        "miss_rate": float(ev["missed"].mean()) if n_ev else float("nan"),
        "median_lead": float(ev["lead_min"].median()) if n_ev else float("nan"),
        "lead_iqr": (float(ev["lead_min"].quantile(.25)), float(ev["lead_min"].quantile(.75))) if n_ev else None,
        "false_per_shift": float(scores["false_episodes"].mean()),
        "warning_min_per_shift": float(scores["warning_minutes"].mean()),
    }


def paired_lead_difference(a: pd.DataFrame, b: pd.DataFrame) -> float:
    """Median of (policy a lead - policy b lead) over the same danger events (E1 paired)."""
    m = a[a["event"]].merge(b[b["event"]], on=["worker_id", "date", "scenario"], suffixes=("_a", "_b"))
    return float((m["lead_min_a"] - m["lead_min_b"]).median()) if len(m) else float("nan")
