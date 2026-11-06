"""Paper-ready figures and tables from the Week 8 results.

    python run_week8.py --run outputs/full      # first
    python make_figures.py --run outputs/full   # then this (needs: pip install matplotlib)

Writes to <run>/week8/figures/:
  fig1_alarm_burden.png/.pdf     warning minutes per shift, every method (clean sensors)
  fig2_lead_difference.png/.pdf  ML minus WBGT lead time per model, median and 95% interval
  fig3_factor_importance.png/.pdf  E5: which factor groups each model relies on
  fig4_sensitivity.png/.pdf      missed events as the heart-rate link weakens
  tables.md                      the same numbers as tables, ready for the paper

Figures are sized for one IEEE column (3.5 in wide) and stay readable in greyscale:
every bar and point is labelled on the axis, so colour is never the only cue.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# Colour follows the method everywhere: WBGT baseline in neutral grey, models in fixed order
COLOURS = {"wbgt_rule": "#8a8f98", "logreg": "#2a78d6", "random_forest": "#eb6834", "grad_boost": "#1baf7a"}
NAMES = {"wbgt_rule": "WBGT rule", "logreg": "Logistic regression", "random_forest": "Random forest",
         "grad_boost": "Gradient boosting"}
MODELS = ["logreg", "random_forest", "grad_boost"]
INK, MUTED, GRID = "#1d2321", "#5b6662", "#e3e6e4"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
WIDTH = 3.5   # inches, one IEEE column


def key(policy: str) -> str:
    return policy.replace("ml_", "").replace("fallback_", "")


def save(fig, out: Path, name: str):
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{name}.{ext}")
    plt.close(fig)


def fig_alarm_burden(summ, out, gain):
    d = summ[(summ.gain == gain) & (summ.scenario == "clean") & ~summ.policy.str.startswith("fallback_")].copy()
    d["k"] = d.policy.map(key)
    d = d.set_index("k").loc[["wbgt_rule"] + MODELS].reset_index()
    fig, ax = plt.subplots(figsize=(WIDTH, 1.55))
    y = range(len(d))[::-1]
    ax.barh(list(y), d.warning_min_per_shift, height=0.55, color=[COLOURS[k] for k in d.k])
    ax.set_yticks(list(y), [NAMES[k] for k in d.k])
    for yi, v in zip(y, d.warning_min_per_shift):
        ax.text(v + 4, yi, f"{v:.0f}", va="center", color=INK, fontsize=7)
    ax.set_xlim(0, 360)
    ax.set_xlabel("Warning minutes per 360-minute shift (clean sensors)")
    ax.grid(axis="y", visible=False)
    save(fig, out, "fig1_alarm_burden")


def fig_lead_difference(diffs, out, gain):
    d = diffs[(diffs.gain == gain) & (diffs.scenario == "clean") & (diffs.b == "wbgt_rule")
              & diffs.a.str.startswith("ml_")].copy()
    d["k"] = d.a.map(key)
    d = d.set_index("k").loc[MODELS].reset_index()
    fig, ax = plt.subplots(figsize=(WIDTH, 1.35))
    y = list(range(len(d)))[::-1]
    ax.axvline(0, color=MUTED, linewidth=0.8, linestyle="--")
    for yi, r in zip(y, d.itertuples()):
        ax.plot([r.ci95_low, r.ci95_high], [yi, yi], color=COLOURS[r.k], linewidth=2, solid_capstyle="round")
        ax.plot(r.median_diff_min, yi, "o", color=COLOURS[r.k], markersize=6, markeredgecolor="white",
                markeredgewidth=1.2)
        ax.text(31, yi, f"{r.median_diff_min:+.1f} [{r.ci95_low:+.0f}, {r.ci95_high:+.0f}]",
                va="center", color=INK, fontsize=6.5)
    ax.set_yticks(y, [NAMES[k] for k in d.k])
    ax.set_xlim(-31, 30)
    ax.set_xlabel("Lead time, ML minus WBGT rule (min)   ← WBGT earlier | ML earlier →")
    ax.grid(axis="y", visible=False)
    n = int(d.events.max()) if len(d) else 0
    ax.set_title(f"Median per-event difference and 95% bootstrap interval ({n} events)", loc="left",
                 color=MUTED, fontsize=7)
    save(fig, out, "fig2_lead_difference")


def fig_importance(imp, out):
    groups = (imp.groupby("group").ap_drop_mean.mean().sort_values(ascending=True).index.tolist())
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH * 2.05, 1.6), sharey=True)
    top = max(imp.ap_drop_mean.max() * 1.25, 0.05)
    for ax, m in zip(axes, MODELS):
        d = imp[imp.model == m].set_index("group").loc[groups]
        ax.barh(range(len(groups)), d.ap_drop_mean.clip(lower=0), height=0.55, color=COLOURS[m],
                xerr=d.ap_drop_sd, error_kw=dict(ecolor=MUTED, elinewidth=0.6, capsize=0))
        for i, v in enumerate(d.ap_drop_mean):
            ax.text(max(v, 0) + top * 0.03, i, f"{v:.2f}", va="center", fontsize=6.5, color=INK)
        ax.set_title(NAMES[m], loc="left")
        ax.set_xlim(0, top)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(groups)), [g.capitalize() for g in groups])
    fig.supxlabel("Drop in average precision when the factor group is shuffled (higher = relied on more)",
                  fontsize=7, color=INK)
    fig.tight_layout()
    save(fig, out, "fig3_factor_importance")


def fig_sensitivity(summ, out):
    d = summ[(summ.scenario == "clean") & summ.policy.str.startswith("ml_")].copy()
    if d.gain.nunique() < 2:
        return False
    d["k"] = d.policy.map(key)
    fig, ax = plt.subplots(figsize=(WIDTH, 1.7))
    for m in MODELS:
        g = d[d.k == m].sort_values("gain")
        ax.plot(g.gain, g.miss_rate * 100, "-o", color=COLOURS[m], linewidth=2, markersize=5,
                markeredgecolor="white", markeredgewidth=1, label=NAMES[m])
    ax.axhline(5, color=MUTED, linewidth=0.8, linestyle="--")
    ax.text(d.gain.min(), 5.5, " 5% miss limit", va="bottom", ha="left", fontsize=6.5, color=MUTED)
    ax.set_xticks(sorted(d.gain.unique()))
    ax.set_ylim(0, max(10, d.miss_rate.max() * 100 * 1.15))
    ax.set_xlabel("Heart-rate link to core temperature (bpm per \u00b0C)")
    ax.set_ylabel("Missed danger events (%)")
    ax.legend(frameon=False, fontsize=6.5, loc="upper right")
    save(fig, out, "fig4_sensitivity")
    return True


def md(df: pd.DataFrame, index: bool = False) -> str:
    """Markdown table without extra packages."""
    if index:
        df = df.reset_index()
    rows = [[str(c) for c in df.columns]] + [["" if pd.isna(v) else str(v) for v in r] for r in df.to_numpy()]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def tables(summ, diffs, imp, out, gain):
    cols = ["policy", "events", "missed", "median_lead", "false_per_shift", "warning_min_per_shift"]
    nice = {"policy": "Method", "events": "Events", "missed": "Missed", "median_lead": "Median lead (min)",
            "false_per_shift": "False episodes / shift", "warning_min_per_shift": "Warning min / shift"}

    def label(p):
        k = key(p)
        return NAMES[k] + (" + fallback" if p.startswith("fallback_") else "")

    lines = [f"# Week 8 result tables (heart-rate link {gain:g} bpm/°C, both folds pooled)", ""]
    t = summ[(summ.gain == gain) & (summ.scenario == "clean")][cols].copy()
    t = t[~t.policy.str.startswith("fallback_")]
    t["policy"] = t.policy.map(label)
    lines += ["## Table A. Clean sensors", "", md(t.rename(columns=nice).round(2)), ""]
    s = summ[(summ.gain == gain) & (summ.scenario != "clean")
             & (summ.policy.isin(["wbgt_rule", "ml_logreg", "fallback_logreg"]))][["scenario"] + cols].copy()
    s["policy"] = s.policy.map(label)
    lines += ["## Table B. Sensor faults (logistic regression; other models in summary_week8.csv)", "",
              md(s.rename(columns=nice).round(2)), ""]
    dd = diffs[(diffs.gain == gain) & (diffs.scenario == "clean")].copy()
    dd["comparison"] = dd.a.map(label) + " vs " + dd.b.map(label)
    lines += ["## Table C. Paired lead-time differences, clean sensors (minutes)", "",
              md(dd[["comparison", "events", "median_diff_min", "ci95_low", "ci95_high"]]
                 .rename(columns={"median_diff_min": "Median difference", "ci95_low": "95% low",
                                  "ci95_high": "95% high"}).round(1)), ""]
    if imp is not None:
        p = imp.pivot(index="group", columns="model", values="ap_drop_mean")[MODELS]
        p.columns = [NAMES[c] for c in p.columns]
        lines += ["## Table D. E5 factor importance (drop in average precision)", "",
                  md(p.round(3), index=True), ""]
    (out / "tables.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--gain", type=float, default=25.0, help="heart-rate link used for the main figures")
    args = ap.parse_args()
    w8 = Path(args.run) / "week8"
    out = w8 / "figures"
    out.mkdir(exist_ok=True)
    summ = pd.read_csv(w8 / "summary_week8.csv")
    diffs = pd.read_csv(w8 / "lead_differences.csv")
    imp = pd.read_csv(w8 / "importance_E5.csv") if (w8 / "importance_E5.csv").exists() else None
    synthetic = "SYNTHETIC" in Path(args.run).name
    fig_alarm_burden(summ, out, args.gain)
    fig_lead_difference(diffs, out, args.gain)
    if imp is not None:
        fig_importance(imp, out)
    fig_sensitivity(summ, out)
    tables(summ, diffs, imp, out, args.gain)
    print(f"figures and tables written to {out}/" + ("  (SYNTHETIC weather: do not report)" if synthetic else ""))


if __name__ == "__main__":
    main()
