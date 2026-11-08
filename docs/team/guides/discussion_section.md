# Discussion section (Week 9, A8; paper Section VI)

**Owner:** Zayed · **Backup:** Jaanvi · **Due:** Thu 19 Nov · **Time:** about 3 hours

## What the markers want

B5 (5 marks): "Critically synthesises findings with prior research … limitations and future work are realistic,
specific and insightful." A8: "critically interprets limitations and implications."
The Results section says **what** happened. The Discussion says **what it means**, compared with other studies.

## Inputs

- Results draft from Fahmi (18 Nov)
- Paper Section II (related work) and its references [7]–[19]
- [wording_rules.md](wording_rules.md)

## Structure (about ¾ page; copy these headings)

**A. Answer to the research question (one paragraph).**
Does the evidence show ML warning *earlier and* with *fewer false alarms* and *no more misses*? The paper says the
RQ is supported only if all three hold together. Say plainly which held and which didn't.
With the v0.2 numbers, for example: fewer false alarms, yes; earlier, no; misses, equal; only 4 events.

**B. SQ1: which factors matter (one paragraph).** Use E5. Remember the caveat: heart rate comes from the same
simulated body as the labels, so a high physiological importance partly reflects how the simulator was built.
Link to the heart-rate sensitivity result.

**C. SQ2: lead time (one paragraph).** The paired difference and its interval. Explain why WBGT gets long lead
times (it is on most of the shift) and why that is alarm fatigue, not better warning.

**D. SQ3: sensor faults (two or three sentences).** What happened with dropout, stuck sensor and noise, and the
role of the WBGT fallback.

**E. Comparison with prior work (one paragraph, the part most groups skip).** Pick two or three:
- Sousan et al. [19] found WBGT-based risk levels **overestimated** measured strain in field workers. Our very
  high WBGT warning time is consistent with that.
- Shimazaki et al. [13] and Ojha et al. [14] report accuracy (85.2%, 93.2%). Explain why our event-based measures
  can't be compared with those numbers directly, and why event-based measures matter more to a supervisor.
- Zhao et al. [18]: no single method was best across datasets, so our result is specific to this simulator.

**F. Implications (two or three sentences).** For employers: a pilot, not adoption (Week 1 APMR framework).
For research: the open comparison and scenarios can be reused.

## Phrases that help you sound critical (not negative)

- "This suggests …, although with only N events the interval is wide."
- "A likely explanation is …; we could not test this directly because …"
- "This is consistent with [ref], who found …"
- "This differs from [ref], possibly because …"

## Done when

- [ ] Section VI draft in your own words, with at least two references to Section II studies
- [ ] Read by Fahmi (numbers) and Faseeh (no overlap with Limitations)
- [ ] Committed from your account ([how](how_to_submit.md)); GenAI log line if you used AI
