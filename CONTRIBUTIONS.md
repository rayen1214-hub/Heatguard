# Contributions

Each member fills their own row and commits the change from their own GitHub account,
so the commit history matches this table.

| Member | Student no. | Part(s) owned | What I did this week | Commits / evidence |
|--------|-------------|---------------|----------------------|--------------------|
| Rayen Chaouachi | 1268806 | 3 Simulator; pipeline and integration | Led the Week 7 build: planned the prototype design and its limits; built v0.1 and v0.2 with Claude Code (declared in docs/genai_log.md); ran the pilot and full study on real 2025 weather on my laptop; found the empty test set in the first full run and had the split fixed (v0.2); took the dashboard evidence screenshots; prepared the documentation handover | Commits b714ac3 to 1b35743 (made through a Claude Code session); iteration log entries for v0.1 to v0.2; evidence/ screenshots |
| Zayed Zanober | 8417386 | Weather loader | Ran the weather fetch; checked the request data and plotted one day of temperature, humidity and WBGT for the evidence pack. | Commit: [add hash]; weather plot and request-data check |
| Faseeh Padinjarathil | 8418779 | Workers and shifts | Checked the acclimatised and unacclimatised worker balance and work rates in the generated workers file; documented the profile assumptions. | Commit: [76697ae]; workers.csv check and profile notes |
| Jaanvi Chugani | 9959877 | Wearables and faults | Reviewed the sample wearable messages and explained their format; ran the S5/S6 scenarios in the dashboard and captured screenshots. | Commit: [add hash]; message-format notes and dashboard screenshots |
| Fahmi Shafeeq | 8982569 | Warning methods; scorer and dashboard | Reviewed the warning threshold results against the 5% miss limit; captured clean-shift and dropout-shift screenshots and checked one lead-time calculation against the scoring rules. | Commit: [add hash]; threshold notes and dashboard evidence |

## Starter tasks for a member taking over a part (about 1–2 hours each)

- **Weather loader:** run `python run_pilot.py --fetch`, check `data/weather_request.json`, and plot one day of temperature, humidity and WBGT for the evidence pack.
- **Workers and shifts:** check that the balance of acclimatised/unacclimatised workers and work rates is right in `outputs/<run>/workers.csv`, and write two sentences on the profile assumptions.
- **Wearables and faults:** open `sample_messages.jsonl`, explain the message format, and run the S5/S6 scenarios in the dashboard and take screenshots.
- **Warning methods:** read `threshold_table.csv` and explain in plain words why the chosen threshold was picked, or why none met the 5% miss limit.
- **Scorer and dashboard:** take dashboard screenshots of one clean shift and one dropout shift, and check one lead-time number by hand against the scoring rules.
