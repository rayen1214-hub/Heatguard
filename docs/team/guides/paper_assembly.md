# Paper assembly (Week 10, Part B)

**Owner:** Jaanvi · **Backup:** Rayen · **Due:** Thu 26 Nov · **Time:** about 4 hours

## The one rule that costs the most marks

**Six pages maximum, IEEE conference template.** Each extra page loses 10 points. Check the page count in the
final PDF, not in the editor.

## Where we are

- Sections I–IV were about **5.4 pages** on 6 Nov, so they must lose about **1.5 pages** (≈1,080 words and one
  table) to make room for V–VIII.
- Target budget (from the [Weeks 8–9 plan](https://claude.ai/artifact/B5mXNPm9wPgNM667Cc1gct)):

| Section | Target |
|---------|--------|
| Abstract + I Introduction | 0.6 page |
| II Related work | 0.9 page |
| III Method | 1.4 pages |
| IV Prototype | 0.6 page |
| V Results (1 table, 2 figures) | 1.0 page |
| VI Discussion | 0.75 page |
| VII Limitations, ethics | 0.5 page |
| VIII Conclusion | 0.1 page |
| References | ≈0.5 page |

## Inputs (with dates)

| Section | From | Due |
|---------|------|-----|
| V Results | Fahmi ([guide](results_section.md)) | 18 Nov |
| VI Discussion | Zayed ([guide](discussion_section.md)) | 19 Nov |
| VII Limitations | Faseeh ([guide](limitations_ethics.md)) | 19 Nov |
| Checked references | Faseeh ([guide](references_check.md)) | 24 Nov |

If an input is late by one day, message the owner **and** their backup.

## Step 1: cut Sections I–IV (about 2 hours)

Cut in this order, and keep a list of what you cut (it goes in the iteration log):
1. Repeated explanations. The method is described once, in III; I and IV only point to it.
2. Long lists of parameters: move to one small table or drop the ones a reader doesn't need.
3. Related work: one or two sentences per study; group similar studies.
4. Any sentence that starts "In this section we will …".
5. Fix: the paper says "Jupyter notebook" in places; our prototype is Python modules plus a Streamlit dashboard.

## Step 2: paste in V–VIII and check fit (1 hour)

- Use the IEEE template's figure and table styles. Figures one column wide.
- Every figure and table is referred to in the text ("Fig. 1 shows …").
- Write the **Conclusion** (3–4 sentences): what we did, the main finding with its caveat, what comes next.
- Rewrite the **Abstract** last (150–200 words) with the real numbers from [key_numbers.md](key_numbers.md).

## Step 3: final checks (30 min)

- [ ] PDF is 6 pages or fewer, including references
- [ ] Every number matches [key_numbers.md](key_numbers.md) and comes from a real (not SYNTHETIC) run
- [ ] Past tense for what we did; no claims from the never-say list in [wording_rules.md](wording_rules.md)
- [ ] Every reference cited, every citation listed
- [ ] Author names and student numbers correct
- [ ] GenAI declaration statement included where the brief asks for it
- [ ] Rayen has read the final PDF

## Done when

- [ ] Final PDF in the project folder and a copy committed to `docs/paper/` from your account
- [ ] Cut list added to `docs/iteration_log.md`
