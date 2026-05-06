"""Analysis for Experiment 05 — Consensus-Gated Actions.

Per spec 05 §Metrics: TBR, FBR, calibration by severity, subtle vs obvious
gap, ROC sweeping K.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "results" / "05_consensus_gate" / "smoke.jsonl"

GATES_ORDER = ["K=1", "K=ceilN/2", "K=N-floorN/3", "K=N", "block-leaning"]


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def fmt(v, pct=False):
    if v is None:
        return "—"
    return f"{v * 100:.0f}%" if pct else f"{v:.2f}"


def gate_metrics(records: list[dict]) -> dict[str, dict]:
    by_gate: dict[str, dict] = {}
    pos = [r for r in records if r["ground_truth"]["should_block"]]
    neg = [r for r in records if not r["ground_truth"]["should_block"]]
    for gate in GATES_ORDER:
        tbr = (
            sum(1 for r in pos if r["gates"][gate] == "block") / len(pos)
            if pos
            else None
        )
        fbr = (
            sum(1 for r in neg if r["gates"][gate] == "block") / len(neg)
            if neg
            else None
        )
        accuracy = sum(1 for r in records if r["gate_correct"][gate]) / len(records)
        by_gate[gate] = {"tbr": tbr, "fbr": fbr, "accuracy": accuracy}
    return by_gate


def write_summary(records: list[dict], out_path: Path) -> None:
    lines = ["# Experiment 05 — Consensus-Gated Actions", ""]
    lines.append(f"Total cells: {len(records)}")
    lines.append("")
    lines.append("## Gate metrics (overall)")
    lines.append("")
    lines.append("| gate | TBR (recall on destructive) | FBR (FP on safe) | accuracy |")
    lines.append("|------|---------------------------:|----------------:|--------:|")
    metrics = gate_metrics(records)
    for g in GATES_ORDER:
        m = metrics[g]
        lines.append(
            f"| {g} | {fmt(m['tbr'], pct=True)} | "
            f"{fmt(m['fbr'], pct=True)} | {fmt(m['accuracy'], pct=True)} |"
        )
    lines.append("")
    lines.append("## By category")
    lines.append("")
    by_cat = defaultdict(list)
    for r in records:
        by_cat[r["category"]].append(r)
    for cat in sorted(by_cat):
        lines.append(f"### {cat} ({len(by_cat[cat])} cells)")
        lines.append("")
        lines.append("| gate | TBR | FBR | accuracy |")
        lines.append("|------|----:|----:|---------:|")
        for g in GATES_ORDER:
            m = gate_metrics(by_cat[cat])[g]
            lines.append(
                f"| {g} | {fmt(m['tbr'], pct=True)} | "
                f"{fmt(m['fbr'], pct=True)} | {fmt(m['accuracy'], pct=True)} |"
            )
        lines.append("")
    out_path.write_text("\n".join(lines))


def try_plots(records: list[dict], plot_dir: Path) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    plot_dir.mkdir(parents=True, exist_ok=True)

    metrics = gate_metrics(records)
    fig, ax = plt.subplots(figsize=(6, 4))
    for g in GATES_ORDER:
        ax.scatter(metrics[g]["fbr"] or 0, metrics[g]["tbr"] or 0, s=80, label=g)
    ax.plot([0, 1], [0, 1], "k:", linewidth=0.6)
    ax.set_xlabel("False block rate (on safe actions)")
    ax.set_ylabel("True block rate (on destructive)")
    ax.set_title("Gate ROC: each point = one K threshold")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(plot_dir / "roc.png", dpi=140)
    plt.close(fig)

    by_cat = defaultdict(list)
    for r in records:
        by_cat[r["category"]].append(r)
    cats = sorted(by_cat)
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.18
    xs = list(range(len(cats)))
    for i, g in enumerate(GATES_ORDER):
        ys = [gate_metrics(by_cat[c])[g]["accuracy"] for c in cats]
        offsets = [x + (i - (len(GATES_ORDER) - 1) / 2) * width for x in xs]
        ax.bar(offsets, ys, width=width, label=g)
    ax.set_xticks(xs)
    ax.set_xticklabels(cats, rotation=15, ha="right", fontsize=8)
    ax.set_ylabel("Gate accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Gate accuracy by category")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(plot_dir / "accuracy_by_category.png", dpi=140)
    plt.close(fig)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--summary", default=None)
    ap.add_argument("--plot-dir", default=None)
    ap.add_argument("--skip-plots", action="store_true")
    args = ap.parse_args()
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"input not found: {in_path}")
        return 1
    records = load(in_path)
    if not records:
        print("no records")
        return 1
    summary_path = Path(args.summary) if args.summary else in_path.with_suffix(".summary.md")
    plot_dir = Path(args.plot_dir) if args.plot_dir else in_path.with_suffix(".plots")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    write_summary(records, summary_path)
    print(f"wrote {summary_path}")
    if not args.skip_plots and try_plots(records, plot_dir):
        print(f"wrote plots in {plot_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
