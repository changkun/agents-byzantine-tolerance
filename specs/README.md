# Experiment Specs

Each spec describes one self-contained experiment: what it measures, how it's set up, ground truth (if any), and the hypotheses being tested.

The seven experiments split into three architectures: **parallel consensus** (01–05), where N agents answer the same question independently; **sequential chains** (06), where agents process each other's output; and **adversarial dialectic** (07), where two agents debate under an external judge.

## Parallel-consensus experiments

1. **[01-verifiable-consensus.md](01-verifiable-consensus.md)** — baseline. Can N headless coding agents agree on an answer with objective ground truth? Measures both *liveness* (did they agree?) and *safety* (were they right?), which the blog argues are separable failure modes.

2. **[02-byzantine-injection.md](02-byzantine-injection.md)** — the adversarial case. Seed 1…⌊N/2⌋ agents with false premises and sweep the honest/Byzantine ratio. Does the classical `f < N/3` bound hold for stochastic agents? Does heterogeneity mitigate correlated failure?

3. **[03-bug-detection-consensus.md](03-bug-detection-consensus.md)** — *testing as distributed consensus* (blog approach #2). N agents independently review the same code snippet. Does unanimous agreement correlate with bugs actually being present? Does disagreement flag ambiguous code?

4. **[04-ambiguous-spec-detection.md](04-ambiguous-spec-detection.md)** — *partial agreement maps* (blog approach #3). Pair ambiguous vs. unambiguous specs; measure whether per-decision disagreement reliably identifies which decisions the author left under-specified. The most directly actionable finding if it works.

5. **[05-consensus-gated-actions.md](05-consensus-gated-actions.md)** — *consensus-gated autonomous actions* (blog approach #1). K-of-N approval gate over a mix of safe and destructive proposed actions. Does gating reduce destructive execution without unacceptably blocking safe actions? Sweep K to find the ROC frontier.

## Sequential-chain experiments

6. **[06-cascading-hallucination.md](06-cascading-hallucination.md)** — the other dominant multi-agent pattern. K-stage pipeline where each agent consumes the previous stage's output. Do errors propagate, amplify, or get corrected? Do chains with re-grounding against the source beat chains without? This is where parallel-consensus intuitions break down.

## Adversarial-dialectic experiments

7. **[07-adversarial-debate.md](07-adversarial-debate.md)** — Irving-2018-style debate. Proposer vs. critic across fixed rounds; judge inspects only the staked leaf. Tests the strong claim that soundness needs only one honest player plus a calibrated judge, not honest majority. Provides debate variants of 03 (bug detection), 04 (ambiguity), and 05 (action gating) for head-to-head against voting at equal compute.

## Reading order

If you only read two specs: **04** (ambiguous-spec detection — most actionable) and **06** (cascading — where classical BFT intuitions invert). For the architectural alternative to voting, read **07**. 01 is the shared baseline that the others build on.
