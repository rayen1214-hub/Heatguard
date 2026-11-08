# Rayen: your tasks (Weeks 8–11)

Do them in this order. Tick each box when done. Backup person in brackets.

## 1. Decide the valid heart-rate range (finding F2) · Mon 9 Nov · (backup Zayed) · 20 min
- [ ] Review branch `fix-hr-plausibility` (heart rate outside 30–220 bpm is treated as missing)
- [ ] Decide merge / change range / reject, and record it as a decision in `docs/decisions.md`

## 2. Merge Week 8 code and run on real weather · Tue 10 Nov · (backup Fahmi) · 2 hours
- [ ] Merge `week8-models` into `main`, then `fix-hr-plausibility` (merge last); decide on `latency-measures`
- [ ] `python -m pytest` and note the result ("N passed, M expected failure")
- [ ] Real-weather Week 8 run; then `make_figures.py` into `outputs/full/week8/figures/`
- [ ] Fill the Week 8 table in [key_numbers.md](../guides/key_numbers.md) with each number's source file
- [ ] Share `outputs/full/week8/` with Fahmi, Zayed and Faseeh

## 3. Read Zayed's Week 8 write-up · Wed 11 Nov evening · 30 min
- [ ] Numbers match key_numbers.md; F1/F2 fixes described as actually merged

## 4. Read Jaanvi's final paper PDF · by Thu 26 Nov · 45 min
- [ ] Page count, numbers, wording rules ([checklist](../guides/paper_assembly.md))

## 5. Final package · Thu 26 Nov · (backup Fahmi) · 2 hours
- [ ] Repo `README.md` up to date (how to run, what is simulated)
- [ ] `docs/evidence_log.md`, `docs/iteration_log.md`, `docs/genai_log.md` complete; prompt records in `docs/prompts/`
- [ ] Every member's contribution row has commit hashes

## 6. Live demo and backup video · Wed 2 Dec · (backup Fahmi) · 1 hour
- [ ] Follow the [demo script](../guides/symposium.md); record the backup video; copy to two devices

## Also for you
Your own [reflection and AI sign-off](../guides/reflection_and_contribution.md) and the Q&A rehearsal ([everyone.md](everyone.md)).
