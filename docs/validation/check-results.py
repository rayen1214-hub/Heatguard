"""Validate supplied evidence and recompute the Dubai airport comparison."""
from pathlib import Path
import csv
import gzip
import hashlib
import json
from datetime import datetime, timedelta
from statistics import mean, median

root = Path(__file__).resolve().parents[2]
run = root / "docs/results/prospie_retrained"
result = json.loads((run / "results.json").read_text())
for name, digest in result["source_sha256"].items():
    path = (root / "data/external" / name.split("/data/", 1)[1]
            if name.startswith("../") else root / name)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
print("Both ERA5 inputs and the three retraining source files match recorded checksums.")

with (run / "test_scores.csv").open() as file:
    groups = {}
    for row in csv.DictReader(file):
        groups.setdefault(row["variant"], []).append(row)
events = {}
cohorts = set()
for variant, rows in groups.items():
    keys = {(r["worker_id"], r["date"]) for r in rows}
    assert len(keys) == len(rows) == 480
    cohorts.add(frozenset(keys))
    events[variant] = {(r["worker_id"], r["date"]) for r in rows if r["event"] == "True"}
    recorded = result["results"][variant]
    assert len(events[variant]) == recorded["events"] == 84
    assert sum(r["missed"] == "True" for r in rows) == recorded["missed"]
    assert abs(mean(int(r["warning_minutes"]) for r in rows) - recorded["warning_min_per_shift"]) < 1e-9
    print(f"{variant}: 480 paired shifts, 84 events, {recorded['missed']} misses.")
assert len(cohorts) == 1
assert len({frozenset(keys) for keys in events.values()}) == 1

with (root / "data/weather_hourly.csv").open() as file:
    era = {datetime.fromisoformat(r["timestamp"]): float(r["temperature_2m"]) for r in csv.DictReader(file)}
observations = {}
with (root / "data/external/dubai-airport/OMDB-METAR-2025-summer.csv").open() as file:
    for r in csv.DictReader(file):
        stamp = datetime.fromisoformat(r["valid"]) + timedelta(hours=4)
        if stamp in era and 6 <= stamp.hour < 12 and r["tmpc"] not in ("", "M"):
            observations.setdefault(stamp, []).append(float(r["tmpc"]))
errors = [abs(era[t] - median(x)) for t, x in observations.items()]
assert len(errors) == 731
print(f"Airport comparison: {len(errors)} matched morning hours, mean absolute error {mean(errors):.3f} °C.")

locked = root / "docs/results/v5_locked_2026-11-16/final_scores.csv.gz"
with gzip.open(locked, "rt") as file:
    clean = {}
    for row in csv.DictReader(file):
        if row["scenario"] == "clean":
            clean.setdefault(row["policy"], []).append(row)
for policy in ("hg", "c4_wbgt"):
    rows = clean[policy]
    assert len(rows) == 4000 and sum(r["event"] == "True" for r in rows) == 720
    misses = sum(r["missed"] == "True" for r in rows)
    assert misses == {"hg": 8, "c4_wbgt": 5}[policy]
    print(f"Locked {policy}: 4,000 shifts, 720 events, {misses} misses, "
          f"{mean(int(r['warning_minutes']) for r in rows):.2f} warning minutes/shift.")
