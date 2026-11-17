"""Build the live demo page (docs/demo/heatguard_demo.html).

    python make_demo_data.py            # needs outputs/v5 (the locked sets); writes docs/demo/
    python make_demo_data.py --page     # only rebuild the page from template.html, engine.js and the stored data

The page runs the HeatGuard alert engine IN THE BROWSER (docs/demo/engine.js): each simulated
wearable message goes through the same inputs, model, sensor check, fallback, hold and ceiling as
the Python code. This script exports the locked model's numbers and a few locked-test shifts,
plus the Python engine's own output for those shifts so that `node docs/demo/check_engine.js` can
prove both engines agree. It reads outputs/v5 and never writes there.
"""
import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

import run_v5 as R
from heatguard import alerts, baseline, evaluate, v5, wearables
from heatguard import config as C

OUT, DEST = Path("outputs/v5"), Path("docs/demo")
STORIES = [  # (code, worker, date, scripted fault, title) - chosen from the locked test set on 16 Nov
    ("A", "X006", "2024-06-01", None, "HeatGuard catches an event the Heat Index rule misses"),
    ("B", "X086", "2024-08-30", None, "Every rule catches it, HeatGuard with far fewer warning minutes"),
    ("C", "X004", "2024-09-19", None, "No danger: WBGT warns all day, HeatGuard stays quiet"),
    ("D", "X003", "2024-09-20", None, "A hot day outside the legal break dates"),
    ("E", "X001", "2024-06-23", "S6_stuck", "Heart-rate sensor stuck at 07:00: HeatGuard falls back to WBGT"),
]
BOARD_SIZE = 12


def r(a, nd):
    return [None if not np.isfinite(x) else round(float(x), nd) for x in np.asarray(a, dtype=float)]


def build_page(data):
    html = (DEST / "template.html").read_text()
    html = html.replace("/*__ENGINE__*/", (DEST / "engine.js").read_text()).replace("__DATA__", json.dumps(data, separators=(",", ":")))
    (DEST / "heatguard_demo.html").write_text(html)
    print("written", DEST / "heatguard_demo.html", f"({len(html) // 1024} KB); board date {data['board_date']}")


def main():
    if "--page" in sys.argv:
        return build_page(json.loads((DEST / "demo_reference.json").read_text())["data"])
    sel = pd.read_csv(OUT / "select_summary.csv").set_index("model").loc["logreg"]
    thr, hold = float(sel["threshold"]), int(sel["hold"])
    wk, ix, groups, _ = R.load_set("train", OUT)
    model = R.fit("logreg", R.rows(wk, ix, groups))
    imp, sc, lr = model[0], model[1], model[2]
    mjson = {"features": R.FEATS, "median": imp.statistics_.tolist(), "mean": sc.mean_.tolist(),
             "scale": sc.scale_.tolist(), "coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]),
             "threshold": thr, "hold": hold, "hi_ceiling": v5.HI_CEILING, "hr_valid": list(C.HR_VALID_RANGE),
             "offline_after": C.HR_OFFLINE_AFTER_MIN, "stuck_after": C.HR_STUCK_AFTER_MIN, "met_per_wm2": 1 / 58.15}
    wk_t, ix_t, groups_t, twl_t = R.load_set("test", OUT)
    scores = pd.read_csv("docs/results/v5_locked_2026-11-16/final_scores.csv.gz")

    # the site board: one legal-break day with a mix of workers who do and do not reach danger
    days = ix_t[ix_t["ban_day"]].groupby("date").agg(n=("worker_id", "size"), ev=("onset", "count"))
    days = days[(days["n"] >= BOARD_SIZE) & days["ev"].between(3, 5)].sort_values(["ev", "n"], ascending=False)
    board_date = days.index[0]
    cand = ix_t[ix_t["date"] == board_date].sort_values("worker_id")
    board = pd.concat([cand[cand["onset"].notna()], cand[cand["onset"].isna()]]).head(BOARD_SIZE).sort_values("worker_id")
    picks = [(f"S{c}", w, d, f, t) for c, w, d, f, t in STORIES] + \
            [(f"B{i + 1:02d}", w, board_date, None, "") for i, w in enumerate(board["worker_id"])]

    shifts, ref = [], {}
    for code, wid, date, fault, title in picks:
        traj, worker = groups_t[(wid, date)], R.worker_row(wk_t, wid)
        row = ix_t[(ix_t["worker_id"] == wid) & (ix_t["date"] == date)].iloc[0]
        onset = None if pd.isna(row["onset"]) else int(row["onset"])
        seed = C.SEED + zlib.crc32(f"{wid}|{date}".encode()) % 10_000
        msgs = wearables.make_messages(traj, worker, seed)
        rule = baseline.wbgt_rule(traj["wbgt"], traj["met_wm2"], worker)
        comp = v5.comparator_alerts(traj, worker, v5.twl_minutes(twl_t, traj["timestamp"]), rule["wbgt_alert"].to_numpy())
        ref[code] = {}
        for scen in R.SCENARIOS:                       # the Python engine's output, for the agreement check
            feats, _ = R.shift_inputs(traj, worker, scen)
            prob = model.predict_proba(feats[R.FEATS])[:, 1]
            hg = R.hg_alert(prob, thr, dict(traj=traj, worker=worker, feats=feats, rule=rule), hold)
            mode = alerts.run_policies(prob, thr, rule["wbgt_alert"], feats)["mode"]
            ref[code][scen] = {"prob": r(prob, 6), "alert": [int(x) for x in hg], "fallback": [int(m != "ML") for m in mode]}
            got = evaluate.score_shift(hg, onset, R.HORIZON)       # must equal the locked score of this shift
            lock = scores[(scores.worker_id == wid) & (scores.date == date) & (scores.scenario == scen) & (scores.policy == "hg")].iloc[0]
            assert int(got["warning_minutes"]) == int(lock.warning_minutes), (code, scen)
        shifts.append({
            "code": code, "title": title, "fault": fault, "worker": wid, "date": date, "onset": onset,
            "acclimatised": bool(worker["acclimatised"]), "work_rate": int(worker["work_rate_wm2"]),
            "mass": float(worker["mass_kg"]), "height": float(worker["height_m"]),
            "limit": 38.5 if worker["acclimatised"] else 38.2, "ban": bool(v5.ban_applies(date)),
            "phase": "".join(p[0] for p in traj["phase"]),
            "hr": r(msgs["hr"], 1), "skin": r(msgs["skin_temp"], 2), "act": r(msgs["activity"], 2),
            "wbgt": r(traj["wbgt"], 3), "tdb": r(traj["tdb"], 3), "rh": r(traj["rh"], 3), "hi": r(traj["heat_index"], 3),
            "core": r(traj["t_re"], 2), "wbgt_alert": [int(x) for x in rule["wbgt_alert"]],
            "c2": "".join(str(int(x)) for x in comp["c2_heat_index"]), "c3": "".join(str(int(x)) for x in comp["c3_twl"]),
            "c4": "".join(str(int(x)) for x in comp["c4_wbgt"]),
        })
        print(code, wid, date, "onset", onset, "matches the locked scores", flush=True)

    DEST.mkdir(parents=True, exist_ok=True)
    data = {"model": mjson, "board_date": board_date, "shifts": shifts}
    (DEST / "demo_reference.json").write_text(json.dumps({"data": data, "ref": ref}, separators=(",", ":")))
    build_page(data)


if __name__ == "__main__":
    main()
