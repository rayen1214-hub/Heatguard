# Results tables and figures (Week 9, A8; paper Section V)

**Owner:** Fahmi · **Backup:** Rayen · **Due:** Wed 18 Nov · **Time:** about 3 hours

## What you get from Rayen's run

After the real-weather Week 8 run (by 10 Nov), Rayen will share the folder `outputs/full/week8/`.
`make_figures.py` creates, in `outputs/full/week8/figures/`, four figures sized for one IEEE column, and
`tables.md` with the numbers:

1. **Alarm burden:** warning minutes and false episodes per shift for each method (answers E3).
2. **Lead-time difference:** ML minus WBGT per danger event, with the 95% interval (answers SQ2 / E1).
3. **Factor importance (E5):** which input groups the model relies on (answers SQ1).
4. **Heart-rate sensitivity:** results as the heart-rate link is weakened 25 → 10 → 0 bpm per °C.

Your job is to choose what goes in the paper and describe it accurately. You don't need to write code.

## Space budget

The paper is tight (see [paper_assembly.md](paper_assembly.md)). Results get about **one page**:
at most **one table and two figures**. Pick the ones that answer the research question.

Suggested choice:
- **Table:** E1–E3 for WBGT rule, logistic regression, random forest, gradient boosting (clean sensors), plus one
  row for ML + fallback under HR dropout (E4).
- **Figure A:** alarm burden (figure 1), the clearest picture of the main finding so far.
- **Figure B:** lead-time difference with its interval (figure 2), the direct answer to SQ2.
- Mention E5 and the sensitivity test in one sentence each, with numbers, unless they change the story.

## How to write each result (pattern)

> "[What was measured] for [which methods] on [which data]. [The number for each]. [One sentence on what is
> notable, without explaining why. The why goes in the Discussion.]"

Example of the pattern using v0.2 numbers: "On the 72 test shifts with clean sensors, both methods detected all 4
danger events. Median lead time was 30 min for the WBGT rule and 26 min for logistic regression. The WBGT rule
produced 1.04 false warning episodes and 274 warning minutes per shift; logistic regression produced 0.49 and 14."

## Checklist for every number

- [ ] It comes from the real-weather run (folder name has no `_TEST_SYNTHETIC`)
- [ ] It's in [key_numbers.md](key_numbers.md) (add it there if new, with its file as source)
- [ ] Event counts are stated next to rates ("4 of 4", not just "100%")
- [ ] Intervals are given where we have them ("median −4 min, 95% interval −12 to 0")
- [ ] Misses are reported for every method, even if zero
- [ ] Results that don't favour ML are reported just as clearly (rule D2: we never tune the experiment to get a result)

## Hand to

Zayed (Discussion) and Faseeh (Limitations) on 18 Nov, and Jaanvi for the paper on 19 Nov.

## Done when

- [ ] Section V draft (about 1 page) with one table and two figures, in your own words
- [ ] Every number ticked against the checklist
- [ ] Committed from your account ([how](how_to_submit.md))
