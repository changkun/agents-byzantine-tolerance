# agents-byzantine-tolerance

An experiment exploring the structural equivalence between Byzantine fault tolerance in distributed systems and failure modes in multi-agent LLM systems.

**Motivation:** Multi-agent LLM systems fail at 41-86.7% rates in production, with coordination failures accounting for 36.94% of failures. LLM hallucinations are structurally identical to Byzantine nodes sending contradictory messages to different peers — yet the agent community has largely overlooked 40 years of BFT theory that directly applies.

Full writeup: https://changkun.de/blog/ideas/agents-byzantine-tolerance/

## Setup

Agents are real coding agents in headless mode — not raw model API calls — so we observe realistic agentic failure modes (planning loops, tool use, hallucinations, etc.).

- **Claude agents**: `claude -p --output-format json --permission-mode bypassPermissions`
- **Codex agents**: `codex exec --sandbox read-only --skip-git-repo-check --ephemeral`

Each agent runs in its own ephemeral working directory so they cannot see or stomp on each other's state during a round.

Requirements: `claude` and `codex` CLIs on PATH, both authenticated.

## Approaches

1. **Consensus-Gated Autonomous Actions** — High-risk decisions require multi-agent agreement before execution; low-risk actions proceed freely.
2. **Testing as Distributed Consensus** — Multiple independent agents must agree on test pass/fail; disagreement indicates specification ambiguity.
3. **Partial Agreement Maps** — Structured views showing where agents converge vs. diverge, treating disagreement as the most informative signal.

## One-time setup

```bash
uv sync                                              # install deps (pyyaml, optional matplotlib)
```

The runners write JSONL records into `results/<spec>/<tag>.jsonl` (default
`tag = smoke` if `--smoke` else `full`); the analysis scripts emit
`<basename>.summary.md` and a `<basename>.plots/` dir alongside. Each
experiment's `results/<spec>/README.md` documents the run record, observed
outcome, and how to extend.

Spec list, status table, and outcome links: [`specs/README.md`](specs/README.md).
Cross-experiment index: [`results/README.md`](results/README.md).

## Experiments

Each command pair below is `smoke → analyze`. Drop `--smoke` for the full
spec-prescribed sweep; use `--resume` to continue an interrupted run.

### 01 — Verifiable consensus

Spec: [`specs/01-verifiable-consensus.md`](specs/01-verifiable-consensus.md).
N agents answer questions with mechanical ground truth against a pinned target
repo (`mvdan/sh@v3.10.0`).

```bash
uv run python experiments/01_compute_ground_truth.py        # clone target, compute GT
uv run python experiments/01_verifiable_consensus.py --smoke
uv run python analysis/01_plot.py --input results/01_verifiable_consensus/smoke.jsonl
```

### 02 — Byzantine injection

Spec: [`specs/02-byzantine-injection.md`](specs/02-byzantine-injection.md).
Reuses the spec-01 question bank; designated Byzantine agents get an
injection-augmented system prompt (`strong-lie` or `subtle-misdirection`).
Records track injection efficacy separately from contamination.

```bash
uv run python experiments/02_byzantine_injection.py --smoke
uv run python analysis/02_plot.py --input results/02_byzantine_injection/smoke.jsonl
```

### 03 — Bug-detection consensus

Spec: [`specs/03-bug-detection-consensus.md`](specs/03-bug-detection-consensus.md).
N agents review a code snippet against a spec and return
`{has_bug, lines, kind}`. Bank in [`experiments/snippets.yaml`](experiments/snippets.yaml).

```bash
uv run python experiments/03_bug_detection.py --smoke
uv run python analysis/03_plot.py --input results/03_bug_detection/smoke.jsonl
```

### 04 — Ambiguous-spec detection

Spec: [`specs/04-ambiguous-spec-detection.md`](specs/04-ambiguous-spec-detection.md).
Paired specs (unambiguous + ambiguous version of the same domain). Per-decision
disagreement is scored as entropy (categorical) or coefficient of variation
(numeric); analysis computes the AUC of disagreement-as-ambiguity classifier.

```bash
uv run python experiments/04_ambiguous_spec.py --smoke
uv run python analysis/04_plot.py --input results/04_ambiguous_spec/smoke.jsonl
```

### 05 — Consensus-gated actions

Spec: [`specs/05-consensus-gated-actions.md`](specs/05-consensus-gated-actions.md).
Each agent returns `{decision: approve|block, severity_guess, reason}`. From a
single fan-out we evaluate `K=1`, `⌈N/2⌉`, `N-⌊N/3⌋`, `N`, and a
block-leaning variant.

```bash
uv run python experiments/05_consensus_gate.py --smoke
uv run python analysis/05_plot.py --input results/05_consensus_gate/smoke.jsonl
```

### 06 — Cascading hallucination

Spec: [`specs/06-cascading-hallucination.md`](specs/06-cascading-hallucination.md).
Sequential K-stage pipeline. `--conditions` selects clean vs. seeded-subtle
vs. seeded-obvious; `--visibilities` selects first-only vs. every-stage source
visibility.

```bash
uv run python experiments/06_cascading.py --smoke
uv run python analysis/06_plot.py --input results/06_cascading/smoke.jsonl
```

### 07 — Adversarial debate (07a bug-detection variant)

Spec: [`specs/07-adversarial-debate.md`](specs/07-adversarial-debate.md).
Fixed 4-round debate (R1 propose, R2 attack, R3 defend, R4 stake) on snippets
from spec 03's bank. Deterministic leaf-judge inspects only the critic's R4
stake. Honesty knob: `both | p-byzantine | c-lazy`. Roles knob:
`<claude|codex>_p_<claude|codex>_c`.

```bash
uv run python experiments/07_debate.py --smoke
uv run python analysis/07_plot.py --input results/07_debate/smoke.jsonl

# The actually-interesting test (forces the critic to do real work):
uv run python experiments/07_debate.py --honesty p-byzantine --snippet-ids S01,S02 --trials 3
```

## References

- Berdoz et al., "Can AI Agents Agree?" — [arXiv:2603.01213](https://arxiv.org/abs/2603.01213)
- Zheng et al., CP-WBFT consensus — [arXiv:2511.10400](https://arxiv.org/abs/2511.10400)
- MAST failure taxonomy — [OpenReview](https://openreview.net/pdf?id=wM521FqPvI)
- DecentLLMs leaderless consensus — [arXiv:2507.14928](https://arxiv.org/abs/2507.14928)
- AgentsNet benchmark — [arXiv:2507.08616](https://arxiv.org/abs/2507.08616)
- FREE-MAD premature convergence — [arXiv:2509.11035](https://arxiv.org/abs/2509.11035)
