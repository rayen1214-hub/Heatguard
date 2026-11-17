# Test cases: AI-generated vs manually developed (Week 8, A7)

The method (Section III) says GenAI-proposed edge cases are compared with manual cases
using an acceptance rationale, a coverage category and the test outcome. This file is that record.

**How to keep the comparison fair:** the manual cases (Part B) should be written by group
members **before reading Part A**, so they are not copied from the AI's list.

Note on the existing tests: the 9 checks in `tests/test_core.py` were also written with
Claude Code during the Week 7 build. They are AI-written, so they don't count as manual cases.

## Part A: AI-generated cases

Proposed by Claude (Claude Code) on 6 Nov 2026 from the code and the method section.
Code: `tests/test_ai_cases.py`. "Proposed decision" is the AI's suggestion. The
**group decision** column is filled in by the group, because accepting a case is the group's call.

| ID | Category | Case | Expected behaviour | Outcome | Proposed decision and rationale | Group decision |
|----|----------|------|--------------------|---------|----------------------------------|----------------|
| AI-01 | Sensor faults | Heart rate AND weather both missing all shift | Status UNAVAILABLE, treated as a warning, never "safe" | Pass | Accept: safety rule from Section III | |
| AI-02 | Sensor faults | Wearable never connects (no heart rate from minute 0) | WBGT fallback from the first minute | Pass | Accept: realistic start-of-shift failure | |
| AI-03 | Boundary | Stuck sensor: 4 vs 5 identical readings | 4 allowed, 5 flagged as stuck | Pass | Accept: checks the exact limit in `config.py` | |
| AI-04 | Robustness | Week 7 model given a shift with no heart rate | Returns a probability, doesn't crash | **Fail (finding F1)** | Accept: real defect found | |
| AI-05 | Data quality | Implausible heart rate (0 or 250 bpm) | Treated as missing, not used | Fail (F2), then pass after the fix | Accept or modify: needs a group decision on the valid range | Accepted, range 30–220 bpm (Rayen, 8 Nov 2026; decision D12) |
| AI-06 | Scoring | Warning 1 minute before onset | Counted, lead time 1 min | Pass | Accept: lower boundary of E1 | |
| AI-07 | Scoring | Warning only at the onset minute | Counted as missed | Pass | Accept: a warning must come before danger | |
| AI-08 | Scoring | Warning 31 min before onset (30-min horizon) | Missed, plus 1 false episode | Pass | Accept: upper boundary of the window | |
| AI-09 | Boundary | Two warnings exactly 5 vs 6 min apart | One episode vs two | Pass | Accept: checks EPISODE_GAP_MIN | |
| AI-10 | Scoring | Warnings in the last 30 min of an event-free shift | Not counted as false alarms (outcome unknown) | Pass | Accept: censoring rule from Section III-E | |
| AI-11 | Baseline | WBGT limit for 100 / 165 / 230 W/m² | Limit falls as work gets harder | Pass | Accept: sanity check of the NIOSH formula | |
| AI-12 | Baseline | Acclimatised vs unacclimatised limit | Acclimatised limit is higher | Pass | Accept: NIOSH REL vs RAL | |
| AI-13 | Statistics | Bootstrap interval on constant data, 1 value, 100 values | Zero width, undefined, contains median | Pass | Accept: protects the Week 8 uncertainty numbers | |
| AI-14 | Model selection | No threshold meets the 5% miss limit | Lowest-miss threshold picked and flagged | Pass | Accept: this happened in the v0.1 pilot | |
| AI-15 | Robustness | Each Week 8 model, normal and no-heart-rate shift | Valid probabilities | Pass (×3 models) | Accept | |
| AI-16 | Message stream | Duplicate or out-of-order messages | — (not implemented) | Not run | Reject: messages are replayed in order without a broker (D6), so this cannot happen in the prototype | |
| AI-17 | Leakage | Changing future readings changes past features | — (not implemented) | Not run | Reject: duplicate of `test_features_are_causal` | |

### Findings from the AI cases

- **F1: Week 7 model crashes when a shift has no heart rate yet.** Logistic regression doesn't
  accept missing values. Scenarios S5 10% and 30% missing can hit this when the very first reading
  is missing. The Week 8 models fix it with a median imputer (`heatguard/week8.py`). The Week 7
  code on `main` is unchanged. The test is marked "expected to fail" (`xfail`) so the finding stays visible.
- **F2: no plausibility check on heart rate.** A 0 or 250 bpm reading goes straight into the
  features. Suggested fix, for the group to decide: treat readings outside 30–220 bpm as missing.
  Fixed on branch `fix-hr-plausibility`: readings outside 30–220 bpm are treated as missing
  (`HR_VALID_RANGE` in `config.py`). Range 30–220 bpm confirmed by Rayen on 8 Nov 2026 (decision D12).

- **F3 (found 17 Nov 2026 while building the live demo): a sensor fault can leave extra warnings after it ends.**
  During a fault HeatGuard correctly switches to the WBGT rule. But the frozen or missing readings
  still feed two inputs, the heart-rate trend and the "rise above today's low", so after the fault
  the risk can stay raised. In the locked scores a 15-minute stuck sensor added more than 60 warning
  minutes on 1,125 of 4,000 shifts (median +42, which is the expected cost of the fallback plus the
  30-minute hold) and more than 240 minutes on 85 shifts. It never made HeatGuard miss an event.
  A diagnostic on 500 shifts (`posthoc_v5.py faultdiag`, added after the plan) split the extra
  minutes: about half fall in the fault and its hold, almost none in the stale trend window, and
  about half later in the day. The later part comes almost only from shifts where the fault lowered
  the stored "today's low" by more than 1 bpm (42% of shifts; +55 minutes there, +1 elsewhere).
  Not fixed in v0.5, because the model was already locked (decision D27). Proposed fix: do not
  update the baseline input during a fault and for 15 minutes after it.

## Part A2: Automated checks added for v0.5 (Week 9)

Written with Claude Code on 16 and 17 Nov 2026. They are regression checks for the new parts, not
edge cases proposed for the comparison in Part C.

| File | Checks | What they protect |
|------|--------|-------------------|
| `tests/test_v5.py` | 10 | The legal break applies only inside its dates; TWL is close to three published field values and falls as heat rises; each comparator follows its rule and is silent in the break; the Heat Index 54 ceiling; person-to-person differences scale as intended; sweat and body-mass loss add up over a day |
| `tests/test_posthoc.py` | 6 | The formula used for Dubai's chart reproduces five cells read from the guideline; the extra checks can never write into the locked results folder |
| `tests/test_demo_engine.py` | 2 | The browser engine gives the same risk, warning and fallback state as the Python engine on every minute of every demo shift, in three sensor scenarios (36,720 minutes); the demo page contains exactly the engine that was checked |

Whole suite on 17 Nov 2026: `python -m pytest -q` gives 46 passed, 5 skipped (the empty manual
template below), 1 expected failure (F1, kept visible on purpose).

## Part B: Manual cases (to be written by group members)

Write these **without looking at Part A**. Add your name. Aim for 8–12 cases across
the same categories. Then implement them in `tests/test_manual_cases.py`.

| ID | Author | Category | Case | Expected behaviour | Outcome | Accepted? Why |
|----|--------|----------|------|--------------------|---------|---------------|
| M-01 | | | | | | |
| M-02 | | | | | | |
| M-03 | | | | | | |

## Part C: Comparison (fill in after Part B)

| Measure | AI-generated | Manual |
|---------|--------------|--------|
| Cases proposed | 17 | |
| Accepted / modified / rejected | 15 / 0 / 2 (proposed) | |
| Categories covered | 9 (sensor faults, boundary, robustness, data quality, scoring, baseline, statistics, model selection, message stream/leakage) | |
| Defects found | 2 (F1, F2) | |
| Cases only one side thought of | | |
| Time taken | about 20 min | |
