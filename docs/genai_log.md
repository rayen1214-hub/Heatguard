# AI assistance and team review log

The team used Claude Code and ChatGPT during implementation, analysis, documentation and interface review. This log records the assistance alongside the decisions, runs and reviews attributed to group members. Automated checks and individual review are recorded separately so that unfinished reviews remain visible.

Rayen requested and coordinated the recorded Claude Code sessions, ran the Week 7 real-weather experiments on his laptop, and signed off the v0.5 research decisions before the locked run. Faseeh ran the dashboard and captured the screenshots used in his usability review. The entries below identify where AI produced code, performed analysis or drafted text, and where member verification is still needed. Both November 19 log revisions are retained in Git.

## Session record

| Date | Team activity | AI assistance and outputs | Verification and follow-up |
|---|---|---|---|
| 3 Nov 2026 | Rayen coordinated the Week 7 prototype and ran the real-weather experiments on his laptop. | Claude Code drafted the plan and produced the v0.1/v0.2 modules, pipeline, tests, dashboard and project documentation. It also assisted with installation. | Automated tests passed. Review of each module by its assigned group owner was still pending in the original record. |
| 4 Nov 2026 | The Week 7 contribution record was updated. The two log revisions give different accounts of who checked the entry. | Claude Code prepared handover material, helped collect and caption screenshots, and drafted Rayen's contribution entry and a prompt for the teammate. | Evidence is retained in `docs/evidence/`. The contribution statement was checked by Rayen. |
| 5 Nov 2026 | The team followed up tutor feedback on latency, usability and evidence. | Claude Code prepared a group reference sheet, proposed latency code and a test on `latency-measures`, and drafted the evidence log, architecture history and decisions D10–D11. | The test passed on the branch. At that session, Rayen's review and merge were pending. Later integration is recorded in the repository history. |
| 6 Nov 2026 | The team requested Week 8 models, statistics, edge-case coverage and review guidance. The two log revisions attribute the request to different members. | Claude Code worked overnight on separate branches and produced `heatguard/week8.py`, `run_week8.py`, AI test cases and Part A of `docs/test_cases.md`. It also drafted a task map and review guide. | Branch tests passed with two known findings. Initial execution used synthetic weather for code checks. Review by Rayen was pending at that point. Manual cases remained assigned to group members. |
| 6 Nov 2026, later | Rayen requested paper preparation and reference support. | Claude Code produced `make_figures.py`, the F2 plausibility fix, a code walkthrough, Crossref/DOI checks, page estimates and draft milestone/paper sections with result placeholders. | Section owners were assigned to review and rewrite their drafts and insert verified results. Reference-owner confirmation remained pending. |
| 6 Nov 2026, evening | Revision material was requested for the course and project. The two log revisions attribute the request to different members. | Claude Code prepared two study guides and PDFs from lecture slides, the subject outline, project brief, draft paper and repository. | These were study aids. Members were asked to verify anything reused in the paper or presentation. |
| 6 Nov 2026, evening | The team prepared for Weeks 8–11 using the previously agreed task map. | Claude Code drafted `docs/team/`, the per-member guides and the empty manual-test template. | Each owner was assigned to write their section, and Rayen to review the pull request. Empty templates did not supply test evidence. |
| 10 Nov 2026 | Faseeh ran the dashboard, captured four screenshots and assessed usability findings and severity. | ChatGPT helped structure and word the review, interpret the screenshots and cross-check labels against source code. | Assistance is disclosed in `docs/team/guides/HeatGuard_Week8_Dashboard_Usability_Review.md`. |
| 16 Nov 2026 | The v0.5 research frame and decisions were signed off through the recorded research lead. See the pre-registration for the dated decision record. | Claude Code produced the frame document, `heatguard/v5.py`, `run_v5.py`, pacing calibration, tests and pre-registration, and executed the single locked evaluation. | The plan was committed at `323cab0` before scoring. The lock file records the completed test. Tests passed. Group review of the walkthrough remained pending. |
| 16 Nov 2026, night | Rayen requested a complete IEEE draft and assigned sections for member review. | Claude Code drafted all paper sections and references, with a review allocation. | Members were assigned to check numbers against the results and review/rewrite their sections. The paper declaration records AI drafting and requires confirmation of completed human review. |
| 17 Nov 2026 | Rayen requested a project review against the brief and follow-up corrections. | Claude Code reviewed the project, corrected reference authorship, a source claim, an unsupported citation and the naming of the Heat Index comparator. It produced the extra-check plan/code, browser demo and updated records. | Sources were opened for the corrections. The extra-check plan preceded execution. Browser/Python agreement was automated. Group section reviews and Rayen's pull-request review were assigned. |
| 17 Nov 2026, later | Rayen requested execution and reporting of the additional checks. | Claude Code ran the checks, prepared the result files and figures, and revised the IEEE draft around the findings. | Both checks that weakened the claim were reported. The additional fault diagnostic was identified as outside the original plan. Manual cases, member paper reviews and confirmation of the declaration were still pending in the session record. |
| 17–19 Nov 2026 | Faseeh requested external data investigation, recovery calibration, retraining and a supervisor dashboard redesign. | Codex/ChatGPT located and downloaded PROSPIE, Australian mine-worker and Dubai Airport measurements; wrote and ran the recovery calibration and exploratory retraining; implemented and checked the redesigned dashboard. It also helped explain the results and draft team messages. | Sources, method, held-out lab results and paired simulated-shift scores were saved locally. The exploratory retraining gave the same three misses in both models over 84 simulated events, with a small change in warning burden. The recovery scripts and results are included here. The separate dashboard redesign was exploratory. The submitted browser artefact is the v0.5 replay. Member review is still pending. The locked v0.5 results were retained as the primary study. |
| 19 Nov 2026 | Faseeh requested clearer wording for this log. Zayed later proposed changes to several attributions. | Codex revised the log structure and wording using the existing session record and the recorded local follow-up. | Historical attribution and pending-review status were retained. Each member should confirm the activities attributed to them before submission. |

| Submission preparation | Faseeh requested a local submission repository and review before publication. | Codex organized the existing Git history, indexed the prompt images, added and ran browser checks, verified research outputs, and drafted the submission documentation and paper edits. | Existing author dates and prompt-image bytes were preserved. The browser checks were executed by Codex using Playwright. Individual reviews and declarations are for each member to confirm. |

| 26 Nov 2026 | Faseeh shared the team lead's request to review the paper before hand-in. | Codex checked citation metadata and primary sources, compared the methods and results with the archived code, and revised the paper for clarity. | The six-page PDF was rebuilt. Team review and the SharePoint URL are pending. |

## Evidence

- Research decisions and approvals are recorded in `docs/decisions.md` and `docs/preregistration_v5.md`.
- Results and exploratory checks are in `docs/results/`.
- See the [prompt evidence index](prompts/README.md) for the retained captures and their provenance.
- Individual contribution records are in `CONTRIBUTIONS.md`.
- The paper's AI declaration should agree with the completed activities in this log.

## Member verification

Each owner records completion after personally performing the relevant check.

- [ ] Explain the assigned module and its assumptions.
- [ ] Run the relevant tests and pipeline.
- [ ] Check at least one output by hand, such as a WBGT limit or warning lead time.
- [ ] Record changes or rejected suggestions in `docs/iteration_log.md`.
- [ ] Review the assigned paper section and verify its numbers and sources.
- [ ] Confirm the individual contribution statement and the paper's AI declaration.
