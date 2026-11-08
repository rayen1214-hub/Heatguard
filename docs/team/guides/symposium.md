# Symposium: slides, demo and Q&A (Week 11, Part C)

**Slides:** Jaanvi (backup Faseeh), due Tue 1 Dec · **Demo + backup video:** Rayen (backup Fahmi), due Wed 2 Dec ·
**Q&A rehearsal:** everyone, Wed 2 Dec

Check Moodle for the exact time limit; the plan below assumes about 10 minutes plus questions.

## Slides (about 10, one idea each)

| # | Slide | Speaker | Time |
|---|-------|---------|------|
| 1 | Title, team, one-line question | Jaanvi | 0:30 |
| 2 | The problem: heat on Gulf worksites, WBGT rule warns too often | Zayed | 1:00 |
| 3 | Research question and three sub-questions | Zayed | 0:45 |
| 4 | Method: simulated workers, real weather, PHS reference, same shifts for both methods | Rayen | 1:30 |
| 5 | Architecture: wearable → messages → decision → dashboard (IoT supporting tech) | Rayen | 0:45 |
| 6 | **Live demo** (see script below) | Rayen | 2:00 |
| 7 | Results: alarm burden figure + lead-time figure | Fahmi | 1:30 |
| 8 | What it means and how it compares with prior work | Zayed | 1:00 |
| 9 | Limitations and ethics | Faseeh | 0:45 |
| 10 | Conclusion and future work | Jaanvi | 0:30 |

Slide rules: big numbers from [key_numbers.md](key_numbers.md) only, one figure per slide, no paragraph text,
every number with its event count ("4 of 4").

## Demo script (2 minutes)

1. Open the dashboard on the real run. Pick a shift marked ⚠.
2. Drag the slider to before the danger minute: point to the WBGT warning (on for most of the shift) and the ML
   warning (appears later, shorter).
3. Switch the scenario to **HR dropout**: the banner goes red "sensor offline", and the system falls back to WBGT.
4. Show the results table: warning minutes and false episodes per shift.

**Backup video:** record exactly these four steps (screen recording, 2 minutes, no editing needed). Use it if the
laptop or Wi-Fi fails. Keep it on two devices.

## Q&A drill

Every member should be able to answer these in two sentences. Full answers are in the Extensive guide,
section [P10](https://claude.ai/artifact/FJjrKEVS8qwHhH1h1tCE1T#p10-1).

1. Why simulation and not real workers?
2. If heart rate comes from the same simulated body as the labels, isn't the ML task too easy?
3. Only 4 danger events: how confident are you?
4. Why is fewer false alarms important if both methods caught everything?
5. What happens if the wearable fails?
6. How was AI used to build this, and how did you check it?
7. What would you need before a real deployment?
8. What did your part do? (each member, about your own part)

Rehearsal: one member asks, another answers, rotate. Twice through the list.

## Done when

- [ ] Slides shared with the group by 1 Dec and practised once with timing
- [ ] Demo works on the presenting laptop; backup video saved on two devices
- [ ] Everyone has answered every Q&A question out loud at least once
