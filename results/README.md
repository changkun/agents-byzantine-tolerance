# Results

Each experiment owns a subdirectory here. Subdirectories contain raw run
records (JSONL), analysis output (Markdown summary), plots (PNG), and a
README.md that describes what was run and what to take away from it.

Each experiment-level README states the run scale (smoke vs full), the
date, the resolved git SHA of the target repo (where applicable), and
the headline finding from that run. The raw JSONL is the source of
truth — anyone can re-run analysis on it without re-spending the agent
invocations.

## Index

| Spec | Directory | Status | Headline |
|------|-----------|--------|----------|
| [01 Verifiable consensus](../specs/01-verifiable-consensus.md) | [01_verifiable_consensus/](01_verifiable_consensus/) | smoke ✅ | Unanimous → correct in 2/2 smoke cells (N=3) |
| [02 Byzantine injection](../specs/02-byzantine-injection.md)   | [02_byzantine_injection/](02_byzantine_injection/) | smoke ✅ | Strong-lie efficacy collapsed at f=2 — agents overruled the injection |
| [03 Bug detection](../specs/03-bug-detection-consensus.md)     | [03_bug_detection/](03_bug_detection/) | smoke ✅ | 4/4 unanimous-correct on N=3 across all categories (bank too small to test H3) |
| [04 Ambiguous spec](../specs/04-ambiguous-spec-detection.md)   | [04_ambiguous_spec/](04_ambiguous_spec/) | smoke ✅ | AUC 0.86 (1 pair, N=3) — disagreement tracks ambiguity, but tiny sample |
| [05 Consensus gate](../specs/05-consensus-gated-actions.md)    | [05_consensus_gate/](05_consensus_gate/) | smoke ✅ | 4/4 correct on N=3, but every cell unanimous — gates indistinguishable here |
| [06 Cascading hallucination](../specs/06-cascading-hallucination.md) | — | ⏳ pending | — |
| [07 Adversarial debate](../specs/07-adversarial-debate.md)     | — | ⏳ pending | — |

## File conventions

```
<spec>_<name>/
  README.md              # Run config, observations, what to look at next.
  smoke.jsonl            # Raw records from the smoke run (committed).
  smoke.summary.md       # Markdown analysis output.
  smoke.plots/           # Plots (PNG).
  full.jsonl             # Raw records from a full run (when applicable).
  full.summary.md
  full.plots/
```

`smoke` is the small-scale end-to-end check — typically a few cells, single
composition, single trial. It exists to prove the pipeline runs and to
provide a small but real sample for the analysis. `full` is the spec-prescribed
sweep; it's expensive and not always present.

## Reproducing a run

Every experiment has a `--smoke` flag and is otherwise driven by CLI args.
The exact command for the run that produced any committed file is recorded
at the top of that experiment's README.md. To replay:

```bash
uv sync
uv run python experiments/<spec>.py --smoke   # or whatever the README states
uv run python analysis/<spec>.py --input results/<dir>/<file>.jsonl
```
