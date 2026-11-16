# HeatGuard v0.5: extra checks after the locked run (17 Nov 2026)

**Everything on this page is exploratory.** These checks were made after the locked test of
16 Nov 2026 had been seen. They are reported next to the locked result and cannot change its
verdict. The plan (`docs/posthoc_plan_v5.md`) was committed before any of them was run, and every
result is reported whatever it shows. The locked run was not repeated; a guard in `posthoc_v5.py`
refuses to write into the locked folder.

Code: `posthoc_v5.py` (stages `data`, `analyse`, `f15`, `f11`, `latency`, `faultdiag`).
Files here: `analyse.json` (P1 to P5, P8), `c2b_scores.csv`, `coefficients.csv`,
`f15_050.json`, `f15_150.json`, `f11_seeds.csv`, `latency.json`, `fault_diagnostic.json`,
`fault_diagnostic.csv`.

Reproduction check first: the stored model re-scored on the locked test set gave warnings
identical to the locked scores on 4,000 of 4,000 shifts.

## Summary

| Check | Result | Does it support the locked result? |
|---|---|---|
| P1 Dubai's own chart | Chart rule misses 8 of 720, the same as HeatGuard, with 534 warning minutes against 163 | Yes for "as safe with fewer warnings". No for "safer than Dubai's rule" |
| P2 Uncatchable events | 5 of 720; without them HeatGuard misses 3 and WBGT 0 | Neutral |
| P3 Alarm burden | HeatGuard warns on 28% of working minutes (WBGT 86%); 14% of its episodes precede an event | Yes, with the caveat that most warnings are precautionary |
| P4 Inputs | No wearable: 56 missed. No weather inputs: 6. No pace and activity inputs: 42 | The wearable is needed; the benefit leans on the simulated self-pacing signal |
| P5 Field averages | Matches the calibration study; hotter and harder than the Qatar and UAE studies | Limits how far the result transfers |
| P6 Stress test | Differences ×0.5: gap closed. ×1.5: **partly closed** (23 missed against 11 for WBGT) | Only in part |
| P7 Other seeds | Gap closed in 2 of 3 small runs, partly closed in 1 | Only in part |
| P8 Sensor faults | No event lost; a fault adds a median 39 to 42 warning minutes, far more on some shifts | A defect, reported and not fixed |
| P9 Speed | Median 12 ms per decision against a 60 s budget | Yes |

In one sentence: the saving in warnings holds in every check; "as safe as WBGT" holds in the
locked test and in most checks, but not when people differ more than we assumed and not in one
of three small repeats.

## P1. Dubai's own Heat Index chart

The locked comparator C2 used the US NWS Heat Index formula. Dubai's guideline has a lookup chart
with higher values; at the five cells we checked they equal the Humidex (for example 45 at 35 °C
and 50% humidity, where the NWS formula gives 41). Rule C2b warns during work when the chart
value is 40 or more.

| On the locked test set (720 events) | Missed | Warning min / shift | False episodes / shift | Working minutes in warning |
|---|---|---|---|---|
| C2 Heat Index, NWS formula (locked) | 26 | 446 | 1.53 | 78% |
| **C2b Dubai chart rule (extra check)** | **8** | **534** | **1.50** | **93%** |
| HeatGuard (locked) | 8 | 163 | 1.08 | 28% |

HeatGuard against C2b, with the rules of the locked plan: H2 (as safe) difference 0.0 points
[−0.9, +1.0], pass. H3 (fewer warning minutes) 69.5% fewer [64.3, 74.9], pass. H4 (lead time)
pass. H6 (safer) 3 against 3 discordant events, p = 0.66, **not passed**.

**What it means.** With C2b in place of C2 the verdict would still be "gap closed", but HeatGuard
is **not safer** than Dubai's chart rule: it misses the same number of events with about
70% fewer warning minutes. The locked H6 result against the NWS formula (21 against 3) must not
be described as "safer than Dubai's rule".

## P2. Events no warning could catch

5 of the 720 events start right after the legal break, so their whole 30-minute window lies inside
the break, when warnings are off. Without them (715 events): HeatGuard missed 3, WBGT 0,
Heat Index (NWS) 21, TWL 554.

## P3. Alarm burden in plain terms

| | Working minutes in warning | Warning episodes followed by an event within 30 min | Shifts with no warning |
|---|---|---|---|
| HeatGuard | 28.5% | 14.1% | 34.4% |
| WBGT | 86.0% | 10.0% | 0.2% |
| Heat Index (NWS) | 77.9% | 10.2% | 0.5% |
| Dubai chart rule | 93.3% | 10.6% | 0.1% |
| TWL | 2.9% | 15.0% | 79.8% |

HeatGuard warns far less, but about six of seven of its warning episodes are still precautionary.

## P4. Which inputs matter

(a) Share of the locked model's standardised weights: physiological 45.9%, workload 25.4%,
weather 17.2%, personal 10.8%, time of day 0.7%, sensor quality 0. Largest single inputs:
heart-rate rise above the day's low (+2.85), pace gap (+1.92), 5-minute heart rate (+1.87),
acclimatised (−1.83), 15-minute activity (−1.49). Full list: `coefficients.csv`.

(b) Variants. Each was tuned on the training workers with the locked tuning rule (hold fixed at
30 minutes) and scored once on the test set.

| Variant | Inputs | Threshold | Missed of 720 | Warning min / shift | False episodes / shift |
|---|---|---|---|---|---|
| Full model, re-tuned as a check | 25 | 0.32 | 8 | 163 | 1.08 |
| Weather + personal only (no wearable) | 11 | 0.22 | 56 | 193 | 0.92 |
| Wearable + personal only (no weather inputs) | 19 | 0.40 | 6 | 157 | 1.07 |
| Full without the pace and activity inputs | 22 | 0.28 | 42 | 184 | 1.39 |

**What it means.** The wearable carries the safety: without it the model misses seven times as
many events. The weather inputs add nothing measurable in this simulation (the variant without
them is, if anything, slightly better; the WBGT fallback and the Heat Index ceiling still use
weather). Much of the wearable's value is the self-pacing signal: without the pace and activity
inputs the model misses 42 events. In the simulation that signal comes from the same body model
that produces the events, so only a field trial can confirm it.

Deviation from the plan: the plan said "full model without the pace input". The code removes the
pace gap and the two activity averages, because activity is the direct sign of self-pacing.

## P5. Simulated workers against published field averages

Training set, 6,000 worker-days.

| Measure | Simulation | Field | Source |
|---|---|---|---|
| Worker-days passing 38.0 / 38.3 / 38.5 °C | 45 / 18 / 6% | 44 / 16 / 6% | Krisher et al. 2025, Guatemala, 55 workers (the calibration target, so this match is by construction) |
| Work time at 38.0 to 38.4 °C | 13.9% | about 3% on average (0 to 3% construction, 8% farm) | ILO/FAME 2019, Qatar, 125 workers |
| Workers passing 38.0 °C at least once | 75.5% (30 simulated days each) | about one in three (fewer monitored days, so not like for like) | ILO/FAME 2019 |
| Mean working heart rate | 104.7 bpm (90.6 / 105.1 / 118.6 by work rate) | 87 to 91 bpm | Bates and Schneider 2008, Al Ain, 22 workers, May |
| Mean WBGT, 08:00 to 16:00 | 33.1 °C | 26 to 29 °C | Bates and Schneider 2008 |

**What it means.** The simulation matches the study it was calibrated to and runs hotter and
harder than the two Gulf studies. Part of that is the season (our data are mid-summer, the UAE
study was in May). The event rate in the field is likely lower than in our test set.

## P6. Stress test: how different people are

Same 100 test workers and 40 dates, locked model and threshold, with the person-to-person
differences scaled by 0.5 and by 1.5. Same hypotheses and verdict rule as the locked plan.

| Differences between people | Events | HeatGuard missed | WBGT missed | Heat Index (NWS) missed | HeatGuard warning min / shift | WBGT warning min / shift | Verdict |
|---|---|---|---|---|---|---|---|
| Halved (×0.5) | 616 | 3 (0.5%) | 1 | 7 | 173 | 503 | Gap closed |
| As in the locked test (×1.0) | 720 | 8 (1.1%) | 5 | 26 | 163 | 493 | Gap closed |
| Increased by half (×1.5) | 890 | 23 (2.6%) | 11 | 57 | 153 | 479 | **Partly closed** |

At ×1.5 HeatGuard is 1.3 points less sensitive than WBGT, with a 95% interval of [−3.1, −0.2]
points. The interval crosses the 2-point margin, so H2 against WBGT is **not passed** (WBGT caught
15 events that HeatGuard missed, HeatGuard caught 3 that WBGT missed). H2 against the Heat Index
(NWS) rule still passes, and there H6 passes too (41 against 7). Warning minutes stay 68% lower
than WBGT [63, 73].

**What it means.** The "as safe as WBGT" result depends on how different people are. With the
differences we documented, or smaller ones, it holds. If real workers differ by half as much
again, HeatGuard with the locked threshold misses about twice as many events as WBGT and is no
longer shown to be as safe within the agreed margin, while still warning far less. A field trial
has to measure this spread before the threshold is trusted.

## P7. Other random seeds

The whole pipeline was repeated with three other seeds at smaller size: 80 new training workers
× 20 dates (2025), tuning on those workers only, then one scoring of 50 new test workers × 20
dates (2024), 1,000 shifts each. Full table: `f11_seeds.csv`.

| Seed | Training events | Threshold chosen | Test events | HeatGuard missed | WBGT missed | Heat Index (NWS) missed | HeatGuard warning min / shift | WBGT warning min / shift | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1305 | 213 | 0.60 | 183 | 5 | 1 | 13 | 116 | 478 | **Partly closed** |
| 2305 | 224 | 0.60 | 177 | 3 | 2 | 2 | 124 | 495 | Gap closed |
| 3305 | 283 | 0.10 | 133 | 0 | 0 | 1 | 173 | 507 | Gap closed |

In seed 1305 HeatGuard was 2.2 points less sensitive than WBGT, interval [−6.0, 0.0], so H2 against
WBGT is not passed (and against the Heat Index rule the interval, [−3.3, +10.7], is too wide to
pass). In all three seeds HeatGuard gave 66 to 76% fewer warning minutes than WBGT and fewer
false alarm episodes (0.75 to 0.98 per shift against 1.62 to 1.70).

**What it means.** The saving in warnings repeats in every seed. The "as safe as WBGT" result
repeats in two of three. With under 200 events per run a difference of four missed events is
enough to fail the 2-point margin, so these small runs cannot settle it either way; they show
that the locked result is not guaranteed to repeat. The chosen threshold also moves a lot between
seeds (0.10 to 0.60), which says the tuning is not stable at this training size (1,600 shifts
against 6,000 in the locked study).

## P8. What a sensor fault leaves behind (finding F3)

The scripted faults never changed which events were caught. They did add warnings.

| On the 4,000 locked test shifts | Median extra warning minutes | Shifts gaining more than 60 min | More than 240 min | Largest |
|---|---|---|---|---|
| Heart rate missing for 10 minutes | +39 | 946 | 30 | +456 |
| Heart rate frozen for 15 minutes | +42 | 1,125 | 85 | +515 |

**Diagnostic (not in the plan; added on 17 Nov after seeing P8).** On every 8th test shift
(500 shifts) the extra minutes were split by when they happen.

| | Mean extra minutes | During the fault and its 30-minute hold | Next 15 minutes (stale readings in the trend) | Rest of the day |
|---|---|---|---|---|
| Missing for 10 minutes | 41.8 | 21.6 | 1.7 | 18.4 |
| Frozen for 15 minutes | 48.7 | 23.2 | 2.0 | 23.5 |

The rest-of-day part comes almost only from shifts where the fault lowered the stored "day's low"
heart rate by more than 1 bpm (36% of shifts for the dropout, 42% for the frozen reading):
+47.9 and +54.5 minutes on those shifts, against +1.5 and +0.9 on the others. A lower baseline
makes the "rise above the day's low" input larger for the rest of the day.

**What it means.** The fallback and hold behave as designed. The baseline is a defect: it should
ignore readings taken during a fault. It is reported and not fixed, because the model was locked
(decision D27). The fix belongs to the next iteration and needs a new locked test.

## P9. Speed

One warning decision with the v0.5 inputs (25 inputs, model, sensor check, fallback, hold, ceiling),
timed on 3,600 messages of five test shifts, Python engine, one thread, cloud build machine:
median 12.2 ms, 95th percentile 14.3 ms, largest 39.8 ms. The budget is one decision per minute
(60,000 ms).

The browser engine of the demo (`docs/demo/engine.js`) takes about 0.005 ms per message in node
on the same machine.
