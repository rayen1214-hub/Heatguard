# Manual test cases (Week 8, A7)

**Owner:** Jaanvi · **Backup:** Zayed · **Due:** Tue 10 Nov · **Time:** about 2 hours

## Why this matters

The Week 8 rubric (A7, 4 marks) and the final testing mark (B3, 7 marks) both ask us to
"critically compare AI-generated and manually developed tests". Claude already proposed 17 test cases
(on branch `week8-models`, file `docs/test_cases.md`, Part A). This file is the **manual** side.
The comparison only means something if the manual cases are your own.

## The one rule

**Don't open `docs/test_cases.md` Part A or `tests/test_ai_cases.py` until your cases are written.**
If you read them first, the comparison is no longer fair, and we would have to say so in the paper.

## Step 1: understand what can go wrong (30 min)

Read these, nothing else:

- The rules for scoring warnings: the "Warning-policy definitions" card P5.1 in the
  [Extensive revision guide](https://claude.ai/artifact/FJjrKEVS8qwHhH1h1tCE1T#p5-1).
- The settings in [`heatguard/config.py`](../../../heatguard/config.py) (every number has a comment).
- The sensor faults in the paper's Table III (S5 dropout, S6 stuck sensor, S7 noise).

Then ask yourself: *where could this system give a wrong answer?* Think about edges: exactly on a limit,
one minute before or after, empty input, strange values, the very start or end of a shift.

## Step 2: write 8–12 cases in plain words (45 min)

Fill the table below. Aim for at least one case in each category. Use the IDs M-01, M-02, ...

Categories: **Scoring** (lead time, misses, false alarms), **Boundary** (exactly on a limit),
**Sensor faults** (missing, stuck, impossible values), **Baseline** (WBGT limits), **Schedule/profile**
(work/rest, acclimatised vs not), **Other**.

| ID | Author | Category | Case (what situation?) | Expected behaviour (what should happen?) | Why it matters | Outcome (Pass/Fail/Not coded) |
|----|--------|----------|------------------------|-------------------------------------------|----------------|-------------------------------|
| M-01 | | | | | | |
| M-02 | | | | | | |
| M-03 | | | | | | |
| M-04 | | | | | | |
| M-05 | | | | | | |
| M-06 | | | | | | |
| M-07 | | | | | | |
| M-08 | | | | | | |
| M-09 | | | | | | |
| M-10 | | | | | | |

Example of a well-written case (format only, don't reuse it):
*"Category: Scoring. Case: warning comes on 45 minutes before danger and stays on. Expected: counted as
caught with a lead time of 30 minutes (lead time is capped at the 30-minute horizon)."*

Write down how long Step 2 took: ______ minutes. (We compare this with the AI's time in Part C.)

## Step 3: turn cases into automatic tests (30 min, optional but worth marks)

Open [`tests/test_manual_cases.py`](../../../tests/test_manual_cases.py). It has five lists
(scoring, episodes, WBGT limit, danger limit, schedule). For each case that fits one of them, copy the
`# Example` line under that list, delete the `# `, and change the values to your case.
Then run `python -m pytest tests/test_manual_cases.py -v` (or ask Rayen to run it) and fill the
Outcome column.

Cases that don't fit any list (for example sensor faults) are fine as **"Not coded"**: describe them
well and Rayen will code them or mark them as manual checks.

## Step 4: only now, compare with the AI cases (30 min)

Now open `docs/test_cases.md` on branch `week8-models` and fill **Part C** together with Zayed:

| Measure | AI-generated | Manual |
|---------|--------------|--------|
| Cases proposed | 17 | |
| Accepted / modified / rejected | | |
| Categories covered | 9 | |
| Defects found | 2 (F1, F2) | |
| Cases only one side thought of | | |
| Time taken | about 20 min | |

Also fill the **Group decision** column of Part A (Accept / Modify / Reject, one short reason each).
The proposed decisions there are the AI's suggestions; the group decides.

## Done when

- [ ] 8–12 manual cases in the table above, with your name
- [ ] Outcomes recorded (Pass / Fail / Not coded)
- [ ] Part C comparison and Part A group decisions filled
- [ ] Handed in from your own account ([how](how_to_submit.md)) and commit hash in CONTRIBUTIONS.md
