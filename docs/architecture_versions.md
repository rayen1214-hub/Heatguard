# Architecture versions

Newest first. Each version says what changed and why. Diagrams are in `docs/evidence/`.

| Version | Date | What changed | Why | Diagram |
|---------|------|--------------|-----|---------|
| v1.2 (as built) | 3–5 Nov 2026 | Built as six Python parts: weather loader, worker/shift generator, PHS simulator, wearables and features, warning methods (WBGT rule, logistic regression, fallback), scorer and Streamlit dashboard. The "evaluation notebook" became a pipeline script (`run_pilot.py`) plus the dashboard. Latency measures added on 5 Nov (`heatguard/latency.py`, decision D10) | A script runs the whole study in one command, so every table can be regenerated; the dashboard is the demo. Latency added after tutor feedback of 29 Oct | Same data flow as v1.1; see README "The six parts" |
| v1.1 | 23 Oct 2026 (Week 5 milestone) | Mosquitto MQTT broker removed: MQTT-style JSON messages are replayed in time order inside Python (decision D6). One evaluation notebook instead of a separate testing tool | Keeps the build within the team's capacity while still testing late, missing and faulty readings; a broker can be added later without changing the message format | `evidence/architecture_v1.1.png` |
| v1.0 | 22 Oct 2026 (Week 5 lab) | First architecture: Open-Meteo weather + worker profiles → ISO 7933 PHS simulator (hidden ground truth) → simulated wearables over MQTT (Mosquitto) → processing → WBGT baseline vs scikit-learn models → alert engine with sensor-offline fallback → Streamlit. Evaluation E1–E5 | First design from the methodology | `evidence/architecture_v1.0.png` |

The hidden ground-truth path has stayed the same in every version: the simulator's core temperature
goes only to the scorer, never to the warning methods.
