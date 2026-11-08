# Dashboard usability review (Week 8, A7; decision D11)

**Owner:** Faseeh · **Second reviewer / backup:** Fahmi · **Due:** Tue 10 Nov · **Time:** about 1.5 hours each

## Why this matters

Our tutor asked how we measure usability (feedback of 29 Oct). Decision D11 answers it in two parts:
alarm burden (already measured: warning minutes and false episodes per shift) and a **heuristic evaluation**
of the dashboard against Jakob Nielsen's 10 usability heuristics by two group members. A heuristic review
needs no outside participants, so our "no human participants" statement stays true.

Cite it in the paper as: J. Nielsen, "Enhancing the explanatory power of usability heuristics," in *Proc. SIGCHI
Conf. Human Factors in Computing Systems (CHI '94)*, 1994, pp. 152–158, doi: 10.1145/191666.191729.
(Checked against Crossref on 6 Nov 2026.)

## Step 1: open the dashboard (10 min)

Ask Rayen for a screen-share, or run it yourself: `streamlit run dashboard.py` (needs a real run in `outputs/`).
If neither works, use the screenshots in [`../../evidence/`](../../evidence/) (files 05–11).

What the screen shows: a sidebar (choose run, sensor scenario, worker shift, and a researcher-only
"show hidden reference" box); four numbers at the top (time, heart rate, WBGT vs limit, ML risk);
a status banner (green "no warning", yellow "arrange a shaded break", red "sensor offline" or "risk unavailable");
four charts (heart rate, WBGT with its limit, ML risk, warning bars per method); a replay slider; and a
results table.

## Step 2: try these four tasks as if you were a site supervisor (20 min)

1. Find a shift with a danger event (marked ⚠ in the shift list) and find when the first warning appeared.
2. Switch to "HR dropout" and say what changed on screen and why.
3. Decide, at minute 90 of any shift, whether this worker needs a break.
4. Find the false alarms per shift for each method.

Note anything that was slow, confusing or easy to get wrong.

## Step 3: rate each heuristic (45 min)

Do this **on your own first**, then compare with the other reviewer. Severity: 0 = no problem,
1 = cosmetic, 2 = minor, 3 = major, 4 = catastrophe (must fix).

| # | Heuristic (in plain words) | What to look at on our dashboard | Problem found (or "none") | Severity 0–4 | Suggested fix |
|---|----------------------------|----------------------------------|---------------------------|--------------|---------------|
| 1 | Visibility of system status: does it show what's happening? | Banner, sensor offline message, current time | | | |
| 2 | Match with the real world: does it speak the user's language? | "WBGT", "ML risk", "episodes": would a supervisor understand? | | | |
| 3 | User control and freedom: can you undo or go back? | Replay slider, switching scenario | | | |
| 4 | Consistency and standards | Colours (red/yellow/green), units (°C, bpm, %) | | | |
| 5 | Error prevention | Could a user misread a researcher view as real? | | | |
| 6 | Recognition rather than recall | Do you need to remember things between screens? | | | |
| 7 | Flexibility and efficiency | One worker at a time: fine for 30 workers? | | | |
| 8 | Aesthetic and minimalist design | Too many charts for a quick decision? | | | |
| 9 | Help users recognise and recover from errors | Sensor offline and "unavailable" messages: clear what to do? | | | |
| 10 | Help and documentation | Is there any explanation on screen? | | | |

Reviewer: __________ · Date: __________

## Step 4: agree and summarise (15 min, both reviewers)

- Merge your two tables. Where you disagree on severity, write both numbers.
- List the top 3 problems by severity. Write one sentence each for the milestone.
- Do **not** change the dashboard code. Rayen decides whether any fix goes in before the symposium.
- Be honest: problems found are evidence of a real review, and they count for marks.

## Done when

- [ ] Two individual tables (one per reviewer), saved below or as separate files in this folder
- [ ] Merged top-3 list with severities
- [ ] Handed in from your own accounts ([how](how_to_submit.md)) and hashes in CONTRIBUTIONS.md

## Merged result

| Rank | Problem | Heuristic | Severity (Faseeh / Fahmi) | Suggested fix |
|------|---------|-----------|---------------------------|---------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
