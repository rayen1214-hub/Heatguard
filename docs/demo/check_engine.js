// Agreement check: the browser engine (engine.js) against the Python engine.
//
//   python make_demo_data.py        # writes docs/demo/demo_reference.json
//   node docs/demo/check_engine.js  # exits 1 if any minute disagrees
//
// For every demo shift and every scenario (clean, 10-minute dropout, 15-minute stuck sensor) it
// compares the risk, the warning on/off state and the fallback state, minute by minute.
const fs = require("fs");
const path = require("path");
const HG = require("./engine.js");

const { data, ref } = JSON.parse(fs.readFileSync(path.join(__dirname, "demo_reference.json"), "utf8"));
let minutes = 0, alertDiff = 0, fallbackDiff = 0, maxProbDiff = 0, cases = 0;
for (const shift of data.shifts) {
  for (const [scenario, want] of Object.entries(ref[shift.code])) {
    const got = HG.run(data.model, shift, HG.SCENARIOS[scenario]);
    cases++;
    for (let t = 0; t < want.prob.length; t++) {
      minutes++;
      maxProbDiff = Math.max(maxProbDiff, Math.abs(got.prob[t] - want.prob[t]));
      if (got.alert[t] !== want.alert[t]) alertDiff++;
      if (got.fallback[t] !== want.fallback[t]) fallbackDiff++;
    }
  }
}
console.log(`${data.shifts.length} shifts x 3 scenarios = ${cases} replays, ${minutes} minutes compared`);
console.log(`largest risk difference: ${maxProbDiff.toExponential(2)}`);
console.log(`warning state differs on ${alertDiff} minutes; fallback state differs on ${fallbackDiff} minutes`);
const ok = alertDiff === 0 && fallbackDiff === 0 && maxProbDiff < 1e-3;
console.log(ok ? "PASS: the browser engine matches the Python engine" : "FAIL");
process.exit(ok ? 0 : 1);
