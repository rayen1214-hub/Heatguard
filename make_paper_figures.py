"""Figures of the v0.5 paper, drawn from the committed result files.

    python make_paper_figures.py            # writes docs/paper/fig1.pdf, fig2.pdf (+ .png previews)

Fig. 1: architecture as built (v1.3). Fig. 2: warning minutes against missed events for every
option on the locked test set, plus the Dubai chart rule from the extra checks (open marker,
because it was scored after the locked run).
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

LOCKED = Path("docs/results/v5_locked_2026-11-16")
POSTHOC = Path("docs/results/v5_posthoc_2026-11-17")
DEST = Path("docs/paper")
INK, HOT, SOFT, WARM = "#1f2d3d", "#b8321f", "#eef2f6", "#fbeee6"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "pdf.fonttype": 42})


def fig1():
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    ax.set_xlim(0, 100), ax.set_ylim(0, 100), ax.axis("off")

    def box(x, y, w, h, text, warm=False, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2", fc=WARM if warm else SOFT,
                                    ec=INK, lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7, color=INK,
                fontweight="bold" if bold else "normal", linespacing=1.15)

    def arrow(a, b, hidden=False):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=7, lw=0.9, color=HOT if hidden else INK,
                                     linestyle=(0, (3, 2)) if hidden else "-", shrinkA=0, shrinkB=0))

    box(0, 82, 30, 18, "ERA5 Dubai\nweather\n(hour → minute)")
    box(35, 82, 30, 18, "Workers and\nschedule\n(legal break)")
    box(70, 82, 30, 18, "Body simulator\n(ISO 7933, person\ndifferences,\nself-pacing)", warm=True)
    box(35, 56, 30, 17, "Simulated wearable\n1 message / min:\nHR, skin, activity")
    box(0, 27, 46, 20, "Alert engine\nmodel → sensor check\n→ WBGT fallback → hold\n→ Heat Index ceiling")
    box(56, 27, 44, 20, "Scorer (reference only)\nmissed events, lead time,\nfalse episodes,\nwarning minutes", warm=True)
    box(0, 0, 21, 17, "Worker's\nwearable:\nSTOP")
    box(25, 0, 21, 17, "Supervisor\nsite board")
    box(56, 0, 44, 17, "UAE rules C1–C4: break,\nHeat Index, TWL, WBGT")
    arrow((30, 91), (35, 91)), arrow((65, 91), (70, 91))
    arrow((80, 82), (58, 73))                       # body -> wearable
    arrow((43, 56), (30, 47))                       # wearable -> engine
    arrow((9, 82), (9, 47))                         # weather -> engine
    arrow((46, 37), (56, 37))                       # engine -> scorer
    arrow((10.5, 27), (10.5, 17)), arrow((35.5, 27), (35.5, 17))
    arrow((78, 17), (78, 27))                       # rules -> scorer
    arrow((92, 82), (92, 47), hidden=True)          # hidden core temperature -> scorer
    ax.text(90.5, 64, "core temperature\n(hidden from\nthe engine)", ha="right", va="center", fontsize=6.6, color=HOT)
    save(fig, "fig1")


def fig2():
    s = pd.read_csv(LOCKED / "final_summary.csv")
    s = s[s["scenario"] == "clean"].set_index("policy")
    names = {"c2_heat_index": "C2 Heat Index", "c3_twl": "C3 TWL", "c4_wbgt": "C4 WBGT", "hg": "HeatGuard"}
    offsets = {"c2_heat_index": (-14, 10, "right"), "c3_twl": (10, 0, "left"), "c4_wbgt": (-9, -3, "right"), "hg": (0, 16, "center")}
    fig, ax = plt.subplots(figsize=(3.5, 2.05))
    for k, name in names.items():
        x, y = s.loc[k, "warning_min_per_shift"], 100 * s.loc[k, "miss_rate"]
        hg = k == "hg"
        ax.scatter([x], [y], s=70 if hg else 28, marker="*" if hg else "o", color=HOT if hg else INK, zorder=3)
        dx, dy, ha = offsets[k]
        ax.annotate(f"{name}\n{int(s.loc[k, 'missed'])} missed, {x:.0f} min", (x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=7, fontweight="bold" if hg else "normal", color=INK, linespacing=1.1)
    extra = POSTHOC / "analyse.json"
    if extra.exists():
        c = json.loads(extra.read_text())["P1_dubai_chart_rule"]["summary"]
        ax.scatter([c["warning_min_per_shift"]], [100 * c["miss_rate"]], s=28, marker="o", facecolors="white", edgecolors=INK, zorder=3)
        ax.annotate(f"Dubai chart rule*\n{c['missed']} missed, {c['warning_min_per_shift']:.0f} min", (c["warning_min_per_shift"], 100 * c["miss_rate"]),
                    xytext=(14, 14), textcoords="offset points", ha="right", va="center", fontsize=7, color=INK, linespacing=1.1)
    ax.set_yscale("symlog", linthresh=1, linscale=0.6)
    ax.set_yticks([0, 1, 2, 5, 10, 25, 50, 100]), ax.set_yticklabels(["0", "1", "2", "5", "10", "25", "50", "100"])
    ax.set_ylim(-0.3, 160), ax.set_xlim(-25, 600)
    ax.set_xlabel("Warning minutes per shift"), ax.set_ylabel("Missed events (% of 720)")
    ax.grid(True, lw=0.3, color="#d5dbe1"), ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.text(0.99, 0.03, "C1 break only: 720 missed, 0 min", transform=ax.transAxes, ha="right", fontsize=6.3, color="#555")
    save(fig, "fig2")


def save(fig, name):
    DEST.mkdir(parents=True, exist_ok=True)
    fig.savefig(DEST / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(DEST / f"{name}.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("written", DEST / f"{name}.pdf")


if __name__ == "__main__":
    fig1()
    fig2()
