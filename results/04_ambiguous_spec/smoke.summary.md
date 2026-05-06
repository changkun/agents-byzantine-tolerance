# Experiment 04 — Ambiguous-Spec Detection

Total cells: 2

## Per-decision disagreement (mean across trials/compositions)

| pair | variant | decision | mean_disagreement | in_ambiguity_set |
|------|---------|----------|------------------:|:----------------:|
| P1 | ambiguous | algorithm | 0.00 | ✓ |
| P1 | ambiguous | capacity | 1.00 | ✓ |
| P1 | ambiguous | key_scope | 0.58 | ✓ |
| P1 | ambiguous | persistence | 0.58 | ✓ |
| P1 | ambiguous | refill_rate | 1.00 | ✓ |
| P1 | ambiguous | rejection_behavior | 0.00 | ✓ |
| P1 | ambiguous | storage | 0.58 | ✓ |
| P1 | unambiguous | algorithm | 0.00 |  |
| P1 | unambiguous | capacity | 0.00 |  |
| P1 | unambiguous | key_scope | 0.00 |  |
| P1 | unambiguous | persistence | 0.00 |  |
| P1 | unambiguous | refill_rate | 0.00 |  |
| P1 | unambiguous | rejection_behavior | 0.00 |  |
| P1 | unambiguous | storage | 0.00 |  |

## H1: per-decision disagreement gap (ambiguous − unambiguous)

| pair | decision | gap |
|------|----------|----:|
| P1 | algorithm | 0.00 |
| P1 | capacity | 1.00 |
| P1 | key_scope | 0.58 |
| P1 | persistence | 0.58 |
| P1 | refill_rate | 1.00 |
| P1 | rejection_behavior | 0.00 |
| P1 | storage | 0.58 |

Mean gap: **0.53** (positive = ambiguity → disagreement)

## H2: AUC of disagreement-as-ambiguity classifier

- AUC: **0.86**  (target ≥ 0.80 for deployable diagnostic)
