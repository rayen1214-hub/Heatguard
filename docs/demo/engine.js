// HeatGuard v0.5 alert engine in plain JavaScript.
//
// A line-for-line port of the Python engine (heatguard/features.py, run_v5.add_extra,
// heatguard/alerts.py, run_v5.hg_alert, heatguard/v5.heatguard_alert). It takes one wearable
// message per minute and uses past and current values only, exactly as the Python code does.
// `node docs/demo/check_engine.js` compares its output with the Python engine on every demo shift.
//
// Used in two places: inlined into the demo page, and required by check_engine.js.
const HGEngine = (() => {
  const mean = (a, from, to) => { let s = 0, n = 0; for (let i = Math.max(0, from); i <= to; i++) { s += a[i]; n++; } return s / n; };
  const meanValid = (a, from, to) => { let s = 0, n = 0; for (let i = Math.max(0, from); i <= to; i++) if (a[i] != null) { s += a[i]; n++; } return n ? s / n : null; };

  // Sensor faults act on the messages only (same as wearables.inject_fault).
  //   {type: "dropout", start, minutes}: no heart-rate reading
  //   {type: "stuck",   start, minutes}: heart rate frozen at the reading before `start`
  function applyFaults(hr, faults) {
    const out = hr.slice();
    for (const f of faults || []) {
      const end = Math.min(out.length, f.start + f.minutes);
      const held = hr[Math.max(0, f.start - 1)];
      for (let m = f.start; m < end; m++) out[m] = f.type === "dropout" ? null : held;
    }
    return out;
  }
  const SCENARIOS = {
    clean: [],
    S5_dropout: [{ type: "dropout", start: 60, minutes: 10 }],
    S6_stuck: [{ type: "stuck", start: 60, minutes: 15 }],
  };

  // One engine per worker and day. Call step() once per minute, in order.
  function create(model, shift) {
    const n = shift.phase.length;
    const [hrLo, hrHi] = model.hr_valid;
    const hr = [], hrFf = [], skin = [], act = [], wbgt = [], hi = [], hrMean15 = [], skinMean15 = [], fused = [];
    let lastValid = -1, stuckRun = 0, hrMin = null, skinMin = null;
    const planned = shift.work_rate * model.met_per_wm2;

    function step(msg) {
      const t = hr.length;
      const valid = msg.hr != null && msg.hr >= hrLo && msg.hr <= hrHi;   // implausible readings count as missing
      hr.push(valid ? msg.hr : null);
      const prevFf = t ? hrFf[t - 1] : null;
      hrFf.push(valid ? msg.hr : prevFf);                                 // forward fill = past values only
      skin.push(msg.skin); act.push(msg.act); wbgt.push(msg.wbgt); hi.push(msg.hi);
      if (valid) lastValid = t;
      stuckRun = (t && hrFf[t] != null && prevFf != null && hrFf[t] === prevFf) ? stuckRun + 1 : 0;

      const f = {};
      f.hr_last = hrFf[t];
      f.hr_mean5 = meanValid(hr, t - 4, t) ?? hrFf[t];
      f.hr_mean15 = meanValid(hr, t - 14, t) ?? hrFf[t];
      f.hr_slope15 = (t >= 15 && hrFf[t] != null && hrFf[t - 15] != null) ? (hrFf[t] - hrFf[t - 15]) / 15 : 0;
      f.skin_mean5 = mean(skin, t - 4, t);
      f.skin_mean15 = mean(skin, t - 14, t);
      f.skin_slope15 = t >= 15 ? (skin[t] - skin[t - 15]) / 15 : 0;
      f.act_mean5 = mean(act, t - 4, t);
      f.act_mean15 = mean(act, t - 14, t);
      f.wbgt = msg.wbgt;
      f.wbgt_mean60 = mean(wbgt, t - 59, t);
      f.tdb = msg.tdb;
      f.rh = msg.rh;
      f.mass_kg = shift.mass;
      f.height_m = shift.height;
      f.acclimatised = shift.acclimatised ? 1 : 0;
      f.work_rate_wm2 = shift.work_rate;
      f.hr_age = lastValid < 0 ? n : t - lastValid;                       // minutes since the last valid reading
      f.hr_stuck = (stuckRun >= model.stuck_after - 1 && valid) ? 1 : 0;  // 5 identical readings in a row
      f.minute_of_day = t;
      f.heat_index = msg.hi;
      f.heat_index_mean60 = mean(hi, t - 59, t);
      f.pace_gap15 = planned - f.act_mean15;                              // how much slower than planned
      hrMean15.push(f.hr_mean15); skinMean15.push(f.skin_mean15);
      if (f.hr_mean15 != null) hrMin = hrMin == null ? f.hr_mean15 : Math.min(hrMin, f.hr_mean15);
      skinMin = skinMin == null ? f.skin_mean15 : Math.min(skinMin, f.skin_mean15);
      f.hr_rise = f.hr_mean15 != null ? f.hr_mean15 - hrMin : 0;
      f.skin_rise = f.skin_mean15 - skinMin;

      // model: median imputer -> standard scaler -> logistic regression
      let logit = model.intercept;
      const push = {};
      model.features.forEach((name, i) => {
        const x = f[name] == null || Number.isNaN(f[name]) ? model.median[i] : f[name];
        const c = model.coef[i] * (x - model.mean[i]) / model.scale[i];
        push[name] = c; logit += c;
      });
      const prob = 1 / (1 + Math.exp(-logit));

      // policy: model normally; WBGT rule while the heart-rate reading is missing or stuck;
      // warn if the WBGT rule is unavailable too (never show "safe" when blind)
      const degraded = f.hr_age >= model.offline_after || f.hr_stuck === 1;
      const envMissing = msg.wbgt_alert === -1;
      const mode = degraded ? (envMissing ? "UNAVAILABLE" : "FALLBACK_WBGT") : "ML";
      const now = mode === "ML" ? (prob >= model.threshold ? 1 : 0) : (mode === "UNAVAILABLE" ? 1 : Math.max(msg.wbgt_alert, 0));
      fused.push(now);
      let latch = 0;                                                      // a warning stays on for `hold` minutes
      for (let k = Math.max(0, t - model.hold); k <= t; k++) if (fused[k]) { latch = 1; break; }
      const ceiling = msg.hi >= model.hi_ceiling;
      const working = msg.phase !== "b";                                  // no one is warned during the legal break
      const alert = (latch || ceiling) && working ? 1 : 0;
      return { minute: t, prob, mode, alert, trigger: now, ceiling, features: f, push, logit };
    }
    return { step };
  }

  // Replay a whole day: returns per-minute outputs.
  function run(model, shift, faults) {
    const eng = create(model, shift), hr = applyFaults(shift.hr, faults);
    const out = { prob: [], alert: [], fallback: [], mode: [], hr, steps: [] };
    for (let t = 0; t < shift.phase.length; t++) {
      const r = eng.step({ hr: hr[t], skin: shift.skin[t], act: shift.act[t], wbgt: shift.wbgt[t], tdb: shift.tdb[t],
        rh: shift.rh[t], hi: shift.hi[t], wbgt_alert: shift.wbgt_alert[t], phase: shift.phase[t] });
      out.prob.push(r.prob); out.alert.push(r.alert); out.fallback.push(r.mode === "ML" ? 0 : 1); out.mode.push(r.mode); out.steps.push(r);
    }
    return out;
  }

  // Same scoring as heatguard/evaluate.score_shift.
  function score(alert, onset, horizon = 30) {
    const n = alert.length, end = onset == null ? n : onset;
    let warning = 0; for (let k = 0; k < end; k++) warning += alert[k] ? 1 : 0;
    if (onset == null) return { event: false, warning, missed: null, lead: null };
    const w0 = Math.max(0, onset - horizon);
    let first = -1; for (let k = w0; k < onset; k++) if (alert[k]) { first = k; break; }
    return { event: true, warning, missed: first < 0, lead: first < 0 ? 0 : onset - first };
  }

  return { create, run, score, applyFaults, SCENARIOS };
})();
if (typeof module !== "undefined") module.exports = HGEngine;
