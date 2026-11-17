# HeatGuard v0.5: plan for the extra checks after the locked run

Written and committed on 17 Nov 2026 (Dubai time) **before any of these checks was run**.
Go-ahead: Rayen, 17 Nov 2026 00:09 ("do it all right now ... make it bulletproof"), after the
marking review of the same night.

## What does not change

- The locked run of 16 Nov 2026 and its verdict (`docs/results/v5_locked_2026-11-16/`) stay exactly
  as they are. `run_v5.py final` is not run again. The lock file stays.
- The model, threshold (0.32) and hold (30 min) are the locked ones. Nothing is re-tuned on test data.
- Everything below is **exploratory**: it is reported next to the locked result, labelled as an
  extra check made after the test set had been seen, and it cannot change the locked verdict.
- Every result is reported whatever it shows, including results that weaken our claims.

## Why these checks

The marking review found points a careful reader would challenge. Each check answers one of them.

| # | Check | Question it answers | How |
|---|-------|--------------------|-----|
| P1 | Dubai chart rule (C2b) | Our C2 used the US NWS Heat Index formula. Dubai's guideline (DM-HSD-GU38) has its own lookup chart, with higher values. Does HeatGuard still hold against the chart? | The chart values match the Humidex formula at the five cells checked (35 °C/50% = 45; 38/40 = 47; 40/30 = 47; 42/25 = 48; 30/70 = 41). C2b warns during work when that value is 40 or more. Same scoring, same H2/H3/H4/H6 rules as the locked plan, on the locked test set. We also report what the verdict would be with C2b in place of C2 |
| P2 | Events nobody can catch | Some events start right after the legal break, when warnings were off | Count events whose whole 30-minute pre-event window lies inside the break. Report misses with and without them |
| P3 | Alarm burden in plain terms | "Fewer warnings" is not "few warnings" | Share of working minutes in warning; share of warning episodes followed by an event within 30 minutes |
| P4 | Which inputs matter (the old SQ1) | Does the wearable add anything over weather? Does the model lean on the self-pacing signal? | (a) Standardised coefficients of the locked model. (b) Three variants, each tuned on training workers with the locked tuning rule and then scored once on the test set: weather + personal only (no wearable); wearable + personal only (no weather); full model without the pace input |
| P5 | Simulated workers against field averages | The professor accepted published averages as the reference for realism | Training set against: Guatemala (Krisher et al. 2025), Qatar (ILO/FAME 2019), UAE (Bates & Schneider 2008). Share of worker-days passing 38.0/38.3/38.5 °C, time at 38.0-38.4 °C, mean working heart rate. All reported, matches and mismatches |
| P6 | Stress test F15 (pre-registered "also reported") | Does the result depend on how different people are? | Same 100 test workers and dates, person-to-person differences scaled by 0.5 and by 1.5; locked model and threshold; same hypotheses |
| P7 | Other random seeds F11 (pre-registered "also reported") | Is the result a lucky draw? | Whole pipeline (new training workers, tuning, new test workers) for 3 other seeds at smaller size: 80 workers x 20 dates training (2025), 50 workers x 20 dates test (2024) |
| P8 | Sensor-fault finding | On one shift a stuck sensor left HeatGuard warning all day | From the locked scores: how many shifts gain more than 60 warning minutes under each fault |
| P9 | Speed of the v0.5 engine | The 12 ms figure was measured on the Week 8 pipeline | Time per message with the v0.5 inputs, on the build machine |

## Outputs

`posthoc_v5.py` writes to `outputs/v5_posthoc/`; the summary goes to
`docs/results/v5_posthoc_2026-11-17/README.md`.
