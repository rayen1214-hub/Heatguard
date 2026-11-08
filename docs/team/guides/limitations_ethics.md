# Limitations, ethics, privacy and sustainability (Week 9, A8; paper Section VII)

**Owner:** Faseeh · **Backup:** Zayed · **Due:** Thu 19 Nov · **Time:** about 2 hours

## Why this matters

The brief requires us to "discuss security, privacy, ethics, sustainability and organisational implications",
and B5 asks for limitations that are "realistic, specific and insightful". Most of the content already exists in
the paper's Section III-G; your job is to turn it into a short, sharp section in **past tense**.

## Structure (about ½ page; copy these headings)

**A. Limitations (most important first, one or two sentences each)**
1. **Shared source for heart rate and labels.** Heart rate is generated from the same simulated body that decides
   when danger happens, so the ML task is easier than in reality. Say what the weaker-link test showed.
2. **Few events.** Only N test danger events (4 in v0.2), so intervals are wide.
3. **Model, not people.** PHS (ISO 7933) is a population model of the body; it isn't a measurement of any real
   worker and can't establish individual medical risk.
4. **Weather.** ERA5 is gridded reanalysis, not a site measurement; radiant temperature was assumed (+10 °C).
5. **No network or device.** Messages were replayed in Python without a broker (D6), so network delay, packet loss,
   battery and real sensor behaviour were not tested.
6. **Simple scenarios.** Fixed work–rest schedule; no breaks triggered by the alerts.

**B. Ethics and privacy (three or four sentences)**
No real data was collected. A real deployment would process health data, so it would need consent, restricted
access, data minimisation, retention limits, secure device communication and occupational/clinical review.
Ask the question a panel might: could a supervisor misuse heart-rate data (for example to judge productivity)?

**C. Organisational implications (two or three sentences)**
Alarm fatigue: a rule that warns three quarters of the shift is likely to be ignored. Breaks cost time; worker trust
and how alerts are acted on matter as much as the model.

**D. Sustainability (two sentences)**
Low-rate messages (one per minute), reusable open code and no unnecessary cloud. We make **no** energy or health
savings claims because nothing was measured.

**E. Future work (two or three specific items)**
Validate against measured core temperature in a supervised study with ethics approval; test with real wearables
and a broker; edge deployment with measured latency and battery (Week 6 lecture).

## Useful lecture links for the defence

Week 6 privacy by design and fail-safe design; Week 1 responsible innovation lenses; Week 4 data governance.
See the [Extensive guide](https://claude.ai/artifact/FJjrKEVS8qwHhH1h1tCE1T#s6-5).

## Done when

- [ ] Section VII draft (about ½ page) in your own words
- [ ] Checked against Zayed's Discussion so nothing is said twice
- [ ] Committed from your account ([how](how_to_submit.md)); GenAI log line if you used AI
