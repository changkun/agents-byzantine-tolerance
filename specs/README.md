# Experiment Specs

Each spec describes one self-contained experiment: what it measures, how it's set up, ground truth (if any), and the hypotheses being tested.

Seven experiments split into three architectures: **parallel consensus** (01–05), where N agents answer the same question independently; **sequential chains** (06), where agents process each other's output; and **adversarial dialectic** (07), where two agents debate under an external judge. A separate repo, [latere-ai/debate](https://github.com/latere-ai/debate), holds the tool that productizes architecture 07 and is gated on spec 07a's results.

## Status

| Spec | Implementation | Smoke run | Full run | Results |
|------|----------------|-----------|----------|---------|
| 01 — Verifiable consensus      | ✅ | ✅ 2026-05-06 | ⏳ | [`results/01_verifiable_consensus/`](../results/01_verifiable_consensus/) |
| 02 — Byzantine injection       | ✅ | ✅ 2026-05-06 | ⏳ | [`results/02_byzantine_injection/`](../results/02_byzantine_injection/) |
| 03 — Bug detection             | ✅ | ✅ 2026-05-06 | ⏳ | [`results/03_bug_detection/`](../results/03_bug_detection/) |
| 04 — Ambiguous-spec detection  | ✅ | ✅ 2026-05-06 | ⏳ | [`results/04_ambiguous_spec/`](../results/04_ambiguous_spec/) |
| 05 — Consensus-gated actions   | ✅ | ✅ 2026-05-06 | ⏳ | [`results/05_consensus_gate/`](../results/05_consensus_gate/) |
| 06 — Cascading hallucination   | ⏳ | ⏳ | ⏳ | — |
| 07 — Adversarial debate        | ⏳ | ⏳ | ⏳ | — |

Smoke = end-to-end pipeline check on a tiny config. Full = the spec-prescribed
sweep. Smoke results are **not** sufficient evidence for any of the hypotheses
in the specs; they prove the runner works and produce a small sample for
inspection.

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

## Productization

The tool spec that builds on spec 07 lives in a separate repo: [latere-ai/debate](https://github.com/latere-ai/debate). It's gated on this repo's spec 07a returning positive (critic-found-bug rate ≥ 60%); do not build until then.

## Reading order

If you only read two specs: **04** (ambiguous-spec detection — most actionable) and **06** (cascading — where classical BFT intuitions invert). For the architectural alternative to voting, read **07**. 01 is the shared baseline that the others build on.
