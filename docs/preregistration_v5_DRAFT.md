# HeatGuard v0.5 pre-registration (DRAFT, not yet approved)

**Status:** draft written 16 Nov 2026, before any v0.5 result exists. When CR approves it after the
Tuesday code walkthrough, it is renamed `docs/preregistration_v5.md` and committed. `run_v5.py final`
refuses to start until that file is committed and unchanged, and it refuses to run a second time.

The frame and the five decisions are in the research frame doc (Claude Docs, "HeatGuard research
frame v2"), signed off by CR on 16 Nov 2026.

## Question

In a UAE summer, does adding HeatGuard to the rules already in force protect workers at least as
well as each rule, while giving far fewer warnings?

## What is compared (every option keeps the legal midday break)

| Code | Rule | How it warns (each minute, during work only) |
|---|---|---|
| C1 | Midday break only (federal MoHRE, 12:30–15:00, 15 June–15 September) | Never: the break is the only protection |
| C2 | Break + Dubai Heat Index rule (DM-HSD-GU38) | Heat Index ≥ 40 °C (NWS Rothfusz formula) |
| C3 | Break + Abu Dhabi TWL rule (OSHAD CoP 11; Bates & Schneider 2008) | TWL < 115 W/m², or TWL < 140 W/m² for unacclimatised workers, or dry bulb > 44 °C, or wet bulb > 32 °C |
| C4 | Break + WBGT (NIOSH RAL/REL, 60-min averages) | WBGT above the worker's limit |
| HG | Break + HeatGuard | Primary model + WBGT fallback when the heart-rate sensor fails; plus everyone warned at Heat Index ≥ 54 °C (ceiling) |

Comparators use each worker's own work rate and acclimatisation and are computed every minute
(best case for them; real sites measure a few times a day).

## Data

- Working day 06:00–18:00, 45 min work + 15 min shaded rest each hour. From 15 June to
  15 September the legal break 12:30–15:00 is in the schedule (no exposure, no warnings).
- Body: ISO 7933 (PHS) minute by minute, plus documented differences between people (F14):
  resting core temperature (SD 0.2 °C), share of sweat replaced by drinking (50–90%), and
  0.10–0.20 °C extra core temperature per 1% body mass lost (Sawka et al. 2007).
- Self-pacing (added 16 Nov after the realism check failed): each worker eases off to 65% of
  their work rate once their core temperature passes their own pace point (mean 37.7 °C, SD
  0.15), and goes back to full pace 0.15 °C lower (Miller et al. 2011; Bates & Schneider 2008).
  The two numbers were tuned on separate calibration workers (2025 weather) so that worker-days
  passing 38.0 / 38.3 / 38.5 °C match field data. Training set result: **45 / 18 / 6 %**
  vs **44 / 16 / 6 %** in Guatemalan field workers (Adgate et al. 2025). Without pacing it was
  74 / 53 / 41 %; that data set was discarded without being scored.
- Danger event: adjusted rectal temperature reaches 38.2 °C (38.5 °C if acclimatised) during work.
- Training: 200 workers × 30 random dates of summer 2025 (real ERA5 Dubai weather): 6,000 shifts,
  937 danger events.
- Locked test: 100 different workers × 40 random dates of summer **2024** (real ERA5 Dubai
  weather). Simulated before the run, never scored before it.

## Model and threshold (chosen on training workers only)

- Out-of-fold over 5 groups of training workers. Selection runs 1 and 2 tried logistic regression,
  random forest and gradient boosting; only logistic regression ever met the tuning limit, so run 3
  (the one used) has logistic regression only.
- Inputs: the Week 8 inputs plus six added on training workers only (time of day, Heat Index now
  and over 60 min, how much slower than planned the worker is moving, heart-rate and skin rise
  since the start of the shift). All use past or current readings only.
- Threshold rule: among thresholds 0.005–0.98 whose out-of-fold miss rate is at most the safest
  index rule's miss rate on the same training shifts **plus 1 point** (half of M; here 3.6%), with a median
  lead of at least 25 min, the one with the fewest false episodes, then fewest warning minutes.
  The search covers thresholds 0.10–0.60 and a warning hold of 0, 15 or 30 min (once on, the
  warning stays on that long after the last trigger, so the wearable does not flicker).
- **Chosen on training workers (run 3): logistic regression, threshold 0.32, hold 30 min.**

| Training workers, out-of-fold (937 events) | Missed | Warning min / shift | False episodes / shift |
|---|---|---|---|
| HeatGuard (0.32, hold 30) | 33 (3.5%) | 162 | 1.12 |
| C4 WBGT | 24 (2.6%) | 489 | 1.67 |
| C2 Heat Index | 44 (4.7%) | 408 | 1.56 |
| C3 TWL | 776 (83%) | 14 | 0.22 |

These are training numbers, shown so the test can be judged against them; they are not results.
- Primary model: among models that meet that rule, the one with the fewest warning minutes per shift.
- The primary model is then fitted on all training workers and scored once on the locked test set.
- Test set size: 100 workers × 40 dates = 4,000 shifts. With self-pacing there will be fewer than the
  ~1,000 events planned (training rate suggests roughly 600). M = 2 points stays as decided.

## Hypotheses and pass rules (locked test set, clean sensors unless stated)

95% intervals come from resampling **workers** (2,000 times), so many shifts of one person do not
count as independent evidence.

| | Claim | Passes if |
|---|---|---|
| H1 | HG catches more danger events than the break alone (C1) | HG − C1 sensitivity: interval above 0 |
| H2 | HG is as safe as each index rule (C2, C3, C4) | HG − rule sensitivity: lower bound ≥ −2 points (M = 2) |
| H3 | HG gives far fewer warnings | Warning minutes reduced by ≥ 50% vs each of C2–C4 (lower bound), and false episodes per shift not higher |
| H4 | HG warns as early | Median lead difference (HG − rule): lower bound ≥ −5 min |
| H5 | HG stays safe when sensors fail | H2 still holds with a 10-min heart-rate dropout and a 15-min stuck sensor |
| H6 | HG catches events the rules miss | For each rule: a = rule missed, HG caught; b = the reverse. a > b and exact one-sided McNemar p < 0.05. "Not testable" if the rule misses no event |

**Per rule:** HG beats an index rule on precision-or-safety if H3 passes against it, **or** HG is
clearly safer than it (HG − rule sensitivity: lower bound above 0).

**Verdict:** gap closed if H1 passes, H2 passes against all of C2–C4, and HG beats each of C2–C4 on
precision-or-safety; partly closed if H1 and precision-or-safety hold but H2 fails against some rule;
otherwise not closed. Whatever happens is reported as is, with the
exact counts.

## Also reported (not part of the verdict)

- F15 stress test: person-to-person differences halved and increased by half.
- F11: the whole pipeline repeated with other random seeds (smaller sizes).
- Reference check of the simulated workers against real field studies (Qatar, Guatemala, UAE).

## Points for CR to confirm at the walkthrough

1. **H1 is easy by construction.** C1 never warns, so its sensitivity is 0 and H1 only shows that
   HG catches some events. The useful number is how many events still happen under the calendar
   rule (late morning, afternoon, June and late-September days) and how many of them HG catches.
2. **Threshold rule changed, on training workers only.** The first selection run asked HeatGuard
   to catch 99% of training events. No model could (best: logistic regression missed 2.3% even at
   the lowest threshold), and on the same training shifts the rules miss too (WBGT 2.6%, Heat
   Index 4.7%, TWL 83%). So the limit is now tied to the safest rule (+1 point), which is what H2
   tests. Six inputs and a warning hold were added, because run 2 gave more alarm episodes than the
   rules (3.5 vs 1.6 per shift, warnings flickering on and off). All of this used training workers
   only; the 2024 test set is still untouched.
3. **TWL is our own implementation** of the published definition (ISO 7933 heat balance, core
   38.2 °C, sweat 1.2 kg/h). Against three published field values it is −1%, +5% and +23% off.
4. **Heat Index formula:** the US NWS (Rothfusz) formula; Dubai's guideline gives bands but not
   its formula.
5. **Change to the verdict rule (needs your OK).** The code check on fake weather showed a rule
   that almost never warns (TWL can stay above 140 W/m² all day) has ~0 warning minutes, so
   "50% fewer warnings than it" is impossible even though it misses most events. Against such a
   rule HeatGuard should win on safety instead. So: per rule, HG must pass H3 **or** be clearly
   safer. Nothing else changes.
