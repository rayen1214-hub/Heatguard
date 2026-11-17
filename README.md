# HeatGuard prototype (v0.5)

CSIT305 Research and Innovation Project, University of Wollongong in Dubai, Autumn 2026.

HeatGuard is an early warning for heat strain in outdoor workers. It reads a worker's wearable
(heart rate, skin temperature, movement) and the weather once a minute, estimates the risk that
the worker reaches a dangerous core temperature within 30 minutes, and tells that worker to stop
and rest. If the heart-rate sensor fails, it falls back to the WBGT rule, so it never shows "safe"
when it cannot see.

This repository is a **simulation testbed**, not a field trial. Virtual workers (ISO 7933
Predicted Heat Strain model, with documented differences between people and self-pacing) work
full UAE summer days on real ERA5 Dubai weather. HeatGuard is compared with the rules a UAE site
can already use. The true core temperature goes only to the scorer, never to any warning method.

## Result in one table (locked test, run once on 16 Nov 2026)

100 new workers × 40 days of summer 2024 = 4,000 shifts, 720 danger events. Every option keeps
the legal midday break. The plan was committed before the run (`docs/preregistration_v5.md`).

| Option | Missed of 720 | Warning minutes per shift | False alarm episodes per shift |
|---|---|---|---|
| Midday break only | 720 | 0 | 0.00 |
| + Heat Index ≥ 40 (US NWS formula) | 26 | 446 | 1.53 |
| + Thermal Work Limit | 559 | 17 | 0.23 |
| + WBGT (NIOSH limits) | 5 | 493 | 1.61 |
| **+ HeatGuard** | **8** | **163** | **1.08** |

Verdict under the rule fixed beforehand: **gap closed**. HeatGuard is as safe as each rule
(within the 2-point margin) with about two thirds fewer warning minutes than WBGT or Heat Index.
It is **not** safer than WBGT (8 missed against 5). Full tables: `docs/results/v5_locked_2026-11-16/`.
Extra checks made after the locked run, including Dubai's own Heat Index chart, a stress test and
other random seeds: `docs/results/v5_posthoc_2026-11-17/`. They are labelled exploratory and do
not change the verdict. What they showed, in short: the saving in warning minutes held in every
check (66 to 76% below WBGT). Against Dubai's own chart HeatGuard is as safe, not safer (8 missed
each). "As safe as WBGT" did **not** hold when people were made half again as different (23 missed
against 11) or in one of three smaller repeats with other seeds (5 against 1).

## What this prototype does not show

- It does not show that real workers would be safer. The workers are simulated; the simulation
  is compared with published field averages, and it runs hotter and harder than the UAE field
  study (see the extra checks).
- Heart rate, skin temperature and movement are generated from the same simulated body that
  produces the danger events, so the model's best inputs are partly circular.
- There is no physical device and no message broker. Faults are injected into the messages.
- After a sensor fault HeatGuard can keep warning longer than it should (a lowered heart-rate
  baseline). This defect is reported and not fixed, because the model was locked.

See Section VIII of the paper and `docs/decisions.md`.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                    # all automated checks
python run_v5.py smoke                                 # code check on synthetic weather (numbers mean nothing)
```

The v0.5 study itself has three stages. Each one only reads what the stage before wrote.

```bash
python run_v5.py data      # simulate 6,000 training shifts (2025) and 4,000 test shifts (2024): about 50 min on 4 cores
python run_v5.py select    # choose the model and threshold on training workers only
python run_v5.py final     # the single locked test run
```

`final` refuses to start unless `docs/preregistration_v5.md` is committed, and refuses to run a
second time (lock file `outputs/v5/FINAL_RUN_DONE.json`). The reported run is the one of
16 Nov 2026. To reproduce the numbers on another machine, use a fresh clone.

```bash
python posthoc_v5.py data      # extra simulations for the stress test and other seeds (about 80 min)
python posthoc_v5.py analyse   # Dubai chart rule, uncatchable events, alarm burden, inputs, field averages
python posthoc_v5.py f15       # stress test
python posthoc_v5.py f11       # other random seeds
python posthoc_v5.py latency   # time per message
python posthoc_v5.py faultdiag # where the extra warnings after a sensor fault come from (added after the plan)
```

**Intel Mac (or a "Failed building wheel for llvmlite" error):** use Anaconda instead of `venv`:

```bash
conda create -n heatguard -c conda-forge python=3.12 numba scipy pyarrow -y
conda activate heatguard
pip install pythermalcomfort==4.8.0 thermofeel==2.3.0 pandas scikit-learn requests streamlit pytest
```

## The demo

`docs/demo/heatguard_demo.html` is one self-contained page. Open it in any browser.

- The HeatGuard alert engine runs **in the page** (`docs/demo/engine.js`, a JavaScript port of the
  Python engine). Every simulated wearable message goes through the same inputs, model, sensor
  check, fallback, 30-minute hold and Heat Index ceiling.
- A site board shows 12 test workers on one day; a detail view shows one worker minute by minute
  against the WBGT, Heat Index and TWL rules.
- You can switch a heart-rate sensor off or freeze it at any time and watch the fallback.

```bash
python make_demo_data.py          # rebuild the page from outputs/v5 (asserts each shift matches the locked scores)
node docs/demo/check_engine.js    # proves the browser engine and the Python engine agree, minute by minute
```

The Week 8 Streamlit dashboard (`streamlit run dashboard.py`) still works on Week 8 outputs. It
is kept as the earlier iteration and is not the v0.5 demo.

## The parts

| # | Part | File |
|---|------|------|
| 1 | Weather loader (ERA5 through Open-Meteo), WBGT and Heat Index | `heatguard/weather.py` |
| 2 | Worker and shift generator; person-to-person differences | `heatguard/workers.py`, `heatguard/v5.py` |
| 3 | Simulator ("the body"): ISO 7933 minute by minute, hydration, self-pacing | `heatguard/simulator.py`, `heatguard/v5.py` |
| 4 | Wearable messages, sensor faults, model inputs | `heatguard/wearables.py`, `heatguard/features.py` |
| 5 | Warning methods: UAE rules (break, Heat Index, TWL, WBGT), model, fallback | `heatguard/baseline.py`, `heatguard/v5.py`, `heatguard/week8.py`, `heatguard/alerts.py` |
| 6 | Scorer, hypotheses H1 to H6, verdict | `heatguard/evaluate.py`, `run_v5.py` |
| 7 | Demo: browser engine and page | `docs/demo/`, `make_demo_data.py` |

All study settings are in `heatguard/config.py` and at the top of `heatguard/v5.py` and
`run_v5.py`. Who worked on what: `CONTRIBUTIONS.md`.

## Earlier iterations (kept, with their results)

| Version | Script | Outcome |
|---|---|---|
| v0.1 to v0.2 (Week 7) | `run_pilot.py` | First pipeline; empty test set found and fixed |
| v0.3 (Week 8) | `run_week8.py`, `make_figures.py` | Declared verdict: not supported (26 events) |
| v0.4 (Week 9, morning of 16 Nov) | `run_week9.py`, `make_confirmation_set.py`, `reference_check.py` | Exploratory only; superseded by v0.5 |
| v0.5 (Week 9) | `run_v5.py`, `calibrate_pacing.py`, `posthoc_v5.py` | Gap closed (table above) |

Every one of these, including the failures, is in `docs/iteration_log.md`.

## Evidence

- `docs/evidence_log.md`: start here; it points to everything below
- `docs/feedback_response.md`: each piece of feedback and what we changed
- `docs/preregistration_v5.md` and `docs/posthoc_plan_v5.md`: plans committed before the runs
- `docs/results/`: results of every reported run
- `docs/paper/`: the paper (LaTeX source, PDF, figures); `python make_paper_figures.py` redraws the figures
- `docs/architecture_versions.md`: architecture v1.0 to v1.3
- `docs/iteration_log.md`: what failed, what changed, and why
- `docs/decisions.md`: design decisions and rejected alternatives
- `docs/test_cases.md`: automated tests, AI-generated and manual test cases
- `docs/genai_log.md`: GenAI use and prompt records
- `CONTRIBUTIONS.md`: who did what
