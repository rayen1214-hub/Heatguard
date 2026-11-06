# GenAI and AI-assisted development log

Keep one entry per session in which a GenAI tool was used. Record what it produced, what the
group checked or changed, and what was rejected. Keep the full prompt records (exported chats)
in `docs/prompts/`.

| Date | Tool | Used for | What was produced | How it was checked / changed by the group |
|------|------|----------|-------------------|-------------------------------------------|
| 2026-11-03 | Claude (Anthropic), Claude Code | Planning the Week 7 prototype; writing the v0.1 and v0.2 code; guiding installation on Rayen's laptop | Planning doc; all code in this repository at v0.1 and v0.2 (modules, pipeline, tests, dashboard, these docs) | Automated checks in `tests/` pass. Rayen ran the real-weather runs on Rayen's own laptop. Group review of each module by its owner: *to be completed* |
| 2026-11-04 | Claude (Anthropic), Claude Code | Documentation handover for a teammate; collecting and captioning screenshots; drafting Rayen's contributions row | Handover doc; `docs/evidence/` screenshots; a prompt the teammate used with his own Claude chat | Rayen checked and committed his own row; the teammate wrote the Week 7 documentation |
| 2026-11-05 | Claude (Anthropic), Claude Code | Group cheat sheet; responding to tutor feedback of 29 Oct (latency, usability, evidence log) | Proposed `heatguard/latency.py` and a latency test (on branch `latency-measures`, not merged); `docs/evidence_log.md`, `docs/architecture_versions.md`, decisions D10–D11, `docs/prompts/` record | New test passes on the branch; Rayen to review the code before it is merged |
| 2026-11-06 (evening) | Claude (Anthropic), Claude Code | Revision material at Rayen's request | Two revision guides (extensive + essentials) covering CSIT305 Weeks 1–5 lectures and the HeatGuard project, built from the lecture slides, subject outline, project brief, paper draft and this repo; PDFs in the project folder | Study aid only, not submitted work. Content traced to the named sources; members should check anything they quote in the paper or defence |
| 2026-11-06 (evening) | Claude (Anthropic), Claude Code | Team documentation for Weeks 8–11 at Rayen's request; Weeks 6–7 added to the revision guides | `docs/team/` (start-here page, one task file per member, step-by-step guides for each Week 8–11 task, key numbers, wording rules); fill-in template `tests/test_manual_cases.py` (empty, so it changes no results) | Follows the task map agreed earlier. Each owner reads their guide and writes their submitted section in their own words; Rayen reviews the PR before merge |

## Verification checklist for AI-written code (each owner signs off their part)

- [ ] I can explain what every function in my part does and why
- [ ] I ran the tests and the pipeline myself
- [ ] I checked at least one output by hand (e.g. one WBGT limit, one lead time)
- [ ] I recorded anything I changed or rejected in `docs/iteration_log.md`
