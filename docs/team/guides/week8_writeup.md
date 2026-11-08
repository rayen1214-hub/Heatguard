# Week 8 milestone write-up: testing, validation and iteration (A7)

**Owner:** Zayed · **Backup:** Faseeh · **Due:** Thu 12 Nov (check Moodle) · **Time:** about 3 hours

## What the markers want (A7, 4 marks, High Distinction wording)

"Develops rigorous tests, benchmarks, scenarios or evaluation measures. Where appropriate, critically compares
AI-generated and manually developed tests. Records successes, failures, revisions and retesting transparently."

So the write-up needs four things: **what we tested**, **AI vs manual comparison**, **what failed and what we
changed**, and **what we re-tested**.

## Before you start

A starting draft exists: [Week 8 milestone draft](https://claude.ai/artifact/QpNnhcascGeKwmJFhkwKuh).
It was written by AI and has gaps marked **[GROUP]** and **[REAL RUN]**. Use it as a checklist of content,
then **write the submitted version in your own words**. Add a line to `docs/genai_log.md` saying you used it.

You need three inputs from others. If any is late on 11 Nov, message the owner and their backup:

| Input | From | Where it will be |
|-------|------|------------------|
| Real-weather Week 8 numbers | Rayen | [key_numbers.md](key_numbers.md), Week 8 table |
| Manual test cases and the AI vs manual table | Jaanvi | [manual_test_cases.md](manual_test_cases.md) |
| Usability review top 3 | Faseeh + Fahmi | [heuristic_review.md](heuristic_review.md) |

## Structure (copy these headings)

**1. What we tested and how (about ⅓ page)**
- Automated checks: 9 core checks in `tests/test_core.py` (they guard data leakage, causal features, the PHS
  check, the weather bug fix). Say in one line that these were written with Claude Code during the Week 7 build.
- The scenarios S1–S7 (paper Table III) and the measures E1–E5 (Table II). One sentence each is enough.
- Latency (decision D10): decision time per message and fault-detection delay. Real numbers from Rayen.
- Usability (D11): alarm burden plus the heuristic review.

**2. AI-generated vs manual test cases (about ½ page, the most important part)**
- Process: Claude proposed 17 cases from the code and the method; group members wrote manual cases
  **without seeing the AI list**; the group decided accept / modify / reject for each.
- Put the Part C comparison table in (cases, accepted/rejected, categories, defects found, time).
- Say what each side found that the other missed. Be critical: for example, did the AI cases miss anything a
  supervisor would care about? Did the manual cases cover fewer categories?
- Defects found: **F1** (the Week 7 model crashes if a shift has no heart-rate reading yet) and **F2** (no check
  for impossible heart rates such as 0 or 250 bpm). Plus any defects found by manual cases.

**3. Failures and revisions (about ⅓ page)**
Use [`docs/iteration_log.md`](../../iteration_log.md). Pick the 3–4 most important:
- First pilot: zero danger events because of a pandas date bug → fixed, regression test added.
- WBGT jumped ~4 °C at sunrise → direct sun faded in (D8).
- First full run: no danger events in validation or test → stratified split (v0.2).
- F1 and F2 from the AI tests → how each was fixed (Rayen will confirm what was merged).

**4. Re-testing and results after the fixes (about ⅓ page)**
- After the fixes: all tests pass (give the number from Rayen's run, for example "27 passed, 1 expected failure").
- Week 8 headline numbers from key_numbers.md, labelled as **preliminary**.

**5. Response to tutor feedback (2–3 lines)**
- 29 Oct feedback asked for latency, usability and an evidence log → point to D10, D11 and `docs/evidence_log.md`.

## Rules

- Only numbers from [key_numbers.md](key_numbers.md). Nothing from SYNTHETIC runs.
- Follow [wording_rules.md](wording_rules.md).
- Ask Rayen to read it before it goes to Moodle (by Wed 11 Nov evening).

## Done when

- [ ] Draft shared with the group by Wed 11 Nov
- [ ] Rayen and one other member have read it
- [ ] Submitted on Moodle; a copy committed to `docs/milestones/` from your account
- [ ] GenAI log line added if you used any AI tool
