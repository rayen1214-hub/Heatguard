"""Week 9 frame v2 (v0.5). New file on purpose: the Week 7-9 modules do not change.

Everything here follows the decisions CR signed off on 16 Nov 2026
(research frame v2, Sections 2, 4 and 5):

- F4  full UAE working day 06:00-18:00. From 15 June to 15 September the legal midday
      break (12:30-15:00) is in the schedule; outside those dates work goes on at midday.
- C1  midday break only   -> no warnings at all (the break is the whole protection)
- C2  break + Dubai Heat Index rule  -> warn when the Heat Index is 40 C or more
- C3  break + Abu Dhabi TWL rule     -> warn by the OSHAD / Bates & Schneider (2008) zones
- C4  break + WBGT (NIOSH limits)    -> heatguard.baseline.wbgt_rule (unchanged)
- HG  break + HeatGuard              -> ML warning with WBGT fallback, plus the hard ceiling:
      everyone is warned when the Heat Index is 54 C or more (decision 5)
- F14 person-to-person differences from documented causes (resting core temperature,
      hydration), on top of body size, acclimatisation, work rate and heart-rate fitness.

Nothing in this file scores held-out data. run_v5.py does that, once, after the
pre-registration is committed.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from pythermalcomfort.models import heat_index_rothfusz, phs
from pythermalcomfort.utilities import wet_bulb_tmp

from . import config as C
from . import simulator, weather, workers

# --- F4: the working day --------------------------------------------------------------
DAY_START_HOUR = 6
DAY_MINUTES = 720                       # 06:00-18:00
BAN_START_MIN = 6 * 60 + 30             # minute 390 of the day = 12:30
BAN_END_MIN = 9 * 60                    # minute 540 = 15:00
BAN_FIRST_DAY = (6, 15)                 # 15 June
BAN_LAST_DAY = (9, 15)                  # 15 September (inclusive)

# --- C2 / ceiling: Heat Index (deg C) --------------------------------------------------
HI_WARN = 40.0                          # Dubai Municipality DM-HSD-GU38: 40-45 = high risk
HI_CEILING = 54.0                       # decision 5: "extreme danger" band (US NWS)

# --- C3: TWL zones (W/m2), OSHAD CoP 11 and Bates & Schneider 2008, Table 4 -----------
TWL_WITHDRAWAL = 115.0                  # below: no ordinary work for anyone
TWL_BUFFER = 140.0                      # 115-140: no unacclimatised person to work
TWL_DRY_BULB_MAX = 44.0                 # Miller & Bates 2007, Table 6: restricted above this
TWL_WET_BULB_MAX = 32.0
TWL_CORE_LIMIT = 38.2                   # TWL definition (Brake & Bates 2002)
TWL_SWEAT_LIMIT_KG_H = 1.2

# --- F14: documented person-to-person differences --------------------------------------
# Resting core temperature: healthy adults differ by about 0.2-0.3 C (SD) at rest.
CORE_OFFSET_SD = 0.2
CORE_OFFSET_CLIP = 0.4
# Drinking: share of sweat replaced during the shift. UAE field workers replaced only part
# of their sweat (Bates & Schneider 2008 report most arrived and stayed mildly dehydrated).
REPLACE_RANGE = (0.5, 0.9)
# Dehydration raises core temperature by about 0.1-0.23 C per 1% of body mass lost
# (Sawka et al. 2007, ACSM position stand). Through the 25 bpm/C heart-rate link this also
# gives about 3-5 bpm per 1%, the rise reported in the same position stand.
DEHYD_GAIN_RANGE = (0.10, 0.20)
# Self-pacing: UAE and Gulf workers slow down when they get hot (Miller et al. 2011; Bates &
# Schneider 2008; Qatar 2019: nobody reached 38.5 C). Each worker eases off to PACE_FACTOR of
# their work rate once their core temperature passes their own pace_start, and goes back to full
# pace when it is PACE_HYST lower. PACE_MEAN and PACE_FACTOR are tuned on 2025 TRAINING workers
# only, so the share of worker-days passing 38.0 / 38.3 / 38.5 C matches the field studies.
PACE_MEAN = 37.7           # tuned: calibrate_pacing.py (49 / 11 / 5 % vs 44 / 16 / 6 % target)
PACE_SD = 0.15
PACE_FACTOR = 0.65
PACE_HYST = 0.15


def ban_applies(date: str) -> bool:
    d = pd.Timestamp(date)
    return BAN_FIRST_DAY <= (d.month, d.day) <= BAN_LAST_DAY


def schedule_day(work_rate_wm2: float, date: str) -> pd.DataFrame:
    """06:00-18:00, 45 min work + 15 min shaded rest each hour; the legal break when it applies."""
    minute = np.arange(DAY_MINUTES)
    working = (minute % 60) < C.WORK_MINUTES_PER_HOUR
    phase = np.where(working, "work", "rest")
    if ban_applies(date):
        phase = np.where((minute >= BAN_START_MIN) & (minute < BAN_END_MIN), "break", phase)
    active = phase == "work"
    return pd.DataFrame({
        "minute": minute,
        "phase": phase,
        "met_wm2": np.where(active, work_rate_wm2, C.REST_MET_WM2),
        "tr_offset": np.where(active, C.TR_OFFSET_EXPOSED, C.TR_OFFSET_SHADE),
    })


def day_minutes(hourly: pd.DataFrame, date: str) -> pd.DataFrame:
    """Minute weather 06:00-18:00 with WBGT and Heat Index (reuses the Week 7 interpolation)."""
    w = _interp_day(hourly, date)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w["heat_index"] = np.asarray(heat_index_rothfusz(tdb=w["tdb"].to_numpy(), rh=w["rh"].to_numpy(),
                                                         round_output=False, limit_inputs=False).hi)
        w["wet_bulb"] = np.asarray(wet_bulb_tmp(tdb=w["tdb"].to_numpy(), rh=w["rh"].to_numpy()))
    return w


def _interp_day(hourly, date):
    """Same method as weather.shift_minutes, with a window long enough for 12 hours."""
    import thermofeel as tf

    start = pd.Timestamp(date) + pd.Timedelta(hours=DAY_START_HOUR)
    minutes = pd.date_range(start, periods=DAY_MINUTES, freq="min")
    h = hourly.set_index("timestamp").sort_index()
    win = h.loc[start - pd.Timedelta(hours=2): start + pd.Timedelta(hours=DAY_MINUTES / 60 + 2)]

    def interp(series, shift=pd.Timedelta(0)):
        x = ((series.index + shift) - start) / pd.Timedelta(minutes=1)
        xq = (minutes - start) / pd.Timedelta(minutes=1)
        return np.interp(np.asarray(xq, dtype=float), np.asarray(x, dtype=float), series.to_numpy(dtype=float))

    half = pd.Timedelta(minutes=-30)
    out = pd.DataFrame({
        "timestamp": minutes,
        "tdb": interp(win["temperature_2m"]), "rh": interp(win["relative_humidity_2m"]),
        "pressure_hpa": interp(win["surface_pressure"]), "wind10": interp(win["wind_speed_10m"]),
        "ssrd": interp(win["shortwave_radiation"], half), "direct": interp(win["direct_radiation"], half),
    })
    out["cossza"] = weather.cos_solar_zenith(pd.DatetimeIndex(out["timestamp"]))
    fdir = np.where(out["ssrd"] > 1, out["direct"] / out["ssrd"].clip(lower=1), 0.0)
    fdir = fdir * np.clip((out["cossza"] - 0.05) / 0.10, 0, 1)
    wbgt_k = tf.calculate_wbgt_liljegren(
        out["tdb"].to_numpy() + 273.15, out["rh"].to_numpy(), out["pressure_hpa"].to_numpy(),
        out["wind10"].to_numpy(), out["ssrd"].to_numpy(), np.clip(fdir, 0, 1), out["cossza"].to_numpy())
    out["wbgt"] = np.asarray(wbgt_k) - 273.15
    out["v"] = np.clip(out["wind10"] * 0.75, 0.2, 3.0)
    out["source"] = h["source"].iloc[0] if "source" in h else "unknown"
    return out


# --- F14 workers -----------------------------------------------------------------------
def make_workers_v5(n: int, seed: int, prefix: str = "W") -> pd.DataFrame:
    """Week 7 workers (balanced acclimatisation x work rate, body size, heart-rate fitness)
    plus the F14 traits. `spread` scales the F14 traits for the F15 stress test."""
    wk = workers.make_workers(n, seed=seed)
    wk["worker_id"] = [f"{prefix}{i + 1:03d}" for i in range(n)]
    rng = np.random.default_rng(seed + 50)
    wk["core_offset"] = np.clip(rng.normal(0, CORE_OFFSET_SD, n), -CORE_OFFSET_CLIP, CORE_OFFSET_CLIP).round(2)
    wk["replace_frac"] = rng.uniform(*REPLACE_RANGE, n).round(2)
    wk["dehyd_gain"] = rng.uniform(*DEHYD_GAIN_RANGE, n).round(3)
    wk["pace_offset"] = rng.normal(0, PACE_SD, n).round(2)    # own pace_start = PACE_MEAN + this
    return wk


def scale_spread(wk: pd.DataFrame, factor: float) -> pd.DataFrame:
    """F15 stress test: shrink (factor < 1) or widen (> 1) the F14 differences around their middle."""
    w = wk.copy()
    w["core_offset"] = (w["core_offset"] * factor).round(2)
    mid = np.mean(REPLACE_RANGE)
    w["replace_frac"] = np.clip(mid + (w["replace_frac"] - mid) * factor, 0.0, 1.0).round(2)
    mid = np.mean(DEHYD_GAIN_RANGE)
    w["dehyd_gain"] = np.clip(mid + (w["dehyd_gain"] - mid) * factor, 0.0, None).round(3)
    return w


def simulate_day(worker: pd.Series, weather_min: pd.DataFrame, date: str, pacing: bool = True,
                 pace_mean: float = PACE_MEAN, pace_factor: float = PACE_FACTOR) -> tuple[pd.DataFrame, int | None]:
    """ISO 7933 minute by minute (as Week 7), then the F14 effects on core temperature:
    resting offset + dehydration from unreplaced sweat. Danger onset uses the adjusted value."""
    sched = schedule_day(worker["work_rate_wm2"], date)
    traj = pd.concat([sched, weather_min.reset_index(drop=True)], axis=1)
    traj["tr"] = traj["tdb"] + traj["tr_offset"]
    state = dict(simulator.INITIAL_STATE)
    mass, keep = float(worker["mass_kg"]), 1 - float(worker["replace_frac"])
    offset, gain = float(worker["core_offset"]), float(worker["dehyd_gain"])
    pace_start = pace_mean + float(worker.get("pace_offset", 0.0))
    paced, sweat_cum, rows, mets = False, 0.0, [], []
    for r in traj.itertuples(index=False):
        core_now = state["t_re"] + offset + gain * 100 * sweat_cum * keep / 1000 / mass
        if pacing:
            if core_now >= pace_start:
                paced = True
            elif core_now < pace_start - PACE_HYST:
                paced = False
        met = r.met_wm2
        if pacing and paced and r.phase == "work":
            met = max(C.REST_MET_WM2, r.met_wm2 * pace_factor)
        mets.append(met)
        new, sweat_g = _phs_step_with_sweat(state, tdb=r.tdb, tr=r.tr, v=r.v, rh=r.rh, met_wm2=met, worker=worker)
        valid = all(np.isfinite(list(new.values())))
        rows.append({**new, "sweat_cum_g": sweat_g if valid else np.nan, "valid": valid, "paced": paced})
        if valid:
            state, sweat_cum = new, sweat_g
    traj["met_wm2"] = mets                          # the pace actually worked (drives heart rate too)
    traj = pd.concat([traj, pd.DataFrame(rows)], axis=1)
    # PHS carries the sweat total in its state (evap_load_wm2_min), so sweat_loss_g is already the
    # running total since 06:00, not the amount for one minute.
    sweat_cum = traj["sweat_cum_g"].ffill().fillna(0)
    loss_pct = 100 * sweat_cum * keep / 1000 / mass
    extra = offset + gain * loss_pct
    traj["t_re_iso"] = traj["t_re"]                 # the unadjusted ISO 7933 value, kept for checks
    traj["t_re"] = traj["t_re"] + extra
    traj["t_cr"] = traj["t_cr"] + extra             # heart rate follows core temperature (wearables.py)
    traj["body_loss_pct"] = loss_pct
    limit = workers.danger_limit(worker["acclimatised"])
    crossed = np.flatnonzero((traj["t_re"] >= limit).to_numpy() & (traj["phase"] != "break").to_numpy())
    onset = int(crossed[0]) if len(crossed) else None
    traj["worker_id"] = worker["worker_id"]
    traj["danger_limit"] = limit
    return traj, onset


def _phs_step_with_sweat(state, *, tdb, tr, v, rh, met_wm2, worker):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = phs(tdb=tdb, tr=tr, v=v, rh=rh, met=met_wm2 * simulator.MET_PER_WM2, clo=C.CLOTHING_CLO,
                posture="standing", duration=1, round_output=False,
                acclimatized=100 if worker["acclimatised"] else 0,
                weight=float(worker["mass_kg"]), height=float(worker["height_m"]), **state)
    return {k: float(getattr(r, k)) for k in simulator.STATE_KEYS}, float(r.sweat_loss_g)


# --- C3: Thermal Work Limit -----------------------------------------------------------------
def twl(tdb: float, tr: float, v: float, rh: float, duration: int = 240) -> float:
    """TWL = the highest metabolic rate (W/m2) a standard acclimatised worker (75 kg, 1.80 m,
    0.6 clo) can keep up without core temperature passing 38.2 C or sweat passing 1.2 kg/h.
    Computed with the ISO 7933 heat balance by bisection over 60-380 W/m2 (the TWL range).
    This follows the published TWL definition; it is not the original Brake & Bates code.
    ISO 7933 only accepts metabolic rates up to about 260 W/m2, so cooler hours top out near
    250 here; that does not change the rule, whose limits are 115 and 140 W/m2.
    Checked against published field values in tests/test_v5.py."""
    def ok(m):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = phs(tdb=tdb, tr=tr, v=float(np.clip(v, 0.1, 3.0)), rh=rh, met=m / 58.15, clo=C.CLOTHING_CLO,
                    posture="standing", duration=duration, round_output=False, acclimatized=100,
                    weight=75.0, height=1.8)
        if not np.isfinite(r.t_re):
            return False
        return r.t_re <= TWL_CORE_LIMIT and r.sweat_loss_g / 1000 / (duration / 60) <= TWL_SWEAT_LIMIT_KG_H
    lo, hi = 60.0, 380.0
    if not ok(lo):
        return lo
    if ok(hi):
        return hi
    for _ in range(9):                  # 320 / 2^9 = 0.6 W/m2 resolution
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return round(lo, 1)


def twl_hourly(hourly: pd.DataFrame) -> pd.Series:
    """TWL for every hour 05:00-19:00 (enough to interpolate the 06:00-18:00 day)."""
    h = hourly[(hourly["timestamp"].dt.hour >= 5) & (hourly["timestamp"].dt.hour <= 19)]
    v = np.clip(h["wind_speed_10m"] * 0.75, 0.2, 3.0)
    vals = [twl(t, t + C.TR_OFFSET_EXPOSED, w, r) for t, w, r in zip(h["temperature_2m"], v, h["relative_humidity_2m"])]
    return pd.Series(vals, index=h["timestamp"].to_numpy(), name="twl")


def twl_minutes(twl_h: pd.Series, timestamps: pd.Series) -> np.ndarray:
    x = (pd.DatetimeIndex(twl_h.index) - pd.Timestamp("2000-01-01")) / pd.Timedelta(minutes=1)
    xq = (pd.DatetimeIndex(timestamps) - pd.Timestamp("2000-01-01")) / pd.Timedelta(minutes=1)
    return np.interp(np.asarray(xq, float), np.asarray(x, float), twl_h.to_numpy(float))


# --- The comparators, one minute at a time -------------------------------------------------
def comparator_alerts(traj: pd.DataFrame, worker: pd.Series, twl_min: np.ndarray, wbgt_alert: np.ndarray) -> pd.DataFrame:
    """C1-C4 warnings for one shift. No one is warned during the legal break (no one works)."""
    working = (traj["phase"] != "break").to_numpy()
    acclim = bool(worker["acclimatised"])
    c2 = traj["heat_index"].to_numpy() >= HI_WARN
    twl_limit = TWL_WITHDRAWAL if acclim else TWL_BUFFER
    c3 = ((twl_min < twl_limit) | (traj["tdb"].to_numpy() > TWL_DRY_BULB_MAX)
          | (traj["wet_bulb"].to_numpy() > TWL_WET_BULB_MAX))
    out = pd.DataFrame({
        "c1_ban": np.zeros(len(traj), dtype=int),
        "c2_heat_index": c2.astype(int),
        "c3_twl": c3.astype(int),
        "c4_wbgt": np.asarray(wbgt_alert).clip(min=0).astype(int),
        "twl": twl_min,
    })
    for c in ("c2_heat_index", "c3_twl", "c4_wbgt"):
        out.loc[~working, c] = 0
    return out


def heatguard_alert(ml_fallback: np.ndarray, traj: pd.DataFrame) -> np.ndarray:
    """HG = ML with WBGT fallback (alerts.run_policies) + the Heat Index 54+ ceiling, outside the break."""
    working = (traj["phase"] != "break").to_numpy()
    ceiling = traj["heat_index"].to_numpy() >= HI_CEILING
    return ((np.asarray(ml_fallback) > 0) | ceiling).astype(int) * working
