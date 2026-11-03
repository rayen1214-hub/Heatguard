# GenAI and AI-assisted development log

Keep one entry per session in which a GenAI tool was used. Record what it produced, what the
group checked or changed, and what was rejected. Keep the full prompt records (exported chats)
in `docs/prompts/`.

| Date | Tool | Used for | What was produced | How it was checked / changed by the group |
|------|------|----------|-------------------|-------------------------------------------|
| 2026-11-03 | Claude (Anthropic), Claude Code | Planning the Week 7 prototype; writing the v0.1 code | Artifact walkthrough doc; all files in this repository at v0.1 (modules, pipeline, tests, dashboard, these docs) | Automated checks in `tests/` pass. Group review of each module by its owner: *to be completed* |

## Verification checklist for AI-written code (each owner signs off their part)

- [ ] I can explain what every function in my part does and why
- [ ] I ran the tests and the pipeline myself
- [ ] I checked at least one output by hand (e.g. one WBGT limit, one lead time)
- [ ] I recorded anything I changed or rejected in `docs/iteration_log.md`
