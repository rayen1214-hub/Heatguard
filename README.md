# HeatGuard prototype (v0.1)

CSIT305 Research and Innovation Project, UOW Dubai, Autumn 2026.

HeatGuard is a **simulation testbed**. It creates virtual outdoor workers on real Dubai summer
mornings (Jun–Sep 2025), uses the ISO 7933 Predicted Heat Strain (PHS) model as the hidden
"body", and compares two ways of warning before a worker reaches the danger limit:

- the **WBGT rule** (NIOSH alert/exposure limits), used on worksites today, and
- an **ML model** that only sees simulated wearable messages and weather.

Both methods run on exactly the same shifts. The true core temperature goes only to the scorer.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                    # 8 checks; all must pass
python run_pilot.py --fetch                            # downloads real weather, runs the pilot (~30 s)
streamlit run dashboard.py                             # opens the demo in the browser
```

**Intel Mac (or a "Failed building wheel for llvmlite" error):** recent numba has no ready-made
package for Intel Macs, so use Anaconda instead of `venv`:

```bash
conda create -n heatguard -c conda-forge python=3.12 numba scipy -y
conda activate heatguard
pip install pythermalcomfort==4.8.0 thermofeel==2.3.0 pandas scikit-learn requests streamlit pytest
```

Use `--design full` for the full study size (30 workers × 60 dates, about 7 minutes).
`--test-weather` uses **synthetic** weather to check the code when Open-Meteo is unreachable.
Its numbers must never be reported. Every output folder from it is labelled `_TEST_SYNTHETIC`.

## The six parts

| # | Part | File | Owner |
|---|------|------|-------|
| 1 | Weather loader | `heatguard/weather.py` | TBD |
| 2 | Worker and shift generator | `heatguard/workers.py` | TBD |
| 3 | Simulator ("the body") | `heatguard/simulator.py` | Rayen Chaouachi |
| 4 | Wearable messages and faults | `heatguard/wearables.py`, `heatguard/features.py` | TBD |
| 5 | Warning methods | `heatguard/baseline.py`, `heatguard/model.py`, `heatguard/alerts.py` | TBD |
| 6 | Scorer and dashboard | `heatguard/evaluate.py`, `dashboard.py` | TBD |
| – | Pipeline and integration | `run_pilot.py`, `heatguard/config.py` | Rayen Chaouachi |

Each part has a header comment that states its input and output, so one part can be changed
without touching the others. All study settings live in `heatguard/config.py`.

## Outputs (`outputs/<run>/`)

| File | Contents |
|------|----------|
| `workers.csv`, `split.csv` | Virtual workers and the train/validation/test split |
| `trajectories.csv.gz` | Minute-by-minute simulated body and weather (the hidden reference) |
| `shift_index.csv` | One row per shift, with the danger-onset minute |
| `threshold_table.csv` | Every candidate ML threshold scored on validation data |
| `scores.csv`, `summary.json` | E1–E3 per test shift, scenario and method; run settings and library versions |
| `policy_logs.csv.gz` | Per-minute warnings for the dashboard |
| `sample_messages.jsonl` | Example MQTT-style wearable messages |

## What this prototype does not show

It does not show that real workers would be safer: PHS is a model of the body, faults are
injected into messages (there is no device or broker), and heart rate is generated from the same
simulated body as the labels. See `docs/decisions.md` and Section III-G of the paper.

## Evidence

- `docs/iteration_log.md`: what failed, what changed, and why
- `docs/decisions.md`: design decisions and rejected alternatives
- `docs/genai_log.md`: GenAI use and prompt records
- `CONTRIBUTIONS.md`: who did what
