# GenAI and AI-assisted development log

Keep one entry per session in which a GenAI tool was used. Record what it produced, what the
group checked or changed, and what was rejected. Keep the full prompt records (exported chats)
in `docs/prompts/`.

| Date | Tool | Used for | What was produced | How it was checked / changed by the group |
|------|------|----------|-------------------|-------------------------------------------|
| 2026-11-03 | Claude (Anthropic), Claude Code | Planning the Week 7 prototype; writing the v0.1 and v0.2 code; guiding installation on Rayen's laptop | Planning doc; all code in this repository at v0.1 and v0.2 (modules, pipeline, tests, dashboard, these docs) | Automated checks in `tests/` pass. Rayen ran the real-weather runs on Rayen's own laptop. Group review of each module by its owner: *to be completed* |
| 2026-11-04 | Claude (Anthropic), Claude Code | Documentation handover for a teammate; collecting and captioning screenshots; drafting Rayen's contributions row | Handover doc; `docs/evidence/` screenshots; a prompt the teammate used with his own Claude chat | Rayen checked and committed his own row; the teammate wrote the Week 7 documentation |
| 2026-11-05 | Claude (Anthropic), Claude Code | Group cheat sheet; responding to tutor feedback of 29 Oct (latency, usability, evidence log) | Proposed `heatguard/latency.py` and a latency test (on branch `latency-measures`, not merged); `docs/evidence_log.md`, `docs/architecture_versions.md`, decisions D10–D11, `docs/prompts/` record | New test passes on the branch; Rayen to review the code before it is merged |
| 2026-11-06 | Claude (Anthropic), Claude Code | Working independently overnight at Rayen's request, on branches only: Week 8 models and statistics; AI-generated edge-case tests; review guide; draft task map | `heatguard/week8.py`, `run_week8.py`, `tests/test_ai_cases.py`, `docs/test_cases.md` (Part A only; Part B is for manual cases by group members) | Tests pass on the branch (2 marked as known findings); checked on synthetic weather only. Rayen to review before merging |

## Verification checklist for AI-written code (each owner signs off their part)

- [ ] I can explain what every function in my part does and why
- [ ] I ran the tests and the pipeline myself
- [ ] I checked at least one output by hand (e.g. one WBGT limit, one lead time)
- [ ] I recorded anything I changed or rejected in `docs/iteration_log.md`
