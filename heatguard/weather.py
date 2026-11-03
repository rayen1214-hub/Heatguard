"""Part 1: Weather loader.

Input : Open-Meteo historical API (ERA5), Dubai, Jun-Sep 2025.
Output: data/weather_hourly.csv (+ the raw JSON response and its request record),
        and per-date minute tables used by the simulator.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C

HOURLY_VARS = [
    "temperature_2m", "relative_humidity_2m", "surface_pressure",
    "wind_speed_10m", "shortwave_radiation", "direct_radiation",
]
API_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_weather(out_dir: str | Path = "data") -> Path:
    """Download hourly weather once and keep the raw response for reproducibility."""
    import requests

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    params = {
        "latitude": C.LATITUDE, "longitude": C.LONGITUDE,
        "start_date": C.WEATHER_START, "end_date": C.WEATHER_END,
        "hourly": ",".join(HOURLY_VARS), "models": C.WEATHER_MODEL,
        "timezone": C.TIMEZONE, "wind_speed_unit": "ms",
    }
    resp = requests.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    raw = resp.json()
    (out / "weather_raw.json").write_text(json.dumps(raw))
    (out / "weather_request.json").write_text(json.dumps({
        "url": resp.url, "params": params,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "units": raw.get("hourly_units", {}),
    }, indent=2))
    df = pd.DataFrame(raw["hourly"]).rename(columns={"time": "timestamp"})
    df["source"] = "open-meteo-era5"
    path = out / "weather_hourly.csv"
    df.to_csv(path, index=False)
    return path


def make_test_weather(out_dir: str | Path = "data") -> Path:
    """SYNTHETIC weather for testing the code only. Never use it for results.

    It exists because some machines cannot reach Open-Meteo. Every row is
    labelled source=SYNTHETIC_TEST so it cannot be mistaken for real data.
    """
    rng = np.random.default_rng(0)
    ts = pd.date_range(C.WEATHER_START, f"{C.WEATHER_END} 23:00", freq="h")
    hour = ts.hour.to_numpy()
    day = rng.normal(0, 1.5, len(ts) // 24 + 1)[(ts.day_of_year - ts.day_of_year[0]).to_numpy()]
    # Rough Dubai-summer shape: about 33 C at 06:00 rising to about 41 C by noon
    temp = 36 + day + 6 * np.sin((hour - 8) / 24 * 2 * np.pi)
    rh = np.clip(55 - 3.0 * (temp - 33) + rng.normal(0, 5, len(ts)), 15, 95)
    sun = np.clip(np.sin((hour - 6) / 13 * np.pi), 0, None)
    df = pd.DataFrame({
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M"),
        "temperature_2m": temp.round(1), "relative_humidity_2m": rh.round(0),
        "surface_pressure": 1000.0, "wind_speed_10m": np.clip(rng.normal(3.5, 1.2, len(ts)), 0.3, None).round(1),
        "shortwave_radiation": (900 * sun).round(0), "direct_radiation": (650 * sun).round(0),
        "source": "SYNTHETIC_TEST",
    })
    path = Path(out_dir) / "weather_TEST_SYNTHETIC.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def load_hourly(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def cos_solar_zenith(ts_local: pd.DatetimeIndex, lat: float = C.LATITUDE, lon: float = C.LONGITUDE,
                     utc_offset_h: float = 4.0) -> np.ndarray:
    """Cosine of the solar zenith angle (NOAA approximation), needed by the WBGT model."""
    doy = ts_local.day_of_year.to_numpy()
    hours = ts_local.hour.to_numpy() + ts_local.minute.to_numpy() / 60
    g = 2 * np.pi / 365 * (doy - 1 + (hours - 12) / 24)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                    - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    solar_time = hours * 60 + eqt + 4 * lon - 60 * utc_offset_h
    ha = np.radians(solar_time / 4 - 180)
    phi = np.radians(lat)
    return np.clip(np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(ha), 0, 1)


def shift_minutes(hourly: pd.DataFrame, date: str) -> pd.DataFrame:
    """One-minute weather for one shift, 06:00-12:00, with WBGT.

    Hourly values are interpolated to minutes: this adds time resolution, not
    measured minute-level weather. Open-Meteo radiation is the mean of the
    preceding hour, so it is placed at the half-hour before interpolating.
    """
    import thermofeel as tf

    start = pd.Timestamp(date) + pd.Timedelta(hours=C.SHIFT_START_HOUR)
    minutes = pd.date_range(start, periods=C.SHIFT_MINUTES, freq="min")
    h = hourly.set_index("timestamp").sort_index()
    win = h.loc[start - pd.Timedelta(hours=2): start + pd.Timedelta(hours=8)]

    def interp(series: pd.Series, shift: pd.Timedelta = pd.Timedelta(0)) -> np.ndarray:
        # Work in minutes since shift start, so datetime units (ns/us/s) cannot disagree
        x = ((series.index + shift) - start) / pd.Timedelta(minutes=1)
        xq = (minutes - start) / pd.Timedelta(minutes=1)
        return np.interp(np.asarray(xq, dtype=float), np.asarray(x, dtype=float), series.to_numpy(dtype=float))

    half = pd.Timedelta(minutes=-30)
    out = pd.DataFrame({
        "timestamp": minutes,
        "tdb": interp(win["temperature_2m"]),
        "rh": interp(win["relative_humidity_2m"]),
        "pressure_hpa": interp(win["surface_pressure"]),
        "wind10": interp(win["wind_speed_10m"]),
        "ssrd": interp(win["shortwave_radiation"], half),
        "direct": interp(win["direct_radiation"], half),
    })
    out["cossza"] = cos_solar_zenith(pd.DatetimeIndex(out["timestamp"]))
    fdir = np.where(out["ssrd"] > 1, out["direct"] / out["ssrd"].clip(lower=1), 0.0)
    # Near sunrise the hour-mean direct radiation divided by a tiny cos(zenith) gives an
    # impossible beam intensity, so direct sun is faded in between cos(zenith) 0.05 and 0.15.
    fdir = fdir * np.clip((out["cossza"] - 0.05) / 0.10, 0, 1)
    wbgt_k = tf.calculate_wbgt_liljegren(
        out["tdb"].to_numpy() + 273.15, out["rh"].to_numpy(), out["pressure_hpa"].to_numpy(),
        out["wind10"].to_numpy(), out["ssrd"].to_numpy(), np.clip(fdir, 0, 1), out["cossza"].to_numpy(),
    )
    out["wbgt"] = np.asarray(wbgt_k) - 273.15
    # Air speed at body height for PHS: simple 10 m -> 2 m log-profile factor (0.75), clipped to PHS range.
    out["v"] = np.clip(out["wind10"] * 0.75, 0.2, 3.0)
    out["source"] = h["source"].iloc[0] if "source" in h else "unknown"
    return out


def sample_dates(hourly: pd.DataFrame, n: int, seed: int = C.SEED) -> list[str]:
    """Sample n distinct dates without replacement, then sort them chronologically."""
    dates = sorted(hourly["timestamp"].dt.strftime("%Y-%m-%d").unique())
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(dates, size=n, replace=False).tolist())
