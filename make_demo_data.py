"""Run: python make_demo_data.py docs/demo   (needs outputs/v5 from the locked run).
Demo data: replay a few LOCKED-TEST shifts minute by minute with the locked model
(same training fit, threshold 0.32, hold 30). Reads outputs/v5, writes only to DEST.
Checks that every replayed shift scores exactly as in final_scores.csv."""
import json, sys, zlib
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, ".")
import run_v5 as R
from heatguard import v5, evaluate, wearables, alerts, config as C

OUT = Path("outputs/v5"); DEST = Path(sys.argv[1])
sc = pd.read_csv(OUT / "final_scores.csv")
cl = sc[sc.scenario == "clean"]
miss = cl.pivot_table(index=["worker_id", "date"], columns="policy", values="missed", aggfunc="first")
wm = cl.pivot_table(index=["worker_id", "date"], columns="policy", values="warning_minutes")
ev = cl[cl.policy == "hg"].set_index(["worker_id", "date"])["event"]

picks = []
a = miss[(miss.hg == False) & (miss.c2_heat_index == True)].index[0]; picks.append(("A", "clean", a, "HeatGuard catches an event the Heat Index rule misses"))
b = miss[(miss.hg == False) & (miss.c2_heat_index == False) & (miss.c4_wbgt == False)].index
b = max(b, key=lambda k: wm.loc[k, "c4_wbgt"] - wm.loc[k, "hg"]); picks.append(("B", "clean", b, "Every rule catches it, HeatGuard with far fewer warning minutes"))
quiet = wm[~ev.reindex(wm.index).astype(bool)]
c = (quiet.c4_wbgt - quiet.hg).idxmax(); picks.append(("C", "clean", c, "No danger: WBGT warns most of the day, HeatGuard stays quiet"))
off = [k for k in miss[(miss.hg == False)].index if not v5.ban_applies(k[1])]
d = off[0]; picks.append(("D", "clean", d, "A hot day outside the legal break dates"))
st = sc[(sc.scenario == "S6_stuck") & (sc.policy == "hg")].set_index(["worker_id", "date"])["warning_minutes"]
stm = sc[(sc.scenario == "S6_stuck") & (sc.policy == "hg")].set_index(["worker_id", "date"])["missed"]
cand = [k for k in stm.index if stm[k] == False and ev.get(k, False) and abs(st[k] - wm.hg[k]) <= 20]
e = cand[0]; picks.append(("E", "S6_stuck", e, "Heart-rate sensor stuck: HeatGuard falls back to WBGT"))

print("fitting the locked model on training workers ...", flush=True)
sel = json.loads((OUT / "select.json").read_text()); name = sel["primary_model"]
chosen = pd.read_csv(OUT / "select_summary.csv").set_index("model").loc[name]
thr, hold = float(chosen["threshold"]), int(chosen["hold"])
wk, ix, groups, _ = R.load_set("train", OUT)
model = R.fit(name, R.rows(wk, ix, groups))
wk_t, ix_t, groups_t, twl_t = R.load_set("test", OUT)

shifts = []
for code, scen, (wid, date), title in picks:
    traj, worker = groups_t[(wid, date)], R.worker_row(wk_t, wid)
    r = ix_t[(ix_t.worker_id == wid) & (ix_t.date == date)].iloc[0]
    onset = None if pd.isna(r.onset) else int(r.onset)
    seed = C.SEED + zlib.crc32(f"{wid}|{date}".encode()) % 10_000
    msgs = wearables.inject_fault(wearables.make_messages(traj, worker, seed), scen, seed, worker=worker, traj=traj)
    feats, rule = R.shift_inputs(traj, worker, scen)
    s = dict(traj=traj, worker=worker, feats=feats, rule=rule)
    prob = model.predict_proba(feats[R.FEATS])[:, 1]
    hg = R.hg_alert(prob, thr, s, hold)
    comp = v5.comparator_alerts(traj, worker, v5.twl_minutes(twl_t, traj["timestamp"]), rule["wbgt_alert"].to_numpy())
    # consistency check against the locked scores
    for p, al in {"hg": hg, "c2_heat_index": comp["c2_heat_index"].to_numpy(), "c4_wbgt": comp["c4_wbgt"].to_numpy()}.items():
        got = evaluate.score_shift(al, onset, R.HORIZON)
        ref = sc[(sc.worker_id == wid) & (sc.date == date) & (sc.scenario == scen) & (sc.policy == p)].iloc[0]
        assert int(got["warning_minutes"]) == int(ref.warning_minutes), (code, p, got, ref.to_dict())
    hr = msgs["hr"].to_numpy() if "hr" in msgs else np.full(len(traj), np.nan)
    end = onset + 1 if onset is not None else len(traj)
    shifts.append(dict(code=code, title=title, scenario=scen, worker=wid, date=date, onset=onset,
        acclimatised=bool(worker["acclimatised"]), work_rate=int(worker["work_rate_wm2"]),
        limit=38.5 if worker["acclimatised"] else 38.2, ban=bool(v5.ban_applies(date)),
        minute=traj["minute"].tolist()[:end], phase=traj["phase"].tolist()[:end],
        core=np.round(traj["t_re"].to_numpy()[:end], 2).tolist(),
        hr=[None if not np.isfinite(x) else int(round(x)) for x in hr[:end]],
        wbgt=np.round(traj["wbgt"].to_numpy()[:end], 1).tolist(),
        hi=np.round(traj["heat_index"].to_numpy()[:end], 1).tolist(),
        risk=np.round(prob[:end], 3).tolist(),
        hg=[int(x) for x in hg[:end]], c2=[int(x) for x in comp["c2_heat_index"][:end]],
        c3=[int(x) for x in comp["c3_twl"][:end]], c4=[int(x) for x in comp["c4_wbgt"][:end]],
        fallback=[int(x) for x in (alerts.run_policies(prob, thr, rule["wbgt_alert"], feats)["mode"] != "ML").to_numpy()[:end]]))
    print(code, wid, date, scen, "onset", onset, "ok", flush=True)
(DEST / "demo_shifts.json").write_text(json.dumps(shifts))
print("written", DEST / "demo_shifts.json")
