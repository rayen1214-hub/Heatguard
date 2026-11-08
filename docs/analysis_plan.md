# Pre-declared analysis plan for the Week 8 results

Fixed by Rayen on **8 Nov 2026, before the real-weather Week 8 run**. The commit date of this
file is the evidence that these rules came first. Changing them after seeing results must be
recorded in `docs/iteration_log.md` with the reason.

## Main comparison

- **Policies:** each model with WBGT fallback (`fallback_logreg`, `fallback_random_forest`,
  `fallback_grad_boost`) against the WBGT rule (`wbgt_rule`).
- **Conditions:** clean sensors, 30-minute horizon, heart-rate gain 25 bpm/°C, both folds (A and B) pooled.
- All three models are reported. No "best" model is chosen after the results are seen.

## When the research question counts as supported

| Verdict | Condition (all on the main comparison) |
|---------|-----------------------------------------|
| **Supported** | Paired ML − WBGT lead-time 95% interval entirely above zero, **and** fewer false episodes per shift than WBGT, **and** no more missed events than WBGT (paper Section III-E) |
| **Partly supported** | Lead-time interval includes zero (no earlier warning shown), **but** fewer false episodes or warning minutes per shift, **and** no more missed events. Read as: same protection, lower alarm burden |
| **Not supported** | More missed events than WBGT, or no reduction in false episodes |

## How to read the heart-rate sensitivity runs (gain 25, 10, 0)

- If the verdict at gain 0 is the same as at gain 25: the result does not depend on the
  simulated heart-rate link (robust).
- If the verdict holds only at gain 25 (or 25 and 10): the result is conditional on wearables
  tracking core temperature this closely, and needs validation on real workers.

## Secondary results (reported, not used for the verdict)

Sensor-fault scenarios (S5–S7), the 15-minute horizon, factor importance (E5), latency and
fault-detection delay.
