"""Generate a polished PNG chart of the 21-iteration pass-rate history."""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Style tokens — match the project's DM Serif / DM Sans / navy palette
NAVY = "#1a1a2e"
BLUE = "#4285F4"
GREEN = "#10b981"
RED = "#ef4444"
WARM_WHITE = "#fafaf8"
MUTED = "#6b7280"
BORDER = "#e5e7eb"

HISTORY_PATH = Path(__file__).resolve().parents[2] / "meta-agent/experience/ml-advisor/history.json"
OUT_PATH = Path(__file__).resolve().parent / "progress.png"


def main():
    data = json.loads(HISTORY_PATH.read_text())
    iterations = data["iterations"]

    names = [it["name"] for it in iterations]
    rates = [it.get("pass_rate", it.get("reward", 0)) * 100 for it in iterations]

    # Compute running best
    best = []
    cur = 0.0
    for r in rates:
        cur = max(cur, r)
        best.append(cur)

    fig, ax = plt.subplots(figsize=(14, 7), dpi=140)
    fig.patch.set_facecolor(WARM_WHITE)
    ax.set_facecolor(WARM_WHITE)

    x = list(range(len(names)))

    # Running best — stepped line in grey for context
    ax.step(x, best, where="mid", color=MUTED, linewidth=1.2, alpha=0.4, label="Running best")

    # Per-iteration rate — markers + thin connecting line
    ax.plot(x, rates, color=BLUE, linewidth=1.5, alpha=0.6, zorder=2)

    # Color markers: green if new best, red if regression (below previous best), blue otherwise
    prev_best = 0.0
    for i, r in enumerate(rates):
        if r > prev_best:
            color = GREEN
            marker = "o"
            size = 140
            prev_best = r
        elif r < prev_best - 0.01:  # clear regression
            color = RED
            marker = "v"
            size = 110
        else:
            color = BLUE
            marker = "o"
            size = 80
        ax.scatter([i], [r], s=size, color=color, zorder=3, edgecolors="white", linewidths=1.6)

    # Annotate key milestones
    key_annotations = {
        "baseline": ("Baseline\n80%", 10, -40),
        "evo_001": ("Phase\nordering", 10, 18),
        "evo_008": ("Context\noverride\n95%", -15, 22),
        "evo_015": ("100%", 0, 14),
    }
    for name, (label, dx, dy) in key_annotations.items():
        if name in names:
            idx = names.index(name)
            rate = rates[idx]
            ax.annotate(
                label,
                xy=(idx, rate),
                xytext=(idx + dx, rate + dy),
                fontsize=10,
                fontweight="600",
                color=NAVY,
                ha="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, alpha=0.6),
            )

    # Horizontal reference lines
    ax.axhline(y=80, color=BORDER, linestyle="--", linewidth=1, alpha=0.7, zorder=1)
    ax.axhline(y=100, color=GREEN, linestyle="--", linewidth=1, alpha=0.4, zorder=1)

    # Axes
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("evo_0", "").replace("baseline", "base") for n in names], fontsize=9, color=MUTED, rotation=0)
    ax.set_yticks([50, 60, 70, 80, 85, 90, 95, 100])
    ax.set_yticklabels(["50%", "60%", "70%", "80%", "85%", "90%", "95%", "100%"], fontsize=10, color=MUTED)
    ax.set_ylim(45, 108)
    ax.set_xlim(-0.7, len(names) - 0.3)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(BORDER)

    ax.grid(axis="y", color=BORDER, linewidth=0.5, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Titles
    fig.suptitle(
        "Meta-agent improver — 21 iterations of prompt optimization",
        fontsize=18,
        fontweight="700",
        color=NAVY,
        x=0.05,
        ha="left",
        y=0.97,
    )
    ax.set_title(
        "Pass rate on 20-task search set. Two proposer crashes (evo_002, evo_003) omitted.",
        fontsize=12,
        color=MUTED,
        loc="left",
        pad=16,
    )

    # Legend as colored dots in text
    legend_handles = [
        mpatches.Patch(color=GREEN, label="New best"),
        mpatches.Patch(color=RED, label="Regression"),
        mpatches.Patch(color=BLUE, label="Iteration"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        frameon=False,
        fontsize=10,
        labelcolor=NAVY,
    )

    # Stamp cost in corner
    fig.text(
        0.95, 0.02,
        "21 iterations  ·  $21 API  ·  +$5 GPU  ·  github.com/abhid1234/meta-agent-improver",
        fontsize=9, color=MUTED, ha="right",
    )

    plt.subplots_adjust(top=0.85, bottom=0.1, left=0.07, right=0.97)
    plt.savefig(OUT_PATH, facecolor=WARM_WHITE, edgecolor="none", bbox_inches="tight", dpi=140)
    plt.close()
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
