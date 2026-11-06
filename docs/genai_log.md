# GenAI and AI-assisted development log

Keep one entry per session in which a GenAI tool was used. Record what it produced, what the
group checked or changed, and what was rejected. Keep the full prompt records (exported chats)
in `docs/prompts/`.

| Date | Tool | Used for | What was produced | How it was checked / changed by the group |
|------|------|----------|-------------------|-------------------------------------------|
| 2026-11-03 | Claude (Anthropic), Claude Code | Planning the Week 7 prototype; writing the v0.1 and v0.2 code; guiding installation on Rayen's laptop | Planning doc; all code in this repository at v0.1 and v0.2 (modules, pipeline, tests, dashboard, these docs) | Automated checks in `tests/` pass. Rayen ran the real-weather runs on Rayen's own laptop. Group review of each module by its owner: *to be completed* |
| 2026-11-04 | Claude (Anthropic), Claude Code | Documentation handover for a teammate; collecting and captioning screenshots; drafting Rayen's contributions row | Handover doc; `docs/evidence/` screenshots; a prompt the teammate used with his own Claude chat | Rayen checked and committed his own row; the teammate wrote the Week 7 documentation |
| 2026-11-05 | Claude (Anthropic), Claude Code | Group cheat sheet; responding to tutor feedback of 29 Oct (latency, usability, evidence log) | Proposed `heatguard/latency.py` and a latency test (on branch `latency-measures`, not merged); `docs/evidence_log.md`, `docs/architecture_versions.md`, decisions D10–D11, `docs/prompts/` record | New test passes on the branch; Rayen to review the code before it is merged |
| 2026-11-06 (night) | Claude (Anthropic), Claude Code | Planning Weeks 8–9 at Rayen's request | Plan page (also PDF in the project folder): Week 8 checklist of what is left on top of the `week8-models` branch, how to report the paired lead-time difference with a 95% bootstrap interval, Week 9 results/discussion outline with the tables and figures needed, and an IEEE 6-page skeleton with a page budget per section; 5 new items on Rayen's task board | Planning aid only, no code changed. Owners and dates follow the draft task map; the group changes them. Page estimates are to be confirmed by pasting into the IEEE template |

## Verification checklist for AI-written code (each owner signs off their part)

- [ ] I can explain what every function in my part does and why
- [ ] I ran the tests and the pipeline myself
- [ ] I checked at least one output by hand (e.g. one WBGT limit, one lead time)
- [ ] I recorded anything I changed or rejected in `docs/iteration_log.md`
