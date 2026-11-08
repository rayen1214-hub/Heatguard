# Week 8 result tables (heart-rate link 25 bpm/°C, both folds pooled)

## Table A. Clean sensors

| Method | Events | Missed | Median lead (min) | False episodes / shift | Warning min / shift |
|---|---|---|---|---|---|
| Gradient boosting | 26 | 7 | 19.5 | 0.19 | 6.28 |
| Logistic regression | 26 | 7 | 13.0 | 0.34 | 9.97 |
| Random forest | 26 | 14 | 0.0 | 0.47 | 11.0 |
| WBGT rule | 26 | 0 | 30.0 | 0.9 | 287.33 |

## Table B. Sensor faults (logistic regression; other models in summary_week8.csv)

| scenario | Method | Events | Missed | Median lead (min) | False episodes / shift | Warning min / shift |
|---|---|---|---|---|---|---|
| S5_dropout | Logistic regression + fallback | 26 | 7 | 13.0 | 0.92 | 14.99 |
| S5_dropout | Logistic regression | 26 | 7 | 13.0 | 0.34 | 9.97 |
| S5_dropout | WBGT rule | 26 | 0 | 30.0 | 0.9 | 287.33 |
| S5_missing10 | Logistic regression + fallback | 26 | 6 | 19.5 | 2.65 | 12.73 |
| S5_missing10 | Logistic regression | 26 | 7 | 13.0 | 0.36 | 9.94 |
| S5_missing10 | WBGT rule | 26 | 0 | 30.0 | 0.9 | 287.33 |
| S5_missing30 | Logistic regression + fallback | 26 | 1 | 23.0 | 12.8 | 35.27 |
| S5_missing30 | Logistic regression | 26 | 7 | 15.5 | 0.38 | 10.1 |
| S5_missing30 | WBGT rule | 26 | 0 | 30.0 | 0.9 | 287.33 |
| S6_stuck | Logistic regression + fallback | 26 | 7 | 13.0 | 0.93 | 16.84 |
| S6_stuck | Logistic regression | 26 | 7 | 13.0 | 0.34 | 9.97 |
| S6_stuck | WBGT rule | 26 | 0 | 30.0 | 0.9 | 287.33 |
| S7_noise | Logistic regression + fallback | 26 | 1 | 23.5 | 0.62 | 10.61 |
| S7_noise | Logistic regression | 26 | 1 | 23.5 | 0.62 | 10.61 |
| S7_noise | WBGT rule | 26 | 0 | 30.0 | 0.9 | 287.33 |

## Table C. Paired lead-time differences, clean sensors (minutes)

| comparison | events | Median difference | 95% low | 95% high |
|---|---|---|---|---|
| Logistic regression vs WBGT rule | 26 | -17.0 | -24.5 | -6.0 |
| Logistic regression + fallback vs WBGT rule | 26 | -17.0 | -24.5 | -6.0 |
| Random forest vs WBGT rule | 26 | -30.0 | -30.0 | -19.0 |
| Random forest + fallback vs WBGT rule | 26 | -30.0 | -30.0 | -19.0 |
| Random forest vs Logistic regression | 26 | -0.5 | -12.0 | 0.0 |
| Gradient boosting vs WBGT rule | 26 | -10.5 | -20.0 | -6.5 |
| Gradient boosting + fallback vs WBGT rule | 26 | -10.5 | -20.0 | -6.5 |
| Gradient boosting vs Logistic regression | 26 | 0.0 | 0.0 | 2.0 |

## Table D. E5 factor importance (drop in average precision)

| group | Logistic regression | Random forest | Gradient boosting |
|---|---|---|---|
| environmental | 0.24 | 0.252 | 0.379 |
| personal | 0.13 | 0.04 | 0.112 |
| physiological | 0.293 | 0.294 | 0.374 |
| quality | 0.0 | 0.0 | 0.0 |
| workload | 0.27 | 0.07 | 0.086 |
