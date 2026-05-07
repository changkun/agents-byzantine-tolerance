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

## Architectures under test

The thirteen specs split across three multi-agent patterns. Each pattern is
what the spec hypothesises about — the harness diagram below it is shared
across all of them.

### Parallel consensus (specs 01, 03, 04, 05; 02 is the Byzantine variant)

N agents answer the *same* prompt independently in isolated workdirs; an
aggregator clusters the parsed values and scores correctness against ground
truth. Disagreement *between* agents is the structural signal.

```text
                 ┌──────────────────────────┐
                 │ task: question / spec /  │
                 │ snippet / action         │
                 └──────────────┬───────────┘
                                │  (same user prompt to each)
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   ┌─────────┐             ┌─────────┐             ┌─────────┐
   │ agent 1 │             │ agent 2 │     ...     │ agent N │
   │ isolated│             │ isolated│             │ isolated│
   │ workdir │             │ workdir │             │ workdir │
   └────┬────┘             └────┬────┘             └────┬────┘
        │                       │                       │
        ▼                       ▼                       ▼
       "0"                     "0"                     "7"
         \                      |                      /
          └────────────┬────────┴────────┬────────────┘
                       ▼                 ▼
            ┌─────────────────────────────────────┐
            │ aggregator: parse → cluster → score │
            │ • unanimous?  majority?  fragmented?│
            │ • correct vs ground truth?          │
            └─────────────────────────────────────┘

Spec 02 (Byzantine injection) is the same shape, but f of N agents
get a private extra system-prompt segment that the others never see:

   honest:    sys = HONEST_PROMPT
   Byzantine: sys = HONEST_PROMPT + "<strong-lie or subtle-misdirection>"
```

### Sequential chain (spec 06)

K stages run one after another. Each stage's *user* prompt contains the prior
stage's output (and optionally the original source). This is where Byzantine
errors *amplify* rather than average out.

```text
   source doc ─► [stage 0: parser] ─► output_0 ─┐
                                                │
                     ▼  (or seed override)      │
                 [stage 1: analyst]─► output_1 ─┤
                                                │
                     ▼                          │
                 [stage 2: writer] ─► output_2 ─┴─► end-to-end check

   source visibility flag:
     first-only   – only stage 0 sees `source`; later stages see only the
                    previous stage's output (the propagation case).
     every-stage  – every stage also sees `source` (tests re-grounding).

   seed conditions:
     clean           – run all stages naturally; measure spontaneous error rate.
     seeded-subtle   – replace stage k's output with a plausible-but-wrong value.
     seeded-obvious  – replace with a flagrantly wrong value.
```

### Adversarial dialectic (specs 07–13)

Two agents (Proposer, Critic) play a fixed 4-round game; an *external* judge
inspects only the critic's R4 stake. Soundness no longer needs honest
majority — it needs one honest player plus a calibrated leaf judge. Specs
08–13 keep this protocol shape and vary one axis each: compute asymmetry
between players (08), round count and recursion (09), temperature (10),
leaf format narrowness (11), Prover-Estimator replacing the Critic role
(12), and judge query budget vs. snippet complexity (13). Their motivating
papers are listed in [References](#references).

```text
       snippet + spec
            │
            ▼
   ┌──────────────────────────────────┐
   │ R1: Proposer  →  claim           │  "no_bug" / "bug at L kind=K"
   └─────────────┬────────────────────┘
                 ▼
   ┌──────────────────────────────────┐
   │ R2: Critic    →  attacks[]       │  ≤ 3 concrete inputs+violations
   └─────────────┬────────────────────┘
                 ▼
   ┌──────────────────────────────────┐
   │ R3: Proposer  →  responses[]     │  concede or rebut each
   └─────────────┬────────────────────┘
                 ▼
   ┌──────────────────────────────────┐
   │ R4: Critic    →  stake (one      │  pick one unresolved attack
   │                  attack)         │
   └─────────────┬────────────────────┘
                 ▼
   ┌──────────────────────────────────┐
   │ deterministic judge sees ONLY    │  cost-of-attention: judge reads
   │ the R4 stake:                    │  one leaf, not the whole transcript
   │   line±1 OR kind match → C_wins  │
   │   else                 → P_wins  │
   └──────────────────────────────────┘
```

### Common harness (all specs)

Every agent invocation goes through the same plumbing. This is what makes
results comparable across architectures.

```text
   _repo_cache/<repo>@<sha>/                  ◄── git clone, ref-pinned
            │
            │ shutil.copytree (APFS clonefile when available)
            ▼
   /tmp/agents-bft/<agent_id>-<uuid>/         ◄── fresh per-invocation workdir
            │
            │ env scrubbed: ANTHROPIC_API_KEY, CLAUDE_CODE_*, OPENAI_*
            │ (so the child agent uses its own credentials, not the parent's)
            ▼
   `claude -p` or `codex exec`                ◄── real coding agents,
            │                                    not raw model calls
            │ stdout → strict-int / JSON parser
            ▼
   per-cell record → results/<spec>/<tag>.jsonl   ◄── flushed every cell;
                                                     resumable via --resume
```

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

### 07 — Adversarial debate

Spec: [`specs/07-adversarial-debate.md`](specs/07-adversarial-debate.md).
The spec defines three sub-tasks:

- **07a** — bug detection (debate variant of spec 03). Deterministic
  leaf-judge: critic's R4 stake is checked against the snippet's
  ground-truth bug line / kind label.
- **07b** — action gating (debate variant of spec 05). LLM-judge or
  human-judge; ROC head-to-head against the K-of-N gate at equal compute.
- **07c** — ambiguity localization (debate variant of spec 04). Critic's
  staked leaf is compared against top-K disagreement from voting.

**Implementation status: only 07a is built.** Fixed 4-round debate
(R1 propose, R2 attack, R3 defend, R4 stake) on snippets from spec 03's
bank. Honesty knob: `both | p-byzantine | c-lazy`. Roles knob:
`<claude|codex>_p_<claude|codex>_c`. 07b and 07c reuse the action and spec
banks from 05/04 and need a different leaf schema + a non-deterministic
judge; not yet implemented.

```bash
# 07a only:
uv run python experiments/07_debate.py --smoke
uv run python analysis/07_plot.py --input results/07_debate/smoke.jsonl

# The actually-interesting 07a test (forces the critic to do real work):
uv run python experiments/07_debate.py --honesty p-byzantine --snippet-ids S01,S02 --trials 3
```

### 08–13 — Debate extensions (spec only)

The doubly-efficient-debate batch is currently spec-only — no runners yet.
Per-spec status and descriptions: [`specs/README.md`](specs/README.md#status).
Recommended execution order once implementations land:
**10 → 11 → 12 → 08 → 09 → 13** ([rationale](specs/README.md#execution-order-08-13-batch)).

## References

- Berdoz et al., "Can AI Agents Agree?" — [arXiv:2603.01213](https://arxiv.org/abs/2603.01213)
- Zheng et al., CP-WBFT consensus — [arXiv:2511.10400](https://arxiv.org/abs/2511.10400)
- MAST failure taxonomy — [OpenReview](https://openreview.net/pdf?id=wM521FqPvI)
- DecentLLMs leaderless consensus — [arXiv:2507.14928](https://arxiv.org/abs/2507.14928)
- AgentsNet benchmark — [arXiv:2507.08616](https://arxiv.org/abs/2507.08616)
- FREE-MAD premature convergence — [arXiv:2509.11035](https://arxiv.org/abs/2509.11035)
- Irving, Christiano, Amodei, "AI Safety via Debate" — [arXiv:1805.00899](https://arxiv.org/abs/1805.00899)
- Brown-Cohen, Irving, Piliouras, "Scalable AI Safety via Doubly-Efficient Debate" — [arXiv:2311.14125](https://arxiv.org/abs/2311.14125) (theoretical foundation for specs 07–11)
- Brown-Cohen, Irving, Piliouras, "Avoiding Obfuscation with Prover-Estimator Debate" — [arXiv:2506.13609](https://arxiv.org/abs/2506.13609) (theoretical foundation for spec 12)
- Brown-Cohen, Irving, Marshall, Newman, Piliouras, Szegedy, "Debate is Efficient with Your Time" — [arXiv:2602.08630](https://arxiv.org/abs/2602.08630) (theoretical foundation for spec 13)
