"""AI-generated edge-case tests (Week 8, rubric A7).

Proposed by Claude (Claude Code) on 6 Nov 2026. Each test carries the ID used in
docs/test_cases.md, where the group records whether the case was accepted, modified or
rejected, and why. A failing test here is a finding, not something to hide: record it in
docs/test_cases.md and docs/iteration_log.md before changing any code.

Run:  python -m pytest tests/test_ai_cases.py -v
"""
import numpy as np
import pandas as pd
import pytest

from heatguard import alerts, baseline, evaluate, features, model, wearables, week8, workers
from heatguard import config as C


def _toy(n=120, hr=None):
    traj = pd.DataFrame({
        "timestamp": pd.date_range("2025-08-01 06:00", periods=n, freq="min"),
        "minute": np.arange(n), "met_wm2": 230.0,
        "t_cr": np.linspace(36.8, 38.5, n), "t_sk": np.linspace(34.5, 36.0, n),
    })
    worker = workers.make_workers(2).iloc[0].copy()
    worker["worker_id"] = "W001"
    weather_min = pd.DataFrame({"wbgt": 30.0, "tdb": 38.0, "rh": 40.0}, index=range(n))
    msgs = wearables.make_messages(traj, worker, seed=1)
    if hr is not None:
        msgs["hr"] = hr
    return traj, worker, weather_min, msgs


def _modes(msgs, weather_min, worker, wbgt_alert=None):
    f = features.build_features(msgs, weather_min, worker)
    wa = pd.Series(np.zeros(len(f))) if wbgt_alert is None else wbgt_alert
    return alerts.run_policies(np.zeros(len(f)), 0.5, wa, f)["mode"].to_numpy(), f


# --- Sensor faults ------------------------------------------------------------------

def test_AI01_no_heart_rate_and_no_weather_is_never_shown_as_safe():
    """AI-01: HR missing all shift AND WBGT missing -> UNAVAILABLE (treated as a warning)."""
    traj, worker, weather_min, msgs = _toy(hr=np.nan)
    f = features.build_features(msgs, weather_min, worker)
    pol = alerts.run_policies(np.zeros(len(f)), 0.5, pd.Series(-np.ones(len(f))), f)
    assert (pol["mode"] == "UNAVAILABLE").all()
    assert (pol["ml_fallback"] == 1).all()


def test_AI02_sensor_that_never_connects_falls_back_from_the_first_minute():
    """AI-02: HR missing from minute 0 -> WBGT fallback from minute 0."""
    traj, worker, weather_min, msgs = _toy(hr=np.nan)
    modes, _ = _modes(msgs, weather_min, worker)
    assert (modes == "FALLBACK_WBGT").all()


@pytest.mark.parametrize("held, flagged", [(C.HR_STUCK_AFTER_MIN - 1, False), (C.HR_STUCK_AFTER_MIN, True)])
def test_AI03_stuck_sensor_boundary(held, flagged):
    """AI-03: 4 identical readings are allowed, 5 trigger the stuck flag."""
    traj, worker, weather_min, msgs = _toy()
    msgs.loc[msgs.minute.between(40, 40 + held - 1), "hr"] = 123.4
    _, f = _modes(msgs, weather_min, worker)
    assert bool(f["hr_stuck"].iloc[40:40 + held].any()) == flagged


@pytest.mark.xfail(strict=True, reason="Finding F1: Week 7 model crashes on missing features (docs/test_cases.md)")
def test_AI04_model_handles_a_shift_with_no_heart_rate_at_all():
    """AI-04: the ML model must still return a probability when HR never arrives
    (features are then missing). The fallback decides, but the model must not crash."""
    traj, worker, weather_min, msgs = _toy()
    f = features.build_features(msgs, weather_min, worker)
    y = pd.Series((np.arange(len(f)) > 60).astype(int))
    clf = model.train(f[features.ALL_FEATURES], y)
    _, _, _, dead = _toy(hr=np.nan)
    fd = features.build_features(dead, weather_min, worker)
    p = model.predict_proba(clf, fd[features.ALL_FEATURES])
    assert len(p) == len(fd) and np.all((p >= 0) & (p <= 1))


def test_AI05_implausible_heart_rate_values_are_flagged():
    """AI-05: readings of 0 or 250 bpm (loose strap, electrical spike) should not be used
    as if they were real. Expected: treated like missing readings."""
    traj, worker, weather_min, msgs = _toy()
    msgs.loc[50, "hr"] = 0.0
    msgs.loc[51, "hr"] = 250.0
    _, f = _modes(msgs, weather_min, worker)
    assert f.loc[51, "hr_last"] != 250.0, "implausible reading passed straight into the features"


# --- Scoring rules (E1-E3) ------------------------------------------------------------

def test_AI06_warning_one_minute_before_onset_counts():
    alert = np.zeros(100, dtype=int)
    alert[69] = 1
    s = evaluate.score_shift(alert, onset=70, horizon=30)
    assert not s["missed"] and s["lead_min"] == 1


def test_AI07_warning_only_at_the_onset_minute_is_a_miss():
    alert = np.zeros(100, dtype=int)
    alert[70:] = 1
    s = evaluate.score_shift(alert, onset=70, horizon=30)
    assert s["missed"]


def test_AI08_warning_just_outside_the_window_is_a_miss_and_a_false_episode():
    alert = np.zeros(100, dtype=int)
    alert[39] = 1                      # window is minutes 40-69 for onset 70
    s = evaluate.score_shift(alert, onset=70, horizon=30)
    assert s["missed"] and s["false_episodes"] == 1


@pytest.mark.parametrize("gap, n_episodes", [(C.EPISODE_GAP_MIN, 1), (C.EPISODE_GAP_MIN + 1, 2)])
def test_AI09_episode_gap_boundary(gap, n_episodes):
    """Two warnings `gap` minutes apart: up to EPISODE_GAP_MIN apart they are one episode."""
    alert = np.zeros(50, dtype=int)
    alert[10] = 1
    alert[10 + gap] = 1
    assert len(evaluate.episodes(alert)) == n_episodes


def test_AI10_late_warnings_on_event_free_shift_are_not_false_alarms():
    """Episodes starting in the last `horizon` minutes have an incomplete outcome and are not scored."""
    alert = np.zeros(360, dtype=int)
    alert[345:] = 1
    s = evaluate.score_shift(alert, onset=None, horizon=30)
    assert s["false_episodes"] == 0


# --- WBGT baseline ------------------------------------------------------------------

def test_AI11_wbgt_limit_falls_as_work_gets_harder():
    w = workers.make_workers(2).iloc[0]
    wbgt = pd.Series(np.full(120, 30.0))
    lims = [baseline.wbgt_rule(wbgt, pd.Series(np.full(120, m)), w)["wbgt_limit"].iloc[-1] for m in (100, 165, 230)]
    assert lims[0] > lims[1] > lims[2]


def test_AI12_acclimatised_limit_is_higher():
    w = workers.make_workers(2).iloc[0].copy()
    wbgt, met = pd.Series(np.full(120, 30.0)), pd.Series(np.full(120, 230.0))
    w["acclimatised"] = True
    hi = baseline.wbgt_rule(wbgt, met, w)["wbgt_limit"].iloc[-1]
    w["acclimatised"] = False
    lo = baseline.wbgt_rule(wbgt, met, w)["wbgt_limit"].iloc[-1]
    assert hi > lo


# --- Week 8 statistics --------------------------------------------------------------

def test_AI13_bootstrap_interval_edge_cases():
    assert week8.bootstrap_ci([5, 5, 5, 5]) == (5.0, 5.0)
    assert all(np.isnan(week8.bootstrap_ci([5])))
    lo, hi = week8.bootstrap_ci(np.arange(100))
    assert lo < np.median(np.arange(100)) < hi


def test_AI14_threshold_choice_when_no_threshold_meets_the_miss_limit():
    """If every threshold misses too much, the lowest-miss one is picked and flagged."""
    def score_fn(t):
        return {"miss_rate": 0.5 + t / 10, "false_per_shift": 1 - t, "median_lead": 10}
    thr, table = model.choose_threshold(score_fn)
    assert thr == 0.05 and not table["constraint_met"].iloc[0]


@pytest.mark.parametrize("name", week8.MODELS)
def test_AI15_every_model_gives_valid_probabilities(name):
    """All Week 8 models return probabilities, including for a shift with no heart rate (F1 fixed there)."""
    traj, worker, weather_min, msgs = _toy()
    f = features.build_features(msgs, weather_min, worker)
    y = (np.arange(len(f)) > 60).astype(int)
    clf = week8.make_model(name).fit(f[features.ALL_FEATURES], y)
    _, _, _, dead = _toy(hr=np.nan)
    for X in (f, features.build_features(dead, weather_min, worker)):
        p = clf.predict_proba(X[features.ALL_FEATURES])[:, 1]
        assert p.shape == (len(X),) and np.all((p >= 0) & (p <= 1))
