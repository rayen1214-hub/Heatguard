# HeatGuard v0.5: single locked run (16 Nov 2026)

Plan: `docs/preregistration_v5.md`, approved by CR and committed (323cab0) before this run.
Run once at 18:49-18:56 UTC; lock file `FINAL_RUN_DONE.json`.

**Verdict under the pre-registered rule: GAP CLOSED.**

Locked test: 100 new workers x 40 days of the 2024 summer = 4,000 shifts, **720 danger events**.
Clean sensors, 30-minute horizon. Model: logistic regression, threshold 0.32, 30-min hold (chosen on 2025 training workers only).

| Policy (all keep the legal midday break) | Missed of 720 | Sensitivity | Median lead | False episodes / shift | Warning min / shift |
|---|---|---|---|---|---|
| C1 midday break only | 720 | 0% | - | 0.00 | 0 |
| C2 + Dubai Heat Index (>= 40) | 26 | 96.4% | 30 | 1.53 | 446 |
| C3 + Abu Dhabi TWL | 559 | 22.4% | - | 0.23 | 17 |
| C4 + WBGT (NIOSH) | 5 | 99.3% | 30 | 1.61 | 493 |
| **HG + HeatGuard** | **8** | **98.9%** | **30** | **1.08** | **163** |

| Hypothesis | vs Heat Index | vs TWL | vs WBGT |
|---|---|---|---|
| H2 safety (lower bound >= -2 pts) | +2.5 pts [+0.1, +5.4] pass | +76.5 pts pass | -0.4 pts [-1.0, 0.0] pass |
| H3 >= 50% fewer warning min, no more false episodes | -63% [57, 70] pass | not possible (TWL barely warns); clearly safer instead | -67% [62, 72] pass |
| H4 lead within 5 min | 0 min pass | +30 pass | 0 min pass |
| H6 catches what the rule misses (a vs b) | 21 vs 3, p = 0.0001 pass | 554 vs 3 pass | 0 vs 3, not passed |

H1 (vs the break alone): 98.9% of events warned vs 0% (interval 98.0 to 99.6%). Events still happen under the calendar rule:
593 on ban days (207 in the 15:00 hour, right after the break) and 127 on days outside the ban dates.

H5 (sensor faults): H2 still holds with a 10-minute heart-rate dropout and a 15-minute stuck sensor. Honest limit: the
faults are at minutes 60-75 and only 13 of 720 events start near them, so no event outcome changed; the fallback
raised HeatGuard's warning minutes to 207 (dropout) and 216 (stuck). A harder fault test (faults just before onset)
is future work.

Intervals are 95%, from resampling workers. Numbers come from simulated workers (ISO 7933 body model with documented
person-to-person differences and self-pacing) on real ERA5 Dubai weather; realism check: 45 / 18 / 6 % of training
worker-days pass 38.0 / 38.3 / 38.5 C vs 44 / 16 / 6 % in Guatemalan field workers.
