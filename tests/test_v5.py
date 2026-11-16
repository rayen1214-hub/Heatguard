"""Checks for the Week 9 frame v2 code (heatguard/v5.py). Run: python -m pytest tests/test_v5.py"""
import numpy as np
import pandas as pd
import pytest
from pythermalcomfort.environment import mean_radiant_tmp

from heatguard import v5


def test_legal_break_only_inside_the_ban_dates():
    on = v5.schedule_day(165, "2025-07-01")
    off = v5.schedule_day(165, "2025-06-10")
    assert (on.loc[390:539, "phase"] == "break").all()          # 12:30-15:00
    assert (on["phase"] == "break").sum() == 150
    assert (off["phase"] != "break").all()                       # before 15 June: no ban
    assert v5.ban_applies("2025-06-15") and v5.ban_applies("2025-09-15")
    assert not v5.ban_applies("2025-06-14") and not v5.ban_applies("2025-09-16")
    assert len(on) == 720                                        # 06:00-18:00


@pytest.mark.parametrize("tdb, rh, tg, v, published", [
    (35.0, 58.9, 38.7, 4.1, 239),   # Miller & Bates 2007, Table 4, coastal site 1
    (36.7, 54.5, 43.1, 2.7, 199),   # coastal site 2
    (37.6, 32.3, 43.5, 1.8, 232),   # inland site 3
])
def test_twl_close_to_published_field_values(tdb, rh, tg, v, published):
    tr = float(mean_radiant_tmp(tdb=tdb, tg=tg, v=v, standard="ISO"))
    got = v5.twl(tdb, tr, v, rh)
    assert abs(got - published) / published < 0.25, (got, published)


def test_twl_falls_as_heat_rises():
    assert v5.twl(30, 40, 1.0, 50) > v5.twl(40, 50, 1.0, 50) > v5.twl(46, 56, 0.5, 40)


def _traj(phase, hi, tdb=40.0, wet=25.0):
    n = len(phase)
    return pd.DataFrame({"phase": phase, "heat_index": np.full(n, hi), "tdb": np.full(n, tdb),
                         "wet_bulb": np.full(n, wet)})


def test_comparators_follow_their_rules_and_stay_silent_in_the_break():
    phase = ["work"] * 5 + ["break"] * 5
    w_acc = pd.Series({"acclimatised": True})
    w_new = pd.Series({"acclimatised": False})
    twl = np.full(10, 130.0)                                     # buffer zone
    a = v5.comparator_alerts(_traj(phase, 41.0), w_acc, twl, np.ones(10))
    b = v5.comparator_alerts(_traj(phase, 39.0), w_new, twl, np.ones(10))
    assert a["c1_ban"].sum() == 0
    assert a["c2_heat_index"].tolist() == [1] * 5 + [0] * 5      # 41 >= 40, silent in the break
    assert b["c2_heat_index"].sum() == 0                         # 39 < 40
    assert a["c3_twl"].sum() == 0 and b["c3_twl"].sum() == 5     # 130: only unacclimatised are stopped
    assert a["c4_wbgt"].sum() == 5


def test_twl_hard_limits_on_dry_and_wet_bulb():
    w = pd.Series({"acclimatised": True})
    hot = v5.comparator_alerts(_traj(["work"] * 3, 30.0, tdb=44.5), w, np.full(3, 200.0), np.zeros(3))
    humid = v5.comparator_alerts(_traj(["work"] * 3, 30.0, wet=32.5), w, np.full(3, 200.0), np.zeros(3))
    assert hot["c3_twl"].sum() == 3 and humid["c3_twl"].sum() == 3


def test_heatguard_ceiling_at_heat_index_54():
    phase = ["work"] * 4 + ["break"] * 2
    traj = _traj(phase, 55.0)
    assert v5.heatguard_alert(np.zeros(6), traj).tolist() == [1, 1, 1, 1, 0, 0]
    assert v5.heatguard_alert(np.zeros(6), _traj(phase, 53.0)).sum() == 0


def test_f14_traits_and_spread_scaling():
    wk = v5.make_workers_v5(200, seed=1)
    assert wk["core_offset"].abs().max() <= v5.CORE_OFFSET_CLIP
    assert wk["replace_frac"].between(*v5.REPLACE_RANGE).all()
    assert wk["dehyd_gain"].between(*v5.DEHYD_GAIN_RANGE).all()
    narrow, wide = v5.scale_spread(wk, 0.5), v5.scale_spread(wk, 1.5)
    assert narrow["core_offset"].std() < wk["core_offset"].std() < wide["core_offset"].std()
    assert v5.scale_spread(wk, 0.0)["core_offset"].abs().max() == 0


def test_simulated_day_sweat_and_dehydration_add_up():
    hourly = pd.read_csv("data/weather_hourly.csv", parse_dates=["timestamp"])
    worker = v5.make_workers_v5(6, seed=2).iloc[0]
    traj, onset = v5.simulate_day(worker, v5.day_minutes(hourly, "2025-07-20"), "2025-07-20")
    assert traj["sweat_cum_g"].dropna().is_monotonic_increasing            # PHS running total
    assert (traj["body_loss_pct"].diff().dropna() >= -1e-9).all()
    extra = traj["t_re"] - traj["t_re_iso"]
    assert extra.iloc[0] == pytest.approx(worker["core_offset"], abs=0.01)   # + first-minute sweat
    if onset is not None:
        assert traj.loc[onset, "phase"] != "break"
