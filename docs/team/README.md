# HeatGuard team: start here

This folder tells every member exactly what to do from Week 8 to Week 11, step by step.
You don't need to read the whole repo. Read this page (5 minutes), then open **your own task file**.

## 1. The project in five lines

- **Question:** does an ML model using wearable data warn before a worker overheats, with fewer false alarms than the WBGT rule used on worksites today?
- **How:** a simulation. 30 virtual workers on real Dubai summer mornings (Jun–Sep 2025). A standard body model (ISO 7933 PHS) tells us the exact minute each worker reaches danger. Both warning methods are scored on the same shifts.
- **Major technology:** AI/ML. **Supporting technology:** IoT (simulated wearables sending MQTT-style messages).
- **First results (v0.2):** both methods caught all 4 test danger events; ML raised far fewer alarms (14 warning minutes per shift vs 274). Only 4 events, so this is preliminary.
- **What we must never claim:** that ML is better, or that real workers are safer. Everything is simulated.

## 2. Find your task file

| Member | Your task file | Your main jobs |
|--------|----------------|----------------|
| Rayen Chaouachi | [tasks/rayen.md](tasks/rayen.md) | Merge Week 8 code, real-weather run, final package, live demo |
| Zayed Zanober | [tasks/zayed.md](tasks/zayed.md) | Week 8 milestone write-up, Discussion section |
| Faseeh Padinjarathil | [tasks/faseeh.md](tasks/faseeh.md) | Dashboard usability review, Limitations & ethics section, references check |
| Jaanvi Chugani | [tasks/jaanvi.md](tasks/jaanvi.md) | Manual test cases, paper assembly, symposium slides |
| Fahmi Shafeeq | [tasks/fahmi.md](tasks/fahmi.md) | Results tables and figures |
| Everyone | [tasks/everyone.md](tasks/everyone.md) | Contribution row, reflection, AI sign-off, symposium Q&A |

Every task has a **backup** person. If you can't do a task on time, tell the group and your backup the same day.

## 3. Timeline

Dates assume each milestone is due at the Thursday lab, with a day or two of buffer. Check Moodle for the exact times.

| Due | What | Owner | Backup | Rubric |
|-----|------|-------|--------|--------|
| Mon 9 Nov | Decide the valid heart-rate range (finding F2) | Rayen | Zayed | A7 |
| Tue 10 Nov | Merge Week 8 code and run it on real weather | Rayen | Fahmi | A7 |
| Tue 10 Nov | Manual test cases (written **without** reading the AI ones) | Jaanvi | Zayed | A7 |
| Tue 10 Nov | Dashboard usability review (Nielsen's 10 heuristics) | Faseeh | Fahmi | A7 |
| Thu 12 Nov | Week 8 milestone write-up submitted | Zayed | Faseeh | A7 |
| Wed 18 Nov | Results tables and figures | Fahmi | Rayen | A8 |
| Thu 19 Nov | Discussion section | Zayed | Jaanvi | A8 |
| Thu 19 Nov | Limitations, ethics, privacy, sustainability section | Faseeh | Zayed | A8 |
| Tue 24 Nov | Every reference checked, DOIs added | Faseeh | Jaanvi | B6 |
| Thu 26 Nov | Six-page paper assembled, page limit checked | Jaanvi | Rayen | B |
| Thu 26 Nov | Final package (README, evidence log, GenAI declaration) | Rayen | Fahmi | B4, B6 |
| Thu 26 Nov | Individual reflection and contribution statement | Everyone | – | B |
| Tue 1 Dec | Symposium slides | Jaanvi | Faseeh | C1, C6 |
| Wed 2 Dec | Live demo plus recorded backup video | Rayen | Fahmi | C2 |
| Wed 2 Dec | Q&A rehearsal | Everyone | – | C3, C4 |

## 4. Five rules that keep the project safe

1. **Don't change code on `main`.** Rayen merges all code. If you think code needs changing, write it down in your task file's "notes" and tell Rayen.
2. **Only report numbers from a REAL run.** Any run or screenshot labelled **SYNTHETIC** only tests the code. Its numbers must never appear in the paper, slides or milestone.
3. **Write in your own words.** Some starting drafts were made with AI. You must rewrite before submitting, and you must be able to explain every sentence you hand in.
4. **Declare AI use.** If you use ChatGPT, Claude, Copilot or any AI tool, add a line to [`../genai_log.md`](../genai_log.md) (date, tool, what for, what you changed). The panel will ask you in Week 11.
5. **Commit from your own GitHub account.** Marks for ownership use the commit history. If git is new to you, use the 3-minute web method in [guides/how_to_submit.md](guides/how_to_submit.md).

## 5. Where to find things

| You need | Open |
|----------|------|
| How to hand in your work | [guides/how_to_submit.md](guides/how_to_submit.md) |
| What to say and what never to say | [guides/wording_rules.md](guides/wording_rules.md) |
| Every number in the project, with its source | [guides/key_numbers.md](guides/key_numbers.md) |
| All evidence (architecture, decisions, iterations, AI use) | [`../evidence_log.md`](../evidence_log.md) |
| What went wrong and how we fixed it | [`../iteration_log.md`](../iteration_log.md) |
| Design decisions D1–D11 | [`../decisions.md`](../decisions.md) |
| How to run the code | [`../../README.md`](../../README.md) |
