"""Core checks that must pass before any result is trusted.  Run:  python -m pytest -q"""
import numpy as np
import pandas as pd

from heatguard import evaluate, features, simulator, wearables, workers


def test_chained_phs_matches_steady_run():
    """Section III-C: the minute-by-minute adapter must reproduce a steady-condition reference."""
    for acclimatised in (False, True):
        steady, chained = simulator.steady_vs_chained(acclimatised=acclimatised)
        assert abs(steady - chained) < 0.05, (acclimatised, steady, chained)


def _toy_shift(n=120):
    traj = pd.DataFrame({
        "timestamp": pd.date_range("2025-08-01 06:00", periods=n, freq="min"),
        "minute": np.arange(n), "met_wm2": 230.0,
        "t_cr": np.linspace(36.8, 38.5, n), "t_sk": np.linspace(34.5, 36.0, n),
    })
    worker = workers.make_workers(2).iloc[0]
    weather_min = pd.DataFrame({"wbgt": 30.0, "tdb": 38.0, "rh": 40.0}, index=range(n))
    return traj, worker, weather_min


def test_faults_do_not_change_the_body():
    traj, worker, _ = _toy_shift()
    before = traj.copy()
    msgs = wearables.make_messages(traj, worker, seed=1)
    faulty = wearables.inject_fault(msgs, "S5_dropout", seed=1)
    pd.testing.assert_frame_equal(traj, before)
    assert faulty.loc[faulty.minute.between(60, 69), "hr"].isna().all()
    assert msgs["hr"].notna().all()


def test_features_are_causal():
    """Changing the future must not change any past feature value."""
    traj, worker, weather_min = _toy_shift()
    msgs = wearables.make_messages(traj, worker, seed=1)
    f1 = features.build_features(msgs, weather_min, worker)
    future = msgs.copy()
    future.loc[future.minute >= 80, ["hr", "skin_temp", "activity"]] = 999.0
    f2 = features.build_features(future, weather_min, worker)
    pd.testing.assert_frame_equal(f1.iloc[:80], f2.iloc[:80])


def test_no_reference_temperature_in_features():
    banned = {"t_re", "t_cr", "t_sk", "t_re_reference"}
    assert not banned & set(features.ALL_FEATURES)


def test_labels_exclude_rows_after_onset_and_censor_the_end():
    y = features.make_labels(100, onset=50, horizon=30)
    assert y.iloc[50:].isna().all()
    assert y.iloc[20:50].eq(1).all() and y.iloc[:20].eq(0).all()
    y0 = features.make_labels(100, onset=None, horizon=30)
    assert y0.iloc[70:].isna().all() and y0.iloc[:69].eq(0).all()


def test_scoring_rules():
    alert = np.zeros(100, dtype=int)
    alert[5:8] = 1          # early false episode
    alert[55:60] = 1        # warning 15 minutes before onset at 70
    s = evaluate.score_shift(alert, onset=70, horizon=30)
    assert s["lead_min"] == 15 and not s["missed"] and s["false_episodes"] == 1
    missed = evaluate.score_shift(np.zeros(100), onset=70, horizon=30)
    assert missed["missed"] and missed["lead_min"] == 0


def test_split_has_no_shared_workers_or_dates():
    ids = [f"W{i:03d}" for i in range(1, 11)]
    dates = [f"2025-07-{d:02d}" for d in range(1, 11)]
    split = workers.make_split(ids, dates, dict(worker_split=(6, 2, 2), date_split=(6, 2, 2)))
    for col in ("worker_id", "date"):
        parts = split.groupby(col)["partition"].nunique()
        assert (parts == 1).all(), f"{col} appears in more than one partition"


def test_minute_weather_actually_varies():
    """Regression test for the v0.1 bug where every minute got the same weather."""
    from heatguard import weather
    ts = pd.date_range("2025-08-01", "2025-08-02 23:00", freq="h")
    hourly = pd.DataFrame({"timestamp": ts, "temperature_2m": np.arange(len(ts), dtype=float),
                           "relative_humidity_2m": 40.0, "surface_pressure": 1000.0, "wind_speed_10m": 3.0,
                           "shortwave_radiation": 500.0, "direct_radiation": 300.0, "source": "unit-test"})
    w = weather.shift_minutes(hourly, "2025-08-01")
    assert w["tdb"].iloc[0] == 6.0 and abs(w["tdb"].iloc[90] - 7.5) < 1e-9 and w["tdb"].iloc[-1] > 11.9


def test_every_partition_gets_every_profile_group():
    """Regression test: the first full run put only light-work unacclimatised and heavy-work
    acclimatised workers in the test set, so the test set could not contain danger events."""
    from heatguard import config as C
    wk = workers.make_workers(30)
    dates = [f"2025-07-{d:02d}" for d in range(1, 31)] + [f"2025-08-{d:02d}" for d in range(1, 31)]
    split = workers.make_split(wk["worker_id"].tolist(), dates, C.FULL)
    m = split.drop_duplicates("worker_id").merge(wk)
    counts = m.groupby(["partition", "acclimatised", "work_rate_wm2"]).size()
    assert len(counts) == 3 * 6 and counts.loc["test"].min() == 1 and counts.loc["train"].min() == 3
