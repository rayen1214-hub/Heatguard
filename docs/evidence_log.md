# Evidence log

One place that points to every piece of development evidence, as asked in the tutor feedback of
29 Oct 2026 ("a complete evidence log containing the architecture version, decision history,
AI prompts and individual contributions").

| Evidence | Where | What it shows |
|----------|-------|---------------|
| Architecture versions | [`architecture_versions.md`](architecture_versions.md), diagrams in [`evidence/`](evidence/) | v1.0 → v1.1 → v1.2 (as built), with what changed and why |
| Decision history | [`decisions.md`](decisions.md) | Decisions D1–D11, each with its reason and the rejected alternative |
| Iterations, including failures | [`iteration_log.md`](iteration_log.md) | Every run: what we tried, what happened, what we changed |
| Version history | GitHub commit history (`main`), screenshot `evidence/13_github_commit_history.png` | v0.1 → v0.2 commits (table below) |
| Test records | [`../tests/test_core.py`](../tests/test_core.py) | 10 automated checks, run with `python -m pytest -q` |
| Results and latency | `outputs/<run>/summary.json` and `latency.json` (created by each run) | E1–E3 per scenario and method; decision and fault-detection latency |
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
| (this commit) | 5 Nov 2026 | v0.3 | Latency measures, evidence log, architecture versions, prompt records |

## Latency and usability measures (added 5 Nov 2026)

- **Decision latency:** time from one wearable message arriving to the alert decision, replaying test shifts
  message by message. Reported as median, 95th percentile and maximum in milliseconds. Budget: 60 s (one message per minute).
- **Fault-detection delay:** minutes from the first faulty heart-rate reading to WBGT fallback (limit: 2 min for dropout,
  5 identical readings for a stuck sensor), and minutes from the end of the fault back to ML.
- **Usability:** alarm burden (warning minutes and false alarm episodes per shift, E3) and a heuristic evaluation of
  the dashboard against Nielsen's 10 heuristics (decision D11).
