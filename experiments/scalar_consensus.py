"""Experiment: Scalar consensus across varying agent group sizes.

Replicates and extends the finding from Berdoz et al. that valid consensus
drops from 46.6% (N=4) to 33.3% (N=16). Tests both homogeneous (single model)
and heterogeneous (mixed model) ensembles.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents_byzantine_tolerance.agent import Agent, AgentConfig, Provider, DEFAULT_CONFIGS
from agents_byzantine_tolerance.consensus import scalar_consensus, ConsensusResult

SYSTEM_PROMPT = (
    "You are participating in a consensus task. "
    "You must respond with exactly one integer between 1 and 100. "
    "Output only the number, nothing else."
)

TASK_PROMPT = "Pick an integer between 1 and 100."

GROUP_SIZES = [4, 8, 12, 16]
TRIALS_PER_SIZE = 20


def make_homogeneous_agents(n: int, config_name: str = "claude-haiku") -> list[Agent]:
    config = DEFAULT_CONFIGS[config_name]
    return [Agent(f"agent-{i}", config) for i in range(n)]


def make_heterogeneous_agents(n: int) -> list[Agent]:
    configs = list(DEFAULT_CONFIGS.values())
    return [Agent(f"agent-{i}", configs[i % len(configs)]) for i in range(n)]


async def run_experiment(
    group_sizes: list[int] = GROUP_SIZES,
    trials: int = TRIALS_PER_SIZE,
    heterogeneous: bool = False,
) -> dict:
    results = {}

    for n in group_sizes:
        print(f"\n--- N={n} agents, {trials} trials {'(heterogeneous)' if heterogeneous else '(homogeneous)'} ---")
        outcomes = []

        for t in range(trials):
            if heterogeneous:
                agents = make_heterogeneous_agents(n)
            else:
                agents = make_homogeneous_agents(n)

            result = await scalar_consensus(
                agents, TASK_PROMPT, system=SYSTEM_PROMPT, tolerance=0.0
            )

            outcomes.append({
                "trial": t,
                "agreed": result.agreed,
                "agreed_value": result.agreed_value,
                "valid_count": result.valid_count,
                "total": n,
                "agreement_map": {
                    str(k): v for k, v in result.agreement_map.items()
                },
            })

            status = "AGREED" if result.agreed else "DISAGREED"
            groups = len(result.agreement_map)
            print(f"  Trial {t:>2}: {status} | {result.valid_count}/{n} valid | {groups} distinct values")

        agreed_count = sum(1 for o in outcomes if o["agreed"])
        valid_rate = sum(o["valid_count"] for o in outcomes) / (len(outcomes) * n)

        summary = {
            "n_agents": n,
            "trials": trials,
            "consensus_rate": agreed_count / trials,
            "avg_valid_rate": valid_rate,
            "outcomes": outcomes,
        }
        results[n] = summary
        print(f"  Consensus rate: {agreed_count}/{trials} = {summary['consensus_rate']:.1%}")
        print(f"  Valid response rate: {valid_rate:.1%}")

    return results


async def main():
    print("=== Scalar Consensus Experiment ===\n")

    print("\n[1/2] Homogeneous ensemble (same model)")
    homo_results = await run_experiment(heterogeneous=False)

    print("\n\n[2/2] Heterogeneous ensemble (mixed models)")
    hetero_results = await run_experiment(heterogeneous=True)

    output = {
        "homogeneous": {str(k): v for k, v in homo_results.items()},
        "heterogeneous": {str(k): v for k, v in hetero_results.items()},
    }

    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "scalar_consensus.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
