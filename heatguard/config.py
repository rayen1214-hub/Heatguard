"""Study settings in one place. Change values here, never inside the modules.

Every number below is a study assumption from Section III of the paper.
If you change one, record it in docs/iteration_log.md.
"""

# --- Location and weather (Section III-B) ---
LATITUDE = 25.2048          # Dubai
LONGITUDE = 55.2708
TIMEZONE = "Asia/Dubai"
WEATHER_START = "2025-06-01"
WEATHER_END = "2025-09-30"
WEATHER_MODEL = "era5"

# --- Shift design ---
SHIFT_START_HOUR = 6        # 06:00 local time
SHIFT_MINUTES = 360         # 06:00-12:00, avoids the 12:30-15:00 midday ban
WORK_MINUTES_PER_HOUR = 45  # then 15 min shaded rest
REST_MET_WM2 = 70           # metabolic rate while resting, W/m2
WORK_RATES_WM2 = (100, 165, 230)
CLOTHING_CLO = 0.6
TR_OFFSET_EXPOSED = 10.0    # mean radiant temp = air temp + this, during exposed work
TR_OFFSET_SHADE = 1.0       # during shaded rest

# --- Worker profiles ---
MASS_RANGE_KG = (55, 95)
HEIGHT_RANGE_M = (1.60, 1.90)

# --- Danger definition (study definition, not a clinical claim) ---
DANGER_LIMIT_UNACCLIMATISED = 38.2   # predicted rectal temperature, deg C
DANGER_LIMIT_ACCLIMATISED = 38.5

# --- Forecast horizons and warning policy ---
HORIZONS_MIN = (30, 15)     # 30 is primary
EPISODE_GAP_MIN = 5         # clear minutes needed before a new warning episode
MAX_MISS_RATE = 0.05        # operating-point constraint on validation data
HR_OFFLINE_AFTER_MIN = 2    # missing HR readings before fallback to WBGT
HR_STUCK_AFTER_MIN = 5      # identical HR readings before "stuck sensor" flag
HR_VALID_RANGE = (30, 220)  # bpm; readings outside are treated as missing (finding F2)

# --- Simulated wearable noise (engineering assumptions, not device specs) ---
HR_NOISE_SD = 3.0
SKIN_NOISE_SD = 0.2
HR_THERMAL_GAIN = 25.0      # bpm per deg C of core-temperature rise; lower it to weaken the link

# --- Experiment sizes ---
SEED = 305
PILOT = dict(n_workers=10, n_dates=10, worker_split=(6, 2, 2), date_split=(6, 2, 2))
FULL = dict(n_workers=30, n_dates=60, worker_split=(18, 6, 6), date_split=(36, 12, 12))
