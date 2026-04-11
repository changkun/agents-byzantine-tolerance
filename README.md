# agents-byzantine-tolerance

An experiment exploring the structural equivalence between Byzantine fault tolerance in distributed systems and failure modes in multi-agent LLM systems.

**Motivation:** Multi-agent LLM systems fail at 41-86.7% rates in production, with coordination failures accounting for 36.94% of failures. LLM hallucinations are structurally identical to Byzantine nodes sending contradictory messages to different peers — yet the agent community has largely overlooked 40 years of BFT theory that directly applies.

Full writeup: https://changkun.de/blog/ideas/agents-byzantine-tolerance/

## Approaches

1. **Consensus-Gated Autonomous Actions** — High-risk decisions require multi-agent agreement before execution; low-risk actions proceed freely.
2. **Testing as Distributed Consensus** — Multiple independent agents must agree on test pass/fail; disagreement indicates specification ambiguity.
3. **Partial Agreement Maps** — Structured views showing where agents converge vs. diverge, treating disagreement as the most informative signal.

## Experiments

### Scalar Consensus

Replicate and extend the finding that valid consensus drops from 46.6% (N=4) to 33.3% (N=16) agents. Measure liveness vs. safety failures across agent counts and model configurations.

### Correlated Failure Analysis

Test whether homogeneous (same model) vs. heterogeneous (mixed models) agent ensembles exhibit different failure correlation patterns.

### Disagreement-as-Signal

Evaluate whether partial agreement maps can reliably identify where human attention is needed, compared to majority voting.

## References

- Berdoz et al., "Can AI Agents Agree?" — [arXiv:2603.01213](https://arxiv.org/abs/2603.01213)
- Zheng et al., CP-WBFT consensus — [arXiv:2511.10400](https://arxiv.org/abs/2511.10400)
- MAST failure taxonomy — [OpenReview](https://openreview.net/pdf?id=wM521FqPvI)
- DecentLLMs leaderless consensus — [arXiv:2507.14928](https://arxiv.org/abs/2507.14928)
- AgentsNet benchmark — [arXiv:2507.08616](https://arxiv.org/abs/2507.08616)
- FREE-MAD premature convergence — [arXiv:2509.11035](https://arxiv.org/abs/2509.11035)
