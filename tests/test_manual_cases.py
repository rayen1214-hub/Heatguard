"""Manual test cases (Week 8, rubric A7), with Codex-assisted verification cases (Q IDs).

HOW TO ADD A CASE (no Python knowledge needed):
  1. Write the case in plain words first in docs/team/guides/manual_test_cases.md.
  2. Copy the "# Example" line under the matching list below, remove the "# ", and change the values.
     Use your case ID (M-01, M-02, ...) as the first value.
  3. Run:  python -m pytest tests/test_manual_cases.py -v
     Each case shows as PASSED or FAILED next to its ID. Record the outcome in the guide.
A FAILED case is not a mistake on your part: it may be a real finding. Record it, don't delete it.

The "# Example" lines are format examples only. They are commented out, so they never run and
are not counted as manual cases.
"""
import numpy as np
import pytest

from heatguard import baseline, evaluate, workers
from heatguard import config as C

# ---------------------------------------------------------------------------------------------
# 1. SCORING: given the minutes when a warning was on, and the minute danger started,
#    is the warning counted correctly?  (Rules: paper Section III-E, docs/team/guides/key_numbers.md)
#    Shift length is 360 minutes (minute 0 = 06:00). onset = None means no danger in this shift.
#    (case ID, warning minutes, danger onset minute, expected missed?, expected lead time in min,
#     expected false-alarm episodes)
SCORING_CASES = [
    ("Q-01", [100, 101, 115], 120, False, 20, 0),
    ("Q-02", [40, 41, 100], 120, False, 20, 1),
    # Example: ("M-00", [100, 101, 102], 120, False, 20, 0),
]

# 2. EPISODES: how many separate warning episodes do these warning minutes make?
#    (A new episode needs 5 clear minutes in between.)
#    (case ID, warning minutes, expected number of episodes)
EPISODE_CASES = [
    ("Q-03", [10, 13, 20, 22], 2),
    # Example: ("M-00", [10, 11, 12, 30], 2),
]

# 3. WBGT LIMIT (NIOSH): for this metabolic rate in watts, is the limit about what you expect?
#    (case ID, metabolic rate in W, acclimatised True/False, expected limit in degrees C, tolerance)
LIMIT_CASES = [
    ("Q-04", 100, False, 31.7, 0.01),
    # Example: ("M-00", 300, False, 25.0, 0.5),
]

# 4. DANGER LIMIT: which body-temperature limit applies?
#    (case ID, acclimatised True/False, expected limit in degrees C)
DANGER_CASES = [
    ("Q-05", True, 38.5),
    ("Q-06", False, 38.2),
    # Example: ("M-00", True, 38.5),
]

# 5. SHIFT SCHEDULE: at this minute of the shift, is the worker working or resting,
#    and at what metabolic rate?  (case ID, work rate W/m2, minute, expected "work"/"rest", expected W/m2)
SCHEDULE_CASES = [
    ("Q-07", 165, 44, "work", 165),
    ("Q-08", 165, 45, "rest", 70),
    # Example: ("M-00", 230, 50, "rest", 70),
]
# ---------------------------------------------------------------------------------------------


def _alert(minutes, n=C.SHIFT_MINUTES):
    a = np.zeros(n, dtype=int)
    a[list(minutes)] = 1
    return a


@pytest.mark.parametrize("case, minutes, onset, missed, lead, false_eps", SCORING_CASES,
                         ids=[c[0] for c in SCORING_CASES])
def test_scoring(case, minutes, onset, missed, lead, false_eps):
    s = evaluate.score_shift(_alert(minutes), onset=onset, horizon=30)
    if onset is not None:
        assert s["missed"] == missed, f"{case}: missed was {s['missed']}"
        assert s["lead_min"] == lead, f"{case}: lead time was {s['lead_min']}"
    assert s["false_episodes"] == false_eps, f"{case}: false episodes were {s['false_episodes']}"


@pytest.mark.parametrize("case, minutes, expected", EPISODE_CASES, ids=[c[0] for c in EPISODE_CASES])
def test_episodes(case, minutes, expected):
    got = len(evaluate.episodes(_alert(minutes)))
    assert got == expected, f"{case}: got {got} episodes"


@pytest.mark.parametrize("case, watts, accl, expected, tol", LIMIT_CASES, ids=[c[0] for c in LIMIT_CASES])
def test_wbgt_limit(case, watts, accl, expected, tol):
    got = float(baseline.niosh_limit(watts, accl))
    assert abs(got - expected) <= tol, f"{case}: limit was {got:.2f} °C"


@pytest.mark.parametrize("case, accl, expected", DANGER_CASES, ids=[c[0] for c in DANGER_CASES])
def test_danger_limit(case, accl, expected):
    assert workers.danger_limit(accl) == expected


@pytest.mark.parametrize("case, rate, minute, phase, met", SCHEDULE_CASES, ids=[c[0] for c in SCHEDULE_CASES])
def test_schedule(case, rate, minute, phase, met):
    row = workers.schedule(rate).iloc[minute]
    assert row["phase"] == phase, f"{case}: phase was {row['phase']}"
    assert row["met_wm2"] == met, f"{case}: metabolic rate was {row['met_wm2']}"
