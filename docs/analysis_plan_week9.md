# Week 9 analysis plan (pre-declared, written before the Week 9 real-weather run)

**Status:** committed on 16 Nov 2026 before `run_week9.py` scored any validation, test or confirmation shift
under these rules. Model selection below used training workers only.
Week 8 (`analysis_plan.md`) stays as iteration 1, reported as declared: not supported.

## Why the question is sharpened

1. **"Earlier than WBGT" can't be shown.** In Week 8 the WBGT rule warned in 287 of 360 minutes per shift
   and reached the full 30-minute lead on all 26 events. No method can beat the cap, so a lead-time CI
   entirely above 0 was impossible by construction.
2. **WBGT fails on precision, not on catching events.** WBGT is a site-level screening index that is the
   same for every worker (Golbabaei et al. 2021 list 17 known limits). In Gulf summers it is above the limit
   most of the day while most workers show low strain (Dehghan et al. 2012). A warning that is on 80% of
   the shift cannot be obeyed, so in practice it protects no one. In the UAE the main control is a
   calendar rule (MoHRE midday break, 12:30–15:00, 15 June–15 September), which does not cover the
   06:00–12:00 shifts in this study.

## Week 9 research question

Can HeatGuard **protect workers as well as the WBGT rule** (catch every danger event with a similar warning
time) **while warning far less**, so that each warning is worth acting on?

## Primary comparison

**Logistic regression with fallback (`fallback_logreg`), Week 8 inputs** vs `wbgt_rule`; clean sensors;
30-minute horizon; heart-rate link 25 bpm/°C; folds A and B pooled (every validation and test event scored
once), and separately on the confirmation set (headline). Random forest and gradient boosting are reported
as secondary results.

### How the primary model was chosen (training workers only)

Each model was trained 5 times, each time leaving out a group of training workers, and the left-out
workers were predicted (out-of-fold). The threshold rule below was then applied to these 89 training
events. No validation, test or confirmation shift was used (`run_week9.py --oof-only`,
`outputs/full/week9_*/oof_selection.csv`).

| Inputs | Model | Missed (of 89) | Median lead | False episodes / shift | Warning min / shift |
|---|---|---|---|---|---|
| Week 8 (v1) | **Logistic regression** | **0** | **30** | **0.53** | **16.1** |
| Week 8 (v1) | Random forest | 1 | 30 | 2.52 | 69.4 |
| Week 8 (v1) | Gradient boosting | 36 | 20 | 0.63 | 14.4 |
| v1 without body mass and height (v1b) | Logistic regression | 2 | 30 | 1.32 | 51.2 |
| v1b + heart-rate/skin rise (v2) | Logistic regression | 2 | 30 | 1.29 | 53.9 |
| v2 | Random forest | 0 | 30 | 2.77 | 48.7 |

Removing body mass and height made logistic regression worse, so the "worker ID" idea (below) was **not**
adopted for the primary model: body build is real heat-storage information. Gradient boosting failed on
unseen workers whatever the inputs.

## Verdict rules (fixed now)

**Safety gate (both must hold):**
- No more missed danger events than WBGT.
- Lead time not more than 5 minutes shorter: lower end of the bootstrap 95% CI of the paired per-event lead
  difference (model minus WBGT) is at least −5 min.

**Precision win (both must hold):**
- Fewer warning minutes per shift: bootstrap 95% CI of the paired per-shift reduction (WBGT minus model)
  entirely above 0.
- No more false-alarm episodes per shift on average.

| Verdict | Condition |
|---|---|
| **Supported** | Safety gate and precision win both hold |
| **Partly supported** | Safety gate holds and warning minutes are lower, but false episodes are not |
| **Not supported** | Safety gate fails |

Also reported (not part of the verdict): warning minutes per caught event, sensor-fault scenarios, latency.

## Design changes in Week 9 (v0.4), and why

| Change | Reason (Week 8 evidence) |
|---|---|
| Threshold tuned on the training events (out-of-fold, by worker group) plus the other unseen partition: about 110 instead of 4 or 22 events | All Week 8 misses were in fold B, tuned on 4 events |
| Threshold must catch every tuning event (was ≤ 5%), with median lead ≥ 25 min; then fewest false episodes | Safety gate allows no extra misses |
| Tested, not adopted: body mass and height removed, heart-rate/skin rise added | Nearly all Week 8 misses were one worker (W018) with an unusual build. Out-of-fold on training workers this made logistic regression worse (table above) |
| Primary model fixed in advance (logistic regression, Week 8 inputs) | Picked on training workers only, so the comparison is one model, not the best of three after the fact |

## Honesty safeguard: the confirmation set

The changes above were informed by Week 8 test results, so the Week 9 fold results are **not a clean test**.
A confirmation set of **12 brand-new workers** (different random seed) on **20 summer dates the study never
used** is simulated with `make_confirmation_set.py`. Thresholds are tuned on all earlier data; the
confirmation set is scored **once**, after this plan is committed, with the same verdict rules.
**The confirmation verdict is the headline Week 9 result.**

## Reference check (simulation realism)

`reference_check.py` compares the simulated workers with published field measurements: Qatar 2019 (ILO),
Guatemala sugarcane workers (Adgate et al. 2025), UAE construction workers (Bates & Schneider 2008).
Measures: share of worker-shifts passing 38.0 / 38.3 / 38.5 °C, share of work time at 38.0–38.4 °C, mean
working heart rate, mean WBGT. Differences are reported, not hidden.
