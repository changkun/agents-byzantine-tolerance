"""Analysis for Experiment 07 — Adversarial Debate (07a)."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "results" / "07_debate" / "smoke.jsonl"


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def fmt(v, pct=False):
    if v is None:
        return "—"
    return f"{v * 100:.0f}%" if pct else f"{v:.2f}"


def cell_metrics(records: list[dict]) -> dict:
    if not records:
        return {"n": 0}
    n = len(records)
    return {
        "n": n,
        "soundness": sum(1 for r in records if r["soundness"]) / n,
        "critic_found_bug": (
            sum(1 for r in records if r["critic_found_bug"])
            / max(1, sum(1 for r in records if r["ground_truth"]["has_bug"]))
        ),
        "stake_rate": sum(1 for r in records if r["stake_index"] != -1) / n,
    }


def write_summary(records: list[dict], out_path: Path) -> None:
    lines = ["# Experiment 07 — Adversarial Debate (07a, bug detection)", ""]
    lines.append(f"Total debates: {len(records)}")
    lines.append("")

    lines.append("## Overall")
    lines.append("")
    lines.append(_table([("all", cell_metrics(records))]))
    lines.append("")

    lines.append("## By honesty (H1, H6)")
    lines.append("")
    by_h = defaultdict(list)
    for r in records:
        by_h[r["honesty"]].append(r)
    rows = [(h, cell_metrics(by_h[h])) for h in sorted(by_h)]
    lines.append(_table(rows))
    lines.append("")
    lines.append(
        "*H1: debate beats voting at equal compute on both-honest. "
        "H6: c-lazy soundness should drop sharply.*"
    )
    lines.append("")

    lines.append("## By roles (asymmetry)")
    lines.append("")
    by_r = defaultdict(list)
    for r in records:
        by_r[r["roles"]].append(r)
    rows = [(rl, cell_metrics(by_r[rl])) for rl in sorted(by_r)]
    lines.append(_table(rows))
    lines.append("")

    lines.append("## By snippet category")
    lines.append("")
    by_c = defaultdict(list)
    for r in records:
        by_c[r["category"]].append(r)
    rows = [(c, cell_metrics(by_c[c])) for c in sorted(by_c)]
    lines.append(_table(rows))
    lines.append("")

    out_path.write_text("\n".join(lines))


def _table(rows: list[tuple[str, dict]]) -> str:
    header = "| group | debates | soundness | critic_found_bug | stake_rate |"
    sep = "|-------|--------:|----------:|-----------------:|----------:|"
    out = [header, sep]
    for name, m in rows:
        out.append(
            f"| {name} | {m.get('n', 0)} | "
            f"{fmt(m.get('soundness'), pct=True)} | "
            f"{fmt(m.get('critic_found_bug'), pct=True)} | "
            f"{fmt(m.get('stake_rate'), pct=True)} |"
        )
    return "\n".join(out)


def try_plots(records: list[dict], plot_dir: Path) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    plot_dir.mkdir(parents=True, exist_ok=True)
    by_h = defaultdict(list)
    for r in records:
        by_h[r["honesty"]].append(r)
    hs = sorted(by_h)
    if not hs:
        return True
    fig, ax = plt.subplots(figsize=(6, 4))
    soundness = [cell_metrics(by_h[h])["soundness"] for h in hs]
    cfb = [cell_metrics(by_h[h])["critic_found_bug"] for h in hs]
    width = 0.35
    xs = list(range(len(hs)))
    ax.bar([x - width / 2 for x in xs], soundness, width=width, label="soundness")
    ax.bar([x + width / 2 for x in xs], cfb, width=width, label="critic_found_bug")
    ax.set_xticks(xs)
    ax.set_xticklabels(hs)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("rate")
    ax.set_title("Debate soundness vs critic-found-bug, by honesty")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(plot_dir / "soundness_by_honesty.png", dpi=140)
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
