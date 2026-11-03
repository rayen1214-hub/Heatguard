"""Part 6b: Supervisor dashboard (demo).   Run:  streamlit run dashboard.py

Replays one worker's shift from outputs/<run>/policy_logs.csv.gz:
heart rate, WBGT against its limit, the ML risk score, each method's warnings,
and the sensor-offline fallback banner.
"""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HeatGuard", layout="wide")
runs = sorted(p for p in Path("outputs").glob("*") if (p / "policy_logs.csv.gz").exists())
if not runs:
    st.error("No results yet. Run `python run_pilot.py --fetch` first.")
    st.stop()

with st.sidebar:
    st.title("HeatGuard")
    run = st.selectbox("Run", runs, format_func=lambda p: p.name)
    logs = pd.read_csv(run / "policy_logs.csv.gz", parse_dates=["timestamp"])
    info = json.loads((run / "summary.json").read_text())
    scenario = st.radio("Sensor scenario", ["clean", "S5_dropout", "S6_stuck"],
                        format_func=lambda s: {"clean": "Clean sensors", "S5_dropout": "HR dropout (min 60-69)",
                                               "S6_stuck": "HR stuck (min 60-74)"}.get(s, s))
    shifts = logs[["worker_id", "date", "onset"]].drop_duplicates()
    label = lambda r: f"{r.worker_id} · {r.date}" + ("  ⚠ danger event" if r.onset >= 0 else "")
    choice = st.selectbox("Worker shift", list(shifts.itertuples(index=False)), format_func=label)
    show_ref = st.checkbox("Show hidden reference (core temp)", value=False,
                           help="Researcher view only. The warning methods never see this.")

if info["run_info"].get("synthetic_weather"):
    st.warning("SYNTHETIC TEST WEATHER: this run checks the code only. Do not report these numbers.")

d = logs[(logs.scenario == scenario) & (logs.worker_id == choice.worker_id) & (logs.date == choice.date)].copy()
minute = st.slider("Replay to minute", 0, int(d.minute.max()), int(d.minute.max()))
now = d[d.minute == minute].iloc[0]
seen = d[d.minute <= minute]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Time", now.timestamp.strftime("%H:%M"))
c2.metric("Heart rate", "offline" if pd.isna(now.hr) else f"{now.hr:.0f} bpm")
c3.metric("WBGT / limit", f"{now.wbgt:.1f} / {now.wbgt_limit:.1f} °C")
c4.metric("ML risk (30 min)", f"{now.prob:.0%}")

if now["mode"] == "FALLBACK_WBGT":
    st.error("Sensor offline or stuck: degraded mode, warnings now come from the WBGT rule.")
elif now["mode"] == "UNAVAILABLE":
    st.error("Risk unavailable: no sensor or weather input. Check this worker manually.")
if now.ml_fallback:
    st.warning(f"⚠ HeatGuard warning for {choice.worker_id}: arrange a shaded break.")
else:
    st.success(f"{choice.worker_id}: no warning")

base = alt.Chart(seen).encode(x=alt.X("timestamp:T", title=None))
hr = base.mark_line().encode(y=alt.Y("hr:Q", title="Heart rate (bpm)", scale=alt.Scale(zero=False)))
wb = base.mark_line().encode(y=alt.Y("wbgt:Q", title="WBGT (°C)", scale=alt.Scale(zero=False)))
lim = base.mark_line(strokeDash=[4, 4], color="gray").encode(y="wbgt_limit:Q")
prob = base.mark_area(opacity=0.4).encode(y=alt.Y("prob:Q", title="ML risk", scale=alt.Scale(domain=[0, 1])))

warn = seen.melt(id_vars=["timestamp"], value_vars=["wbgt_rule", "ml", "ml_fallback"], var_name="method")
warn = warn[warn.value > 0]
names = {"wbgt_rule": "WBGT rule", "ml": "ML only", "ml_fallback": "ML + fallback"}
warn["method"] = warn["method"].map(names)
bands = alt.Chart(warn).mark_tick(thickness=3, size=18).encode(
    x="timestamp:T", y=alt.Y("method:N", title="Warnings", sort=list(names.values())), color=alt.Color("method:N", legend=None))

W = 760
charts = [hr.properties(height=160, width=W), (wb + lim).properties(height=160, width=W),
          prob.properties(height=110, width=W), bands.properties(height=110, width=W)]
if choice.onset >= 0 and minute >= choice.onset:
    rule = alt.Chart(d[d.minute == choice.onset]).mark_rule(color="red").encode(x="timestamp:T")
    charts = [c + rule for c in charts]
if show_ref:
    ref = base.mark_line(color="red").encode(y=alt.Y("t_re_reference:Q", title="Core temp, reference (°C)", scale=alt.Scale(zero=False)))
    dl = base.mark_line(strokeDash=[4, 4], color="red").encode(y="danger_limit:Q")
    charts.append((ref + dl).properties(height=140, width=W))
st.altair_chart(alt.vconcat(*charts).resolve_scale(x="shared"))

with st.expander("Test results for this run (E1-E3)"):
    rows = [{"scenario": s, "method": names.get(p, p), **{k: v for k, v in r.items() if k != "lead_iqr"}}
            for s, pol in info["results"].items() for p, r in pol.items() if isinstance(r, dict)]
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.caption(f"Threshold {info['run_info']['threshold']} chosen on validation data · horizon {info['run_info']['horizon_min']} min")
