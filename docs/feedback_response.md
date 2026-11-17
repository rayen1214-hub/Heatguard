# Feedback and what we did about it

One row per piece of feedback from the teaching team, with the change it led to and where the
evidence is. Newest first.

| Date | Feedback | What we did | Where to see it |
|------|----------|-------------|-----------------|
| 17 Nov 2026 | (Professor, answer passed on by Rayen) Because raw data of real workers could not be found publicly, published averages from field studies may be used as references. Not preferred, but accepted | The simulated workers stay, and are compared openly with field averages from Guatemala (Krisher et al. 2025), Qatar (ILO and FAME Laboratory 2019) and the UAE (Bates and Schneider 2008). Matches and mismatches are both reported: the share of worker-days passing 38.0 / 38.3 / 38.5 °C matches the Guatemala study, but the simulated workers spend more time above 38 °C than the Qatar workers and have a higher mean heart rate than the UAE workers | Decision D25; `results/v5_posthoc_2026-11-17/README.md` (check P5); paper Sections IV and VIII |
| 12 Nov 2026 | (Professor, Week 8 demo) The artefact has to work and close the research gap. "Not supported" is not enough | We did not keep tuning until Week 8 passed. We changed the question to the one the evidence pointed at (as safe as the rules in use, with far fewer warnings), wrote the plan down, and tested once on new workers in a new year. Result: gap closed, with the parts that did not pass reported | Decisions D14 to D23; `preregistration_v5.md`; `results/v5_locked_2026-11-16/`; iteration log 12 to 16 Nov |
| 12 Nov 2026 | (Professor, Week 8 demo) All data should be real | The weather is real (ERA5 reanalysis for Dubai, summers 2025 and 2024). No public data set of outdoor workers with heart rate and core temperature exists: every study we found shares data on request only. We asked how to proceed and received the answer of 17 Nov above | `data/weather_hourly.csv`, `data/weather_hourly_2024.csv`; decision D25 |
| 12 Nov 2026 | (Professor, Week 8 demo) It is not clear who receives the alarm | The worker's wearable shows STOP and rest; the supervisor sees a site board with every worker's state. The demo now shows both views | Decision D13; `docs/demo/heatguard_demo.html` |
| 29 Oct 2026 | (Tutor) Add explicit latency and usability measures | Latency: time per wearable message from arrival to decision, and minutes until a sensor fault triggers the fallback. Usability: alarm burden (warning minutes and false alarm episodes per shift) plus a heuristic review of the interface against Nielsen's ten heuristics by group members | Decisions D10 and D11; `evidence_log.md`; `results/v5_posthoc_2026-11-17/README.md` (check P9) |
| 29 Oct 2026 | (Tutor) Keep a complete evidence log: architecture version, decision history, AI prompts, individual contributions | One index page that points to each of them | `evidence_log.md` |
| 19 Oct 2026 | (Professor) State the sub-questions as research questions; report the median lead time; show which factors contribute (SQ1); give a DOI for every reference | Sub-questions rewritten; median lead time is a reported measure (E1); the contribution of each group of inputs is reported, and for v0.5 also what happens when the wearable inputs or the weather inputs are removed; DOIs checked against Crossref | Paper Sections I and III; `results/v5_posthoc_2026-11-17/README.md` (check P4); paper reference list |

## What we could not do

- **Real worker data.** Not available publicly (see 12 and 17 Nov). The result is about simulated
  workers and is stated that way everywhere.
- **A test with real users.** The method says no human participants are involved, so usability is
  measured by alarm burden and a heuristic review, not by a user study.
