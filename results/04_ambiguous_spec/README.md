# Experiment 04 — Ambiguous-Spec Detection

Spec: [`specs/04-ambiguous-spec-detection.md`](../../specs/04-ambiguous-spec-detection.md)

## Run record

| Run    | Date       | Cells | Records | Cost | Reproducer |
|--------|------------|------:|--------:|------|------------|
| smoke  | 2026-05-06 | 2     | 6       | ~40s wall | `python experiments/04_ambiguous_spec.py --smoke` |

The spec calls for ~8–10 paired specs × 3 N × 3 compositions × 3 trials ≈ 1,500
invocations. The smoke bank has **one pair** (P1: rate-limiter); expand
`experiments/specs.yaml` before drawing conclusions.

## Smoke configuration

- **Spec pair**: P1 rate-limiter. Decisions: algorithm, storage, key_scope,
  rejection_behavior, persistence, capacity (numeric), refill_rate (numeric).
- **Variants**: unambiguous (token-bucket, capacity 100, refill 10/s, per-user,
  HTTP 429, in-memory, no persistence) vs. ambiguous ("Build a rate limiter.").
- **N**: 3, homogeneous-claude, 1 trial per cell.

## Outcome — H1 confirmed in microcosm; H2 hits target

Per-decision disagreement (entropy for categorical, CV for numeric):

| Decision           | Unambiguous | Ambiguous | Gap    |
|--------------------|------------:|----------:|-------:|
| algorithm          | 0.00        | 0.00      | 0.00   |
| storage            | 0.00        | 0.58      | +0.58  |
| key_scope          | 0.00        | 0.58      | +0.58  |
| rejection_behavior | 0.00        | 0.00      | 0.00   |
| persistence        | 0.00        | 0.58      | +0.58  |
| capacity (numeric) | 0.00        | 1.00      | +1.00  |
| refill_rate (numeric) | 0.00     | 1.00      | +1.00  |

- **Mean disagreement gap: +0.53.** Strongly positive — ambiguity → disagreement
  in this sample.
- **AUC of disagreement-as-ambiguity classifier: 0.86.** Exceeds the spec's
  H2 target (≥ 0.80 for deployability). Small-sample warning applies.
- **The two zero-gap decisions (algorithm, rejection_behavior) are interesting**:
  even given just "Build a rate limiter," all three agents converged on
  token-bucket + HTTP 429. Strong shared priors override under-specification
  for these slots. This validates the H5 caveat in the spec — disagreement is
  signal, but "no disagreement" doesn't always mean "spec is unambiguous";
  it can also mean "shared convention is so strong that ambiguity is hidden
  by uniform default-picking."
- The numeric decisions (capacity, refill_rate) hit max disagreement (CV=1.0)
  on the ambiguous spec. Numeric ambiguity is the cleanest signal.

## Files

- [`smoke.jsonl`](smoke.jsonl) — raw records: per-agent answer dict + per-decision
  disagreement scores + ambiguity-set labels.
- [`smoke.summary.md`](smoke.summary.md) — per-decision gap table + AUC.
- [`smoke.plots/heatmap.png`](smoke.plots/heatmap.png) — disagreement heatmap
  (decisions × specs); the visual analogue of the partial-agreement-map
  diagnostic the spec proposes.

## How to extend

1. **Add spec pairs.** Cache, retry, idempotency, timestamp parsing — see
   spec 04 §"Spec bank" for the full draft list.
2. **Heterogeneous composition** is the most direct test of H4 (heterogeneity
   sharpens the signal):
   `python experiments/04_ambiguous_spec.py --compositions heterogeneous --ns 5 --trials 3`
3. **Larger N + more trials**: the AUC computed here is from 14
   (decision, label) datapoints; extending to more pairs and trials gives
   a defensible AUC measurement.
