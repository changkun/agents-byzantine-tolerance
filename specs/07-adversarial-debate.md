# Experiment 07 — Adversarial Debate as a Third Architecture

## Thesis under test

The other six experiments cover two architectures: **parallel consensus** (01–05), where N independent agents answer the same question and we aggregate, and **sequential chains** (06), where each stage consumes the previous. This spec adds a third: **adversarial dialectic between two roles, judged externally**.

Inspired by Irving et al. (2018), *AI Safety via Debate*: one agent proposes, another is incentivized to find flaws, multiple rounds of cross-examination, and a judge inspects only the single disputed claim that decides the debate. The complexity-theoretic intuition (debate ≈ PSPACE under optimal play, strictly above NP) is suggestive but not what we test — LLMs aren't optimal players. What we test empirically:

1. Does debate achieve higher soundness than K-of-N voting at equal compute, on tasks with verifiable ground truth?
2. Does it preserve soundness when the proposer is Byzantine (the strongest theoretical claim — soundness with one honest player plus judge)?
3. Is the cost-of-attention asymmetry real — does the judge actually need to inspect less than reading the full output?

This is **structurally distinct** from voting: adversarial incentive replaces independence-by-replication. A Byzantine proposer must maintain a consistent lie across every cross-examination round; an honest critic only needs to find one inconsistency. Soundness no longer requires honest majority — it requires one honest player and a calibrated judge.

## Architecture

Three roles, fixed for a debate:

- **Proposer (P)** — given a task, produces a claim, code, or argument. Stake: judged correct at the staked leaf.
- **Critic (C)** — given P's output, must produce *concrete* attacks (specific input/assertion/counterexample, not vibes). Stake: forces P into an indefensible leaf.
- **Judge (J)** — evaluates only the leaf the debate ends on, never the full transcript.

Round structure (4 rounds, fixed):

1. **R1 — Proposal.** P answers the task.
2. **R2 — Attack.** C produces ≤ K specific attacks. Each attack must be a verifiable claim of the form "input X produces output Y, which violates Z."
3. **R3 — Defense.** P responds to each attack: *concede* or *rebut* with a specific counter-claim.
4. **R4 — Stake.** C picks one unresolved attack as the decisive leaf. If C cannot find one (i.e., conceded all), P wins by default.

The judge sees only R4's staked leaf, not R1–R3. This is the cost-of-attention claim under test.

## Judge modes

We compare three (this is the most important variable):

1. **Deterministic check** — the staked leaf is structured as a runnable assertion (test case, type-check, property). No LLM/human in the loop. Highest soundness, narrowest applicability. *This is where PCP-style spot-checking enters: a leaf that propagates errors deterministically.*
2. **LLM judge** — a separate LLM evaluates the staked leaf only. Cheap; risks moving the problem. Important to measure how much it loses to (1).
3. **Human judge** — gold standard for tasks without a deterministic check. Expensive; we sample a small fraction.

## Task design

We piggyback on existing experiments rather than inventing new tasks, so we can A/B against voting:

- **07a — Bug detection** (debate variant of spec 03). Code snippet with or without seeded bug. P claims "no bug" (or proposes a fix); C must produce input that triggers it. Deterministic-check judge: run the input.
- **07b — Action gating** (debate variant of spec 05). P argues "execute"; C argues "block." LLM or human judge. ROC curve vs. spec 05's K-of-N gate at equal compute.
- **07c — Ambiguity localization** (debate variant of spec 04). Spec from the 04 bank; P commits to design decisions; C attacks each one. Hypothesis: the staked leaf identifies the genuine ambiguity more precisely than top-K disagreement from voting.

07a is the cleanest test (deterministic judge, ground truth). Run it first.

## Independent variables

- **Task**: 07a, 07b, 07c.
- **Judge mode**: {deterministic, LLM-judge, human}. Deterministic only available for 07a.
- **Honesty**: {both honest, P-Byzantine, C-lazy}. P-Byzantine reuses the injection templates from spec 02. C-lazy = critic prompt removes the adversarial framing ("review this code" instead of "find a flaw"). C-lazy is the realistic failure mode and probably the binding constraint.
- **Role assignment**: {Claude-as-P/Codex-as-C, Codex-as-P/Claude-as-C, both Claude, both Codex}. Asymmetry between models matters — a stronger critic changes everything.
- **Round budget**: {2 rounds (R1+R2 only, no defense), 4 rounds (full)}.

Trials per cell: 5. Tasks per cell: 10–15 (reuse from 02, 03, 05).

## Comparison baseline

For every cell, compute the **equal-compute K-of-N voting result** on the same task. "Equal compute" = same number of total agent invocations. A 4-round 2-player debate is 4 invocations; the matched voting baseline is N=4 with majority vote. This is the head-to-head debate-vs-voting comparison the spec exists to make.

## Metrics

1. **Soundness** (primary): judge's verdict matches ground truth.
2. **Critic-found-bug rate** (gating metric): when ground truth has a bug, fraction of debates where C's R2 attacks include a valid one. *If this is near zero, debate ≈ proposer alone, and nothing else matters.* Measure separately and report first.
3. **Cost-of-attention**: tokens (or lines) the judge actually reads vs. tokens in the full transcript. The asymmetry claim under test.
4. **Soundness under Byzantine proposer**: subset metric (1) restricted to P-Byzantine cells. Compare to spec 02's voting result at the same effective f/N. The strongest claim — does debate stay sound where voting collapses?
5. **Soundness under lazy critic**: subset metric (1) restricted to C-lazy cells. Quantifies how brittle the architecture is to critic effort.

Headline plot: **soundness vs. critic-found-bug rate**, faceted by honesty condition, with voting baselines as horizontal lines.

## Hypotheses

- **H1 (debate beats voting at equal compute on bug-detection).** On 07a with both honest, deterministic judge, debate soundness > matched K-of-N voting soundness.
- **H2 (critic strength gates everything).** Soundness scales near-linearly with critic-found-bug rate. The variable that determines whether debate works isn't debate vs. voting — it's whether C actually attacks.
- **H3 (Byzantine proposer asymmetry).** Debate degrades *less* under P-Byzantine than voting degrades at f/N = 1/2 (one of two players Byzantine). This is the strongest version of Irving's claim and the experiment that justifies the architecture.
- **H4 (judge mode dominates).** Soundness ordering: deterministic > human > LLM-judge, with the gap between deterministic and LLM-judge larger than the gap between debate and voting under either judge. If true, the win from debate is inseparable from how good the leaf check is.
- **H5 (cost-of-attention is real).** Judge-read tokens are < 30% of full-transcript tokens at no soundness cost when leaf structure is enforced. If false, the architecture's central efficiency claim doesn't hold.
- **H6 (lazy critic is the binding constraint).** C-lazy soundness is closer to proposer-alone than to honest-critic debate. Debate's win comes from adversarial framing, not from having a second agent.

## Open questions / known risks

- **What forces the critic to actually attack?** Irving 2018 assumes optimal adversarial play; LLMs default to politeness. Prompt engineering will determine whether this experiment runs at all. Pilot: measure critic-found-bug rate in isolation before running the full sweep. If it's < 30% on tasks with seeded bugs, redesign the critic prompt or abandon the spec.
- **Leaf disputability is fuzzy.** In PCP, "inconsistency" is binary. In code, leaves drift toward stylistic gripes. Mitigation: 07a uses runnable assertions (deterministic), 07b/07c need a leaf-format spec the critic must conform to (e.g., "your stake must name a concrete input and an expected violation").
- **LLM-judge moves the problem.** The whole point of debate is that the judge is cheap-because-narrow. If the LLM judge inherits the same biases as the players, soundness collapses to LLM-judge alone. H4 measures this directly; if it's bad, the architecture only works with deterministic or human judges, narrowing applicability.
- **Trusted judge assumption.** Strictly weaker than BFT's no-trusted-node, but real. We are *not* claiming debate solves the no-trust problem — we're claiming it lowers the trust budget from "honest majority across N players" to "calibrated judge plus one honest player." Spec writeups must say this explicitly.
- **Cross-cutting with PCP-style spot-checking.** The deterministic judge mode *is* PCP-style: a single check at the leaf gates the whole argument. Whether the encoding makes errors propagate (the actual PCP property) is task-dependent and not separately tested here. Worth its own spec later if H1+H4 hold.

## Deliverable

- `experiments/07_debate.py` — the runner. Takes `--task {07a,07b,07c}`, `--judge {det,llm,human}`, `--honesty {both,p-byz,c-lazy}`.
- `experiments/debate_prompts.yaml` — the proposer, critic, and judge prompt templates. Critic prompt is the high-leverage file; iterate on it.
- `experiments/leaf_schemas.yaml` — the structured-leaf format per task (e.g., `{input: ..., expected: ..., actual: ...}`).
- `results/07_debate.json`.
- `analysis/07_plot.py` — soundness-vs-critic-found-bug, plus the head-to-head debate-vs-voting bars at equal compute.

## Exit criteria

We have a publishable finding when at least one of the following holds:

1. **H1 + H3 hold:** debate beats voting on the equal-compute bug-detection baseline *and* survives Byzantine proposer where voting collapses. This is the strong positive result and justifies adversarial dialectic as a first-class architecture.
2. **H2 + H6 hold:** critic strength gates everything and lazy critics collapse the architecture. This is the negative result that matters — debate isn't an architectural win, it's a prompt-engineering win on the critic side, with implications for how to deploy it.
3. **H4 holds strongly** (judge-mode gap > debate-vs-voting gap): tells us the research direction is verification primitives at the leaf, not adversarial framing — a redirection finding worth publishing.

H5 (cost-of-attention) is a sanity check; if it fails, we haven't built debate, we've built voting-with-extra-steps.

## Cross-references

- **vs. 02**: 07 directly tests the Byzantine-proposer claim that 02 sets up a voting baseline for. Compare at matched f/N.
- **vs. 03**: 07a is the debate variant of 03's bug-detection task. Run 03 first; 07a is the head-to-head.
- **vs. 04**: 07c is the debate variant of 04's ambiguity-localization task. Compares staked-leaf precision against top-K disagreement.
- **vs. 05**: 07b is the debate variant of 05's K-of-N gate. ROC head-to-head at equal compute.
- **Not vs. 01, 06**: 01 has no adversary; 06 is sequential, not dialectic. Out of scope.
