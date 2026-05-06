"""Analysis for Experiment 04 — Ambiguous-Spec Detection.

Per spec 04 §Metrics:
  1. Per-decision disagreement gap (ambiguous - unambiguous, per decision).
  2. AUC of disagreement-as-ambiguity classifier.
  3. Precision @ top-K disagreement.
  4. Ensemble-size effect.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "results" / "04_ambiguous_spec" / "smoke.jsonl"


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def fmt(v, pct=False):
    if v is None:
        return "—"
    return f"{v * 100:.0f}%" if pct else f"{v:.2f}"


def auc(labels: list[bool], scores: list[float | None]) -> float | None:
    """Simple ROC AUC. Treats None scores as ties at 0."""
    pairs = [
        (s if s is not None else 0.0, bool(label))
        for s, label in zip(scores, labels)
    ]
    pos = [s for s, lbl in pairs if lbl]
    neg = [s for s, lbl in pairs if not lbl]
    if not pos or not neg:
        return None
    wins = ties = 0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    return (wins + 0.5 * ties) / (len(pos) * len(neg))


def write_summary(records: list[dict], out_path: Path) -> None:
    lines: list[str] = ["# Experiment 04 — Ambiguous-Spec Detection", ""]
    lines.append(f"Total cells: {len(records)}")
    lines.append("")

    # Aggregate per (pair, variant, decision_key) — average disagreement
    # across trials/compositions.
    bucket: dict[tuple, list[float | None]] = defaultdict(list)
    in_set: dict[tuple, bool] = {}
    for r in records:
        for k, d in r["per_decision"].items():
            bucket[(r["pair_id"], r["variant"], k)].append(d["score"])
            in_set[(r["pair_id"], r["variant"], k)] = d["in_ambiguity_set"]

    by_decision = {}
    for key, vals in bucket.items():
        valid = [v for v in vals if v is not None]
        avg = sum(valid) / len(valid) if valid else None
        by_decision[key] = avg

    lines.append("## Per-decision disagreement (mean across trials/compositions)")
    lines.append("")
    lines.append("| pair | variant | decision | mean_disagreement | in_ambiguity_set |")
    lines.append("|------|---------|----------|------------------:|:----------------:|")
    for key in sorted(by_decision):
        pid, v, dk = key
        marker = "✓" if in_set[key] else ""
        lines.append(
            f"| {pid} | {v} | {dk} | {fmt(by_decision[key])} | {marker} |"
        )
    lines.append("")

    # H1: per-decision gap (ambiguous - unambiguous), averaged across pairs/decisions
    pair_keys = {(p, k) for (p, _, k) in by_decision}
    gaps = []
    for (p, dk) in sorted(pair_keys):
        a = by_decision.get((p, "ambiguous", dk))
        u = by_decision.get((p, "unambiguous", dk))
        if a is not None and u is not None:
            gaps.append((p, dk, a - u))
    lines.append("## H1: per-decision disagreement gap (ambiguous − unambiguous)")
    lines.append("")
    lines.append("| pair | decision | gap |")
    lines.append("|------|----------|----:|")
    for p, dk, g in gaps:
        lines.append(f"| {p} | {dk} | {fmt(g)} |")
    if gaps:
        mean_gap = sum(g for _, _, g in gaps) / len(gaps)
        lines.append("")
        lines.append(f"Mean gap: **{fmt(mean_gap)}** (positive = ambiguity → disagreement)")
    lines.append("")

    # H2: ambiguity classifier AUC (treating per-(spec,decision) score as predictor,
    # in_ambiguity_set as label).
    labels = []
    scores = []
    for key, score in by_decision.items():
        labels.append(in_set[key])
        scores.append(score)
    a = auc(labels, scores)
    lines.append("## H2: AUC of disagreement-as-ambiguity classifier")
    lines.append("")
    lines.append(f"- AUC: **{fmt(a)}**  (target ≥ 0.80 for deployable diagnostic)")
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

    # Heatmap: rows = decisions, cols = (pair, variant), cell = mean disagreement.
    bucket: dict[tuple, list[float]] = defaultdict(list)
    for r in records:
        for k, d in r["per_decision"].items():
            if d["score"] is not None:
                bucket[(r["pair_id"], r["variant"], k)].append(d["score"])
    keys = sorted(bucket)
    if not keys:
        return True
    pairs_variants = sorted({(p, v) for (p, v, _) in keys})
    decisions = sorted({k for (_, _, k) in keys})

    matrix = []
    for dk in decisions:
        row = []
        for (p, v) in pairs_variants:
            vals = bucket.get((p, v, dk), [])
            row.append(sum(vals) / len(vals) if vals else 0.0)
        matrix.append(row)

    fig, ax = plt.subplots(
        figsize=(max(6, len(pairs_variants) * 1.5), max(3, len(decisions) * 0.4))
    )
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_xticks(range(len(pairs_variants)))
    ax.set_xticklabels([f"{p}\n{v}" for (p, v) in pairs_variants], fontsize=8)
    ax.set_yticks(range(len(decisions)))
    ax.set_yticklabels(decisions, fontsize=8)
    ax.set_title("Per-decision disagreement heatmap")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(plot_dir / "heatmap.png", dpi=140)
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
