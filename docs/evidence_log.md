# Evidence log

One place that points to every piece of development evidence, as asked in the tutor feedback of
29 Oct 2026 ("a complete evidence log containing the architecture version, decision history,
AI prompts and individual contributions").

| Evidence | Where | What it shows |
|----------|-------|---------------|
| Architecture versions | [`architecture_versions.md`](architecture_versions.md), diagrams in [`evidence/`](evidence/) | v1.0 → v1.1 → v1.2 → v1.3 (as built for v0.5), with what changed and why |
| Decision history | [`decisions.md`](decisions.md) | Decisions D1–D27, each with its reason and the rejected alternative |
| Plans written before the runs | [`analysis_plan.md`](analysis_plan.md) (Week 8), [`analysis_plan_week9.md`](analysis_plan_week9.md) (v0.4), [`preregistration_v5.md`](preregistration_v5.md) (v0.5, locked), [`posthoc_plan_v5.md`](posthoc_plan_v5.md) (extra checks) | Each plan was committed before the run it governs; the commit history shows the order |
| Feedback and our response | [`feedback_response.md`](feedback_response.md) | Each piece of feedback from the teaching team and what changed |
| Iterations, including failures | [`iteration_log.md`](iteration_log.md) | Every run: what we tried, what happened, what we changed |
| Version history | GitHub commit history (`main`, and branch `week9-iteration` until its pull request is merged), screenshot `evidence/13_github_commit_history.png` | v0.1 → v0.5 commits (table below) |
| Test records | [`../tests/`](../tests/), [`test_cases.md`](test_cases.md) | 10 regression tests (`test_core.py`), 17 AI-generated edge cases (`test_ai_cases.py`), 18 checks for v0.5 (`test_v5.py`, `test_posthoc.py`, `test_demo_engine.py`), manual cases (`test_manual_cases.py`); findings F1 to F3 and the AI vs manual comparison in `test_cases.md`. Run with `python -m pytest -q` |
| Results | `outputs/<run>/summary.json` (created by each run); Week 8 in [`results/week8_real_2026-11-08/`](results/week8_real_2026-11-08/); v0.5 locked run in [`results/v5_locked_2026-11-16/`](results/v5_locked_2026-11-16/); extra checks in [`results/v5_posthoc_2026-11-17/`](results/v5_posthoc_2026-11-17/) | Tables, per-shift scores and verdict of every reported run |
| Demo | [`demo/heatguard_demo.html`](demo/heatguard_demo.html), engine [`demo/engine.js`](demo/engine.js), agreement check [`demo/check_engine.js`](demo/check_engine.js) | The alert engine running in a browser page: site board, worker's wearable, sensor-fault controls |
| Usability review | [`team/guides/HeatGuard_Week8_Dashboard_Usability_Review.md`](team/guides/HeatGuard_Week8_Dashboard_Usability_Review.md) | Heuristic evaluation of the Week 8 dashboard (Faseeh, 10 Nov), and what the v0.5 demo changed in response (below) |
| Screenshots | [`evidence/`](evidence/) | Test runs, results tables, dashboard (clean, dropout, stuck, danger shift) |
| AI use and prompts | [`genai_log.md`](genai_log.md), prompt records in [`prompts/`](prompts/) | Which tool did what, how it was checked, and the prompts used |
| Individual contributions | [`../CONTRIBUTIONS.md`](../CONTRIBUTIONS.md) | Each member's own row, committed from their own GitHub account |

## Prototype versions and commits

| Commit | Date | Version | What changed |
|--------|------|---------|--------------|
| b714ac3 | 3 Nov 2026 | v0.1 | First working pipeline: all six parts, tests, dashboard, docs |
| a9c9cd6 | 3 Nov 2026 | v0.1 | README: install steps for Intel Macs |
| c3782b0 | 3 Nov 2026 | v0.1 | Logged first real-weather pilot run; fixed a pandas deprecation |
| adf803f | 3 Nov 2026 | v0.2 | Stratified worker split, fixing the empty test set |
| 0ab144b | 3 Nov 2026 | v0.2 | Iteration log: corrected full-run duration |
| 1b35743 | 3 Nov 2026 | v0.2 | Iteration log: first full real-weather results |
| 234e007 | 4 Nov 2026 | v0.2 | Contributions table: Rayen's row |
| 52f0ff4 and later | 5 Nov 2026 | v0.2 | Evidence log, architecture versions, prompt records (documentation only) |
| 7b5d445 | 8 Nov 2026 | v0.2 | Team documentation for Weeks 8–11 (PR #1) |
| 3be394f | 8 Nov 2026 | v0.2 | Week 8 analysis plan pre-declared before the real run |
| f42d520 | 8 Nov 2026 | v0.3 | Week 8 models, swap fold, sensor scenarios, intervals, sensitivity, E5, AI test cases, figures (PR #2) |
| 435ad0c | 8 Nov 2026 | v0.3 | Heart-rate plausibility check 30–220 bpm, finding F2 / decision D12 (PR #3) |
| 7a055cb | 8 Nov 2026 | v0.3 | Latency measures (PR #4) |
| 9cc22e4 | 8 Nov 2026 | v0.3 | Week 8 real-weather results, verdict, key numbers |
| badf856 | 16 Nov 2026 | v0.4 | Week 9 first attempt: plan, threshold tuned on more events, confirmation set, reference check (exploratory only) |
| e1bd5bc | 16 Nov 2026 | v0.5 | Real ERA5 Dubai weather for summers 2025 and 2024 |
| d4b0073 | 16 Nov 2026 | v0.5 | Full UAE day, four UAE rules, TWL, person-to-person differences, self-pacing, hypotheses H1 to H6 |
| 109b319 | 16 Nov 2026 | v0.5 | Model and threshold chosen on training workers |
| 323cab0 | 16 Nov 2026 | v0.5 | Pre-registration locked, before the test run |
| 93b4362 | 16 Nov 2026 | v0.5 | Results of the single locked run |
| 651e2dc | 17 Nov 2026 | v0.5 | Plan for the extra checks, before running them |
| 0b0ddca | 17 Nov 2026 | v0.5 | Live demo (browser engine, site board, sensor faults) and extra-checks script |
| 76697ae (merged 17 Nov) | 10 Nov 2026 | v0.3 | Week 8 dashboard usability review (Faseeh) |

## Latency and usability measures (proposed 5 Nov 2026, merged and measured 8 Nov 2026)

The latency code (`heatguard/latency.py`) was reviewed by Rayen and merged into `main` on 8 Nov 2026 (PR #4).
Measured on real weather on 8 Nov (full design, 3,600 messages from 10 test shifts):

| Measure | Result | Limit |
|---------|--------|-------|
| Decision latency per message | median 11.99 ms, p95 13.95 ms, max 197.55 ms | 60 s (one message per minute) |
| Heart-rate dropout detected | after 1 min | 2 min |
| Stuck sensor detected | after 3 min | 5 identical readings |
| Back to ML after the fault ends | 1 min | – |
| Alarm burden, clean sensors (Week 8) | WBGT 287 warning min / shift; ML 6–11 | lower is better |

Source: `run_pilot.py` output of 8 Nov and [`results/week8_real_2026-11-08/README.md`](results/week8_real_2026-11-08/README.md).
The heuristic usability review of the Week 8 dashboard was completed on 10 Nov 2026 (decision D11;
see "Usability review" below). Latency of the v0.5 engine is check P9 in [`results/v5_posthoc_2026-11-17/README.md`](results/v5_posthoc_2026-11-17/README.md).

- **Decision latency:** time from one wearable message arriving to the alert decision, replaying test shifts
  message by message. Reported as median, 95th percentile and maximum in milliseconds. Budget: 60 s (one message per minute).
- **Fault-detection delay:** minutes from the first faulty heart-rate reading to WBGT fallback (limit: 2 min for dropout,
  5 identical readings for a stuck sensor), and minutes from the end of the fault back to ML.
- **Usability:** alarm burden (warning minutes and false alarm episodes per shift, E3) and a heuristic evaluation of
  the dashboard against Nielsen's 10 heuristics (decision D11).

## Usability review and what changed (Week 8 dashboard → v0.5 demo)

The review used Nielsen's ten heuristics on the Week 8 Streamlit dashboard. The v0.5 demo page
was designed with its findings in hand. The demo page itself has not yet had its own review.

| Finding in the review (severity 0 to 4) | In the v0.5 demo |
|---|---|
| During a sensor fault the model's risk still showed 0%, which could be read as "safe" (3) | While the WBGT rule is deciding, the wearable shows "WBGT rule says OK" instead of a risk, the risk bar turns grey, and the reasons panel says the model's risk is not used |
| A frozen heart-rate value looked like a normal reading (3) | The value is marked "(frozen)" and shown in the warning colour |
| One message for two different faults, and no advice (2) | The banner says whether there is no reading or a frozen reading, and to check the strap and the device |
| Only one worker visible at a time (2) | Site board with 12 workers, each with state, risk and sensor status; click to open one |
| Technical labels and unexplained empty cells (2) | Plain labels ("warning minutes", "false alarms per shift"); results always come from the full test, so no empty cells |
| No quick way to reach a fault or a warning (1) | "Go to first warning" and "Go to danger event" buttons |
| WBGT limit line without a label; colour alone (2) | Every line and lane has a text label; hovering the chart lists which rules are warning |
