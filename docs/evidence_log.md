# Evidence log

One place that points to every piece of development evidence, as asked in the tutor feedback of
29 Oct 2026 ("a complete evidence log containing the architecture version, decision history,
AI prompts and individual contributions").

| Evidence | Where | What it shows |
|----------|-------|---------------|
| Architecture versions | [`architecture_versions.md`](architecture_versions.md), diagrams in [`evidence/`](evidence/) | v1.0 → v1.1 → v1.2 (as built), with what changed and why |
| Decision history | [`decisions.md`](decisions.md) | Decisions D1–D12, each with its reason and the rejected alternative |
| Pre-declared analysis plan | [`analysis_plan.md`](analysis_plan.md) | Week 8 main comparison and verdict rules, committed before the real run (8 Nov), plus the outcome |
| Iterations, including failures | [`iteration_log.md`](iteration_log.md) | Every run: what we tried, what happened, what we changed |
| Version history | GitHub commit history (`main`), screenshot `evidence/13_github_commit_history.png` | v0.1 → v0.2 commits (table below) |
| Test records | [`../tests/`](../tests/), [`test_cases.md`](test_cases.md) | 10 regression tests (`test_core.py`), 17 AI-generated edge cases (`test_ai_cases.py`), manual cases (`test_manual_cases.py`); AI vs manual comparison in `test_cases.md`. Run with `python -m pytest -q` |
| Results | `outputs/<run>/summary.json` (created by each run); Week 8 real-weather results in [`results/week8_real_2026-11-08/`](results/week8_real_2026-11-08/) | E1–E3 per scenario and method; Week 8 tables, figures, per-shift scores and latency |
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
The heuristic usability review of the dashboard is in progress (decision D11).

- **Decision latency:** time from one wearable message arriving to the alert decision, replaying test shifts
  message by message. Reported as median, 95th percentile and maximum in milliseconds. Budget: 60 s (one message per minute).
- **Fault-detection delay:** minutes from the first faulty heart-rate reading to WBGT fallback (limit: 2 min for dropout,
  5 identical readings for a stuck sensor), and minutes from the end of the fault back to ML.
- **Usability:** alarm burden (warning minutes and false alarm episodes per shift, E3) and a heuristic evaluation of
  the dashboard against Nielsen's 10 heuristics (decision D11).
