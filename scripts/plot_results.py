#!/usr/bin/env python3
"""Plot released judge-family and creative-selection results."""
import json
import statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
BG, INK, MUTED, GRID = "#f7f8f5", "#182d32", "#577078", "#dce5e3"
TEAL, ORANGE, PURPLE = "#087e82", "#cf6a35", "#795aa8"
CREATIVE_MODELS = ["deepseek/deepseek-chat-v3.1", "google/gemini-2.5-flash"]
CREATIVE = CREATIVE_MODELS + ["anthropic/claude-sonnet-5"]
NAMES = {CREATIVE_MODELS[0]: "DeepSeek V3.1", CREATIVE_MODELS[1]: "Gemini 2.5 Flash",
         "anthropic/claude-sonnet-5": "Claude Sonnet*", "anthropic/claude-sonnet-4.5": "Claude Sonnet 4.5",
         "openai/gpt-4o": "GPT-4o", "deepseek/deepseek-v3.1": "DeepSeek V3.1",
         "cncl-penn-state/crpo-llama-3.1-8b-instruct-nov": "CrPO-Llama 8B"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "figure.facecolor": BG,
    "axes.facecolor": BG, "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": INK, "svg.fonttype": "none", "svg.hashsalt": "llm-judge-reliability",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.spines.bottom": False, "axes.axisbelow": True})


def save(fig, name):
    for ext in ("png", "svg"):
        path = ROOT / "figures" / f"{name}.{ext}"
        fig.savefig(path, dpi=170, facecolor=BG, **({"metadata": {"Date": None}} if ext == "svg" else {}))
        if ext == "svg":
            path.write_text("\n".join(x.rstrip() for x in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def heading(fig, title, sub):
    fig.text(.05, .94, title, size=21, weight="bold")
    fig.text(.05, .875, sub, size=10.5, color=MUTED)


def family(s):
    rows = s["jury"]["matrix"]
    judges = sorted({r["judge"] for r in rows}); gens = sorted({r["generator"] for r in rows})
    fig = plt.figure(figsize=(12, 5.4)); ax = fig.add_axes([.20, .29, .72, .43])
    heading(fig, "TRIZ preference differs by judge and generator", "Each pair contains a TRIZ and a control answer from the same generator · all valid presentations")
    matrix = [[next(r["triz_rate"] for r in rows if r["judge"] == j and r["generator"] == g) for g in gens] for j in judges]
    ax.imshow(matrix, vmin=.4, vmax=.8, cmap="BuGn", aspect="auto")
    for i, judge in enumerate(judges):
        for k, gen in enumerate(gens):
            ax.text(k, i, f"{matrix[i][k]:.1%}", ha="center", va="center", size=13, weight="bold", color="white" if matrix[i][k] > .65 else INK)
            if judge.split("/")[0] == gen.split("/")[0]:
                ax.add_patch(Rectangle((k-.5, i-.5), 1, 1, fill=False, edgecolor=ORANGE, lw=2.5))
    ax.set_yticks(range(len(judges)), [NAMES[j] for j in judges]); ax.set_xticks(range(len(gens)), [NAMES[g].replace(" ", "\n", 1) for g in gens], size=9)
    ax.set_ylabel("Judge"); ax.set_xlabel("Generator", labelpad=8)
    r = s["jury"]["family_interaction"]
    fig.text(.05, .105, f"Matched pairs: own-family judges choose TRIZ {r['mean']*100:+.2f} pp more often (95% case bootstrap [{r['ci_low']*100:.2f}, {r['ci_high']*100:.2f}]).", size=10)
    fig.text(.05, .05, "Orange: same family. This is a treatment-preference interaction; these pairs cannot identify own-output vs other-output bias.", size=9, color=MUTED)
    save(fig, "family")


def creative(s):
    c = s["creative"]
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.3))
    fig.subplots_adjust(left=.17, right=.97, bottom=.21, top=.70, wspace=.22)
    heading(fig, "Creative rankings change under reordering", "One slate of 40 Mars-boot concepts · 5 permutations × 10 requested repeats · temperature = 0")
    for i, model in enumerate(CREATIVE):
        rs = {r["comparison"]: r for r in c["resolution"] if r["judge"] == model}
        y = 2-i; a, b = rs["same_order"]["kendall_tau"], rs["cross_order"]["kendall_tau"]
        axs[0].plot([b, a], [y, y], lw=4, color=GRID)
        axs[0].scatter(a, y, color=TEAL, s=65); axs[0].scatter(b, y, color=ORANGE, s=65)
        axs[0].text(a, y+.16, f"{a:.3f}", ha="center", size=9, color=TEAL)
        axs[0].text(b, y-.27, f"{b:.3f}", ha="center", size=9, color=ORANGE)
        for mode, marker, ls in [("same_order", "o", "-"), ("cross_order", "s", "--")]:
            vals = [rs[mode][f"Q{q}_jaccard"] for q in range(1, 5)]
            if model == CREATIVE_MODELS[1]:
                axs[1].plot(range(1, 5), vals, marker=marker, ls=ls, color=TEAL if mode == "same_order" else ORANGE, label=mode.replace("_", " "))
    axs[0].set_yticks(range(3), [NAMES[m] for m in CREATIVE[::-1]])
    axs[0].set_xlim(-.12, 1.10); axs[0].set_ylim(-.55, 2.45); axs[0].grid(axis="x", color=GRID)
    axs[0].set_xlabel("Kendall tau of full ranking")
    axs[1].set_title("Gemini quartile membership", loc="left", size=11)
    axs[1].set_xticks(range(1, 5), ["Q1", "Q2", "Q3", "Q4"]); axs[1].set_ylim(0, 1.07)
    axs[1].set_ylabel("Raw Jaccard"); axs[1].grid(axis="y", color=GRID); axs[1].legend(frameon=False)
    fig.text(.05, .09, "Teal: same order. Orange: different orders. Gemini repeats exactly at a fixed order but changes under permutation.", size=9, color=MUTED)
    fig.text(.05, .04, "*Claude logged ID: anthropic/claude-sonnet-5; 46/50 complete rankings. Other models: 50/50. Calls and pairs overlap.", size=9, color=MUTED)
    save(fig, "creative_rankings")


def elimination(s):
    c = s["creative"]; fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
    fig.subplots_adjust(left=.09, right=.97, bottom=.23, top=.70, wspace=.26)
    heading(fig, "Scoring changes removal consistency", "Creative-selection follow-ups · 15 overlapping sets and up to 5 sessions per model · one problem")
    for i, (condition, color, marker) in enumerate([("rank", ORANGE, "o"), ("score_batch", TEAL, "s")]):
        for j, model in enumerate(CREATIVE_MODELS):
            rs = [r for r in c["permutations"] if r["judge"] == model and r["condition"] == condition]
            x = j + (i-.5)*.22
            axs[0].scatter([x+(k-7)*.006 for k in range(len(rs))], [r["distinct_removals"] for r in rs], s=28,
                           color=color, marker=marker, alpha=.5)
            axs[0].plot([x-.06, x+.06], [st.mean(r["distinct_removals"] for r in rs)]*2, color=INK, lw=2)
    axs[0].set_xticks(range(2), ["DeepSeek V3.1", "Gemini 2.5 Flash"])
    axs[0].set_ylim(0, 10.7); axs[0].set_ylabel("Distinct removals over 10 attempted permutations")
    axs[0].grid(axis="y", color=GRID)
    for j, model in enumerate(CREATIVE_MODELS):
        good = [r for r in c["sessions"] if r["judge"] == model and r["complete"]]
        sessions = sorted({r["session"] for r in good if r["condition"] == "rank"} & {r["session"] for r in good if r["condition"] == "score_batch"})
        for k, sid in enumerate(sessions):
            vals = [next(r["removal_overlap_fraction"] for r in good if r["session"] == sid and r["condition"] == condition) for condition in ("rank", "score_batch")]
            xs = [j-.12+(k-2)*.012, j+.12+(k-2)*.012]
            axs[1].plot(xs, vals, color=GRID, lw=1.6)
            axs[1].scatter(xs[0], vals[0], color=ORANGE, marker="o", s=40, zorder=3)
            axs[1].scatter(xs[1], vals[1], color=TEAL, marker="s", s=40, zorder=3)
        axs[1].text(j, 1.02, f"{len(sessions)} paired sessions", ha="center", size=9, color=MUTED)
    axs[1].set_xticks(range(2), ["DeepSeek V3.1", "Gemini 2.5 Flash"])
    axs[1].set_ylim(0, 1.12); axs[1].yaxis.set_major_formatter(PercentFormatter(1)); axs[1].grid(axis="y", color=GRID)
    axs[1].set_ylabel("Shared removals / 10 across two sessions")
    fig.legend(handles=[Line2D([], [], marker="o", color=ORANGE, ls="", label="Ranking"), Line2D([], [], marker="s", color=TEAL, ls="", label="Batch scoring")], loc="lower center", bbox_to_anchor=(.5, .10), ncol=2, frameon=False)
    fig.text(.05, .045, "One Gemini ranking session is incomplete and excluded. Dots reuse one problem; the figure makes no across-task inference.", size=9, color=MUTED)
    save(fig, "elimination")

if __name__ == "__main__":
    summary = json.loads((ROOT / "results/summary.json").read_text())
    for draw in (family, creative, elimination):
        draw(summary)
    print("Rendered three result charts as PNG and SVG.")
