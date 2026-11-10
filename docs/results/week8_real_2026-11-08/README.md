# Week 8 results on REAL weather (run 8 Nov 2026, Rayen's laptop)

Commands: `python run_week8.py --run outputs/full` then `python make_figures.py --run outputs/full`,
on the v0.2 full-design simulation (792 shifts, real 2025 Dubai weather). Code: `main` after PRs #2–#4.
Copied here from `outputs/full/week8/` (which git ignores) so the whole group can use them.

| File | What |
|------|------|
| `tables.md` | Tables A–D for the paper (clean sensors, faults, lead-time differences, E5) |
| `scores_week8.csv` | One row per shift × policy × scenario × fold × heart-rate gain (source for every number) |
| `figures/` | Fig. alarm burden, lead-time difference, factor importance, heart-rate sensitivity (PNG + PDF) |

## Verdict under the pre-declared plan (`docs/analysis_plan.md`)

Main comparison (each model + fallback vs WBGT rule, clean, 30 min, gain 25, folds pooled, 26 events):
**not supported.** Every model missed more events than the WBGT rule (7, 7 and 14 of 26 vs 0), and
every lead-time interval is entirely below zero. ML cut warning time from 287 to 6–11 minutes per shift.

## Breakdown by fold (exploratory: not pre-declared, does not change the verdict)

Fold A tunes the threshold on validation (22 events) and scores test (4 events).
Fold B tunes on test (4 events) and scores validation (22 events). Gain 25, clean sensors, with fallback:

| Fold | Policy | Events | Missed | Median lead | False / shift | Warning min / shift |
|------|--------|--------|--------|-------------|---------------|---------------------|
| A | Gradient boosting | 4 | 0 | 26.0 | 0.19 | 6.0 |
| A | Logistic regression | 4 | 0 | 26.0 | 0.49 | 14.4 |
| A | Random forest | 4 | 0 | 28.5 | 0.90 | 21.5 |
| A | WBGT rule | 4 | 0 | 30.0 | 1.04 | 274.0 |
| B | Gradient boosting | 22 | 7 | 19.0 | 0.18 | 6.6 |
| B | Logistic regression | 22 | 7 | 11.5 | 0.19 | 5.6 |
| B | Random forest | 22 | 14 | 0.0 | 0.04 | 0.5 |
| B | WBGT rule | 22 | 0 | 30.0 | 0.76 | 300.7 |

Every missed event is in fold B, where the threshold was tuned on only 4 events. With a threshold tuned
on 22 events (fold A) no model missed an event, at every heart-rate gain, but fold A scores only 4 events,
so this is a lead for further work, not a result.

## Other numbers

- Danger events: train 89 (79 unacclimatised, 10 acclimatised), validation 22, test 4 (all unacclimatised).
- Thresholds (gain 25): fold A logreg 0.85, RF 0.30, GB 0.30; fold B logreg 0.95, RF 0.80, GB 0.25.
- Miss-limit check (`week8/thresholds_week8.csv`, checked by Rayen on 10 Nov 2026): the 5% miss limit could not
  be met in 2 of 18 tunings, both gradient boosting in fold A (gain 25, threshold 0.30; gain 0, threshold 0.05).
  With 22 validation events, 5% allows at most 1 miss, and every candidate threshold missed more, so the code
  used the threshold with the fewest misses (`heatguard/model.py`, `choose_threshold`). All other tunings met the limit.
  To look at in the Week 9 ML iteration.
- Sensor faults (logistic regression, Table B): fallback keeps warnings available, but with 10% / 30%
  random missing heart rate it raised false episodes to 2.65 / 12.8 per shift (0.34 without faults).
- E5: physiological inputs mattered most for logistic regression and random forest; environmental and
  physiological were about equal for gradient boosting; quality flags 0 (expected on clean sensors).
- Heart-rate gain 25 → 10 → 0: missed events did not rise steadily (gradient boosting 7 → 1 → 11),
  so threshold choice moved results more than the heart-rate link did.
- Latency (`run_pilot.py`, same day): decision per message median 11.99 ms, p95 13.95 ms, max 197.55 ms
  (3,600 messages); dropout detected after 1 min, stuck sensor after 3 min, back to ML 1 min after each fault.
