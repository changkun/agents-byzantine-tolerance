# Experiment 07 — Adversarial Debate

Spec: [`specs/07-adversarial-debate.md`](../../specs/07-adversarial-debate.md)

The spec calls for three sub-tasks: **07a** (bug detection), **07b** (action
gating), **07c** (ambiguity localization). Only 07a is implemented in this
repo. 07b/07c need a different leaf schema and a non-deterministic judge —
see the bottom of this file for what's missing.

## Run record

| Run    | Date       | Debates | Records | Cost | Reproducer |
|--------|------------|--------:|--------:|------|------------|
| smoke  | 2026-05-06 | 2       | 8       | ~2 min wall | `uv run python experiments/07_debate.py --smoke` |

The spec wants 3 sub-tasks (07a/07b/07c) × 3 honesty conditions × 4 role
assignments × 2 round budgets × 10–15 tasks × 5 trials. Smoke covers 07a only,
both honest, claude_p_claude_c roles, 4 rounds, 2 snippets.

## Run order

1. **Smoke** — sanity check the wiring (~2 min):
   `uv run python experiments/07_debate.py --smoke`
2. **First spec-07 run that exercises the debate architecture** — the spec's
   H6 test (p-byzantine proposer on a clear bug). The smoke run only proves
   the harness; this is the first one that actually tests the architecture:
   `uv run python experiments/07_debate.py --honesty p-byzantine --snippet-ids S01 --trials 5`
3. **Broaden** along the axes in [How to extend (07a)](#how-to-extend-07a).

The smoke run does not test the architecture — see Outcome below for why.

## Smoke configuration

- **Sub-task**: 07a (bug detection on snippets from `experiments/snippets.yaml`)
- **Snippets**: S01 (clear off-by-one) and S03 (no-bug-looks-buggy)
- **Honesty**: both (proposer & critic both honest)
- **Roles**: P=claude, C=claude
- **Round budget**: 4 (R1 propose, R2 attack, R3 defend, R4 stake)
- **Judge**: deterministic — checks the critic's R4 stake against the
  ground-truth bug line (±1) or kind label.

## Outcome — judge semantics matter

Each debate is 4 rounds, 1 invocation per round = 4 invocations per debate.

| Debate | gt_has_bug | P R1 claim       | C R2 attacks | C R4 stake | Verdict | System says | Sound? |
|--------|:----------:|-----------------:|:-----------:|:----------:|:-------:|:-----------:|:----:|
| S01    | true       | bug (line 8, OOB) | []          | none (-1)  | P_wins  | bug         | ✅   |
| S03    | false      | no_bug            | []          | none (-1)  | P_wins  | no_bug      | ✅   |

Both debates collapsed into "proposer-only assertion" mode. The critic produced
empty attack lists and conceded the stake. **Soundness is 2/2** — but only
because the proposer happened to give the truthful R1 claim in both cases.

This is a real and important finding the spec calls out as H6 (the binding
constraint): **debate's soundness is gated by critic strength**. With critic
producing zero attacks, the architecture reduces to "trust the proposer." That
is no better than asking one agent in isolation — and it costs 4× the
invocations.

The spec's prescribed test is the **p-byzantine** condition: force the proposer
to claim "no_bug" on a known-buggy snippet, and measure whether the critic can
recover. We didn't run that in smoke — it's step 2 in [Run order](#run-order).

If the critic stays silent under p-byzantine on a clear bug, the architecture
fails at the gating constraint and the spec's H1/H3 ("debate beats voting" /
"debate survives Byzantine proposer") cannot hold. If the critic *does* engage
when the proposer is byzantine, the all-honest cases above were just well-aligned
agents that didn't need debate.

## Note on the judge change during smoke development

The first version of `judge()` always declared C_wins ⇔ system says has_bug,
which gave **soundness=False on S01** because P correctly admitted the bug
and C had nothing to do (the system's claim was true, but the judge tied
soundness to the critic-winning rather than the system-claiming-correctly).
The judge was rewritten to track the *system's claim* (the proposer's R1
claim if P_wins, or "bug at staked location" if C_wins). That's the
semantically correct definition for 07a and aligns soundness with
ground truth, not with role-assignment.

## Files

- [`smoke.jsonl`](smoke.jsonl) — full per-round transcripts (raw_tail) +
  parsed JSON + judge output.
- [`smoke.summary.md`](smoke.summary.md) — by-honesty / by-roles tables.
- [`smoke.plots/soundness_by_honesty.png`](smoke.plots/soundness_by_honesty.png).

## How to extend (07a)

After step 2 of [Run order](#run-order) (the p-byzantine S01 run) lands,
broaden along these axes:

1. **Widen p-byzantine to more snippets**:
   `uv run python experiments/07_debate.py --honesty p-byzantine --snippet-ids S01,S02 --trials 3`
2. **c-lazy** (test H6 binding):
   `uv run python experiments/07_debate.py --honesty c-lazy --snippet-ids S01,S02 --trials 3`
3. **Heterogeneous roles**: critic = codex while proposer = claude:
   `uv run python experiments/07_debate.py --roles claude_p_codex_c --trials 3`
4. **Equal-compute baseline vs. spec 03**: spec calls for a head-to-head
   comparison at matched invocations. Cross-reference results/07/x.jsonl
   with results/03_bug_detection/x.jsonl.

## What 07b and 07c would need

Both reuse banks already in this repo (`experiments/actions.yaml` for 07b,
`experiments/specs.yaml` for 07c) but need new code:

**07b — action gating**
- Reuses `actions.yaml`. P argues "execute"; C argues "block."
- Leaf shape: a concrete *failure mode* the action would trigger
  (e.g. `{"input_state": "...", "expected_breakage": "..."}`).
- Judge: cannot be deterministic — needs an LLM-judge that scores the
  staked failure mode against the action's ground-truth `should_block`
  and `severity`. The spec says human-judge is gold standard but
  expensive; LLM-judge is the practical option.
- Comparison: ROC head-to-head against the spec-05 K-of-N gate at
  matched compute (4 invocations per debate ≈ N=4 voting).

**07c — ambiguity localization**
- Reuses `specs.yaml`. P commits to design decisions; C attacks individual
  decisions as under-specified.
- Leaf shape: `{"decision_key": "...", "two_valid_interpretations": ["...","..."]}`
  — the critic must exhibit *two* defensible interpretations to win.
- Judge: structured — checks whether `decision_key` is in the spec-04
  ambiguity set.
- Comparison: precision against spec-04's top-K disagreement classifier.

The current `experiments/07_debate.py` would need a `--task {07a,07b,07c}`
dispatch that loads the right bank, swaps the round prompts, and routes
to the right judge. The Agent class and round loop carry over unchanged.
