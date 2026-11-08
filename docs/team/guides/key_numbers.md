# Key numbers and where they come from

If you quote a number, it must match this table. If a number isn't here, ask Rayen before using it.
Week 8 numbers will be added after the real-weather run (Rayen, by 10 Nov).

## Study design (from `heatguard/config.py` and paper Section III)

| What | Value | Source |
|------|-------|--------|
| Location | Dubai, 25.2048 N, 55.2708 E | config.py |
| Weather | Hourly, 1 Jun – 30 Sep 2025, Open-Meteo historical API, ERA5 | config.py, `data/weather_request.json` |
| Shift | 06:00–12:00 (360 min); 45 min work + 15 min shaded rest each hour | config.py |
| Why that window | Avoids the UAE midday work ban (12:30–15:00, 15 Jun – 15 Sep) | paper ref [2] |
| Workers | 30 virtual workers; 55–95 kg; 1.60–1.90 m; acclimatised and unacclimatised balanced | config.py, workers.py |
| Work rates | 100, 165, 230 W/m² (rest 70 W/m²); clothing 0.6 clo | config.py |
| Dates | 60, sampled with seed 305 | config.py |
| Split | Workers 18/6/6, dates 36/12/12 → 648 train, 72 validation, 72 test shifts (792 total) | config.py |
| Body model | ISO 7933:2023 PHS via pythermalcomfort, run minute by minute | simulator.py |
| PHS check | Chained one-minute runs match one steady run within 0.023 °C | iteration log, test_core.py |
| Danger limit | 38.2 °C unacclimatised, 38.5 °C acclimatised (study definitions) | config.py |
| Warning horizon | 30 min (main), 15 min (secondary) | config.py |
| New warning episode | after 5 clear minutes | config.py |
| Miss limit for threshold choice | at most 5% on validation | config.py |
| Sensor fallback | HR missing 2 min → WBGT; 5 identical HR readings → "stuck" → WBGT | config.py, alerts.py |
| Simulated noise | HR SD 3 bpm, skin temperature SD 0.2 °C | config.py |

## v0.2 results (real 2025 weather, run 3 Nov 2026 on Rayen's laptop)

| What | WBGT rule | ML (logistic regression) |
|------|-----------|--------------------------|
| Danger events caught (test) | 4 of 4 | 4 of 4 |
| Median lead time | 30 min | 26 min |
| False alarm episodes per shift | 1.04 | 0.49 |
| Warning minutes per shift (of 360) | 274 | 14 |
| With 10-min HR dropout (ML + fallback) | – | 0.92 false episodes, 18 warning min |

Danger events by split: 89 train, 22 validation, 4 test. ML threshold: 0.85, chosen on validation.
Source: `docs/iteration_log.md` (3 Nov entries).

## Week 8 (to be filled after the real run)

| What | Value | Source |
|------|-------|--------|
| Danger events scored (two folds) | _pending_ | `outputs/full/week8/` |
| Median paired lead-time difference ML − WBGT, 95% interval | _pending_ | |
| Random forest / gradient boosting results | _pending_ | |
| E5 most important factor group | _pending_ | |
| Weaker heart-rate link (25 → 10 → 0 bpm/°C) | _pending_ | |
| Decision latency per message (median, p95) | _pending_ | latency-measures branch |
