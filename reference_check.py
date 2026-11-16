"""Week 9: compare the simulated workers with published field studies of real workers in heat.

    python reference_check.py --run outputs/full

The simulated workers are not real people, so we check that they behave like real ones.
Reference numbers (all real field measurements, summer, hot climates):
  - Qatar 2019, ILO/FIFA field study, 125 outdoor workers: about 1 in 3 workers passed 38.0 C at some
    point; 38.0-38.4 C for 2-5% of work time; nobody reached 38.5 C.
  - Guatemala sugarcane cutters (Adgate et al. 2025, AJP-Regu, ingestible pill, 55 workers): during a
    workday 44% passed 38.0 C, 16% passed 38.3 C, 6% passed 38.5 C.
  - UAE construction workers, Al Ain (Bates & Schneider 2008, J Occup Med Toxicol 3:21, 22 workers):
    mean working heart rate 87-91 bpm; WBGT 26-29 C (site means, 08:00-16:00).
Output: <run>/reference_check.csv and a printed table.
"""
from __future__ import annotations

import argparse
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from heatguard import config as C
from heatguard import wearables

REFS = {
    "share of worker-shifts passing 38.0 C": ("44% (Guatemala, per workday)", 0.44),
    "share of worker-shifts passing 38.3 C": ("16% (Guatemala)", 0.16),
    "share of worker-shifts passing 38.5 C": ("6% (Guatemala); 0% (Qatar)", 0.06),
    "share of workers passing 38.0 C on any monitored day": ("about 33% (Qatar)", 0.33),
    "share of work time at 38.0-38.4 C": ("2-5% (Qatar)", 0.035),
    "mean working heart rate (bpm)": ("87-91 (UAE, Al Ain)", 89.0),
    "mean WBGT during the shift (C)": ("26-29 (UAE, Al Ain, 08-16 h)", 27.5),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--days", type=int, default=3, help="days per worker for the 'any monitored day' measure "
                                                         "(Qatar monitored workers over a few days)")
    args = ap.parse_args()
    run = Path(args.run)
    trajs = pd.read_csv(run / "trajectories.csv.gz", parse_dates=["timestamp"])
    wk = pd.read_csv(run / "workers.csv").set_index("worker_id")

    per_shift = trajs.groupby(["worker_id", "date"]).agg(t_max=("t_re", "max"), wbgt=("wbgt", "mean")).reset_index()
    work = trajs[trajs["phase"] == "work"]

    # Heart rate during work minutes, from the simulated wearable (clean sensors, main heart-rate link)
    hr_work = []
    for (wid, date), traj in trajs.groupby(["worker_id", "date"]):
        traj = traj.reset_index(drop=True)
        w = wk.loc[wid].copy()
        w["worker_id"] = wid
        seed = C.SEED + zlib.crc32(f"{wid}|{date}".encode()) % 10_000
        msgs = wearables.make_messages(traj, w, seed)
        hr_work.append((int(w["work_rate_wm2"]), msgs["hr"][traj["phase"].to_numpy() == "work"].mean()))

    # 'Any monitored day': for each worker, the first `days` dates in time order (like a short field study)
    first_days = per_shift.sort_values("date").groupby("worker_id").head(args.days)
    any_day = first_days.groupby("worker_id")["t_max"].max()

    sim = {
        "share of worker-shifts passing 38.0 C": (per_shift["t_max"] > 38.0).mean(),
        "share of worker-shifts passing 38.3 C": (per_shift["t_max"] > 38.3).mean(),
        "share of worker-shifts passing 38.5 C": (per_shift["t_max"] > 38.5).mean(),
        "share of workers passing 38.0 C on any monitored day": (any_day > 38.0).mean(),
        "share of work time at 38.0-38.4 C": work["t_re"].between(38.0, 38.4).mean(),
        "mean working heart rate (bpm)": float(np.nanmean([h for _, h in hr_work])),
        "mean WBGT during the shift (C)": per_shift["wbgt"].mean(),
    }
    rows = []
    for k, (ref_text, ref_val) in REFS.items():
        v = sim[k]
        pct = "share" in k
        rows.append({"measure": k, "simulated": round(100 * v, 1) if pct else round(v, 1),
                     "unit": "%" if pct else "", "real reference": ref_text,
                     "ratio sim/ref": round(v / ref_val, 2)})
    out = pd.DataFrame(rows)
    out.to_csv(run / "reference_check.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"{len(per_shift)} simulated worker-shifts, {per_shift['worker_id'].nunique()} workers\n")
    print(out.to_string(index=False))
    by_rate = pd.DataFrame(hr_work, columns=["work_rate_wm2", "hr"]).groupby("work_rate_wm2")["hr"].mean().round(1)
    by_rate.to_csv(run / "reference_check_hr_by_work_rate.csv")
    print("\nMean working heart rate by work rate (W/m2); the UAE reference workers self-paced (light work):\n"
          + by_rate.to_string())


if __name__ == "__main__":
    main()
