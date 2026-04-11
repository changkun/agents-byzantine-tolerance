"""Consensus protocols for multi-agent agreement."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field

from .agent import Agent


@dataclass
class ConsensusResult:
    """Result of a consensus round."""

    responses: dict[str, str]  # agent_id -> raw response
    parsed_values: dict[str, float | None]  # agent_id -> parsed numeric value
    agreed: bool = False
    agreed_value: float | None = None
    rounds: int = 1

    @property
    def valid_count(self) -> int:
        return sum(1 for v in self.parsed_values.values() if v is not None)

    @property
    def agreement_map(self) -> dict[float, list[str]]:
        """Partial agreement map: value -> list of agent_ids that proposed it."""
        groups: dict[float, list[str]] = {}
        for aid, val in self.parsed_values.items():
            if val is not None:
                groups.setdefault(val, []).append(aid)
        return groups


def parse_numeric(text: str) -> float | None:
    """Extract a numeric value from agent response text."""
    # Try to find a JSON number first
    try:
        return float(json.loads(text))
    except (json.JSONDecodeError, ValueError):
        pass
    # Look for a number pattern
    match = re.search(r"(?:^|\s)(-?\d+(?:\.\d+)?)\s*$", text.strip())
    if match:
        return float(match.group(1))
    # Look for "answer is X" patterns
    match = re.search(r"(?:answer|value|number|result)\s*(?:is|:)\s*(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


async def scalar_consensus(
    agents: list[Agent],
    prompt: str,
    system: str = "",
    tolerance: float = 0.0,
    max_rounds: int = 1,
) -> ConsensusResult:
    """Run a scalar consensus protocol: all agents respond, check agreement.

    Args:
        agents: List of agents to participate.
        prompt: The prompt asking for a numeric answer.
        system: Optional system prompt.
        tolerance: Maximum allowed difference between values for agreement.
        max_rounds: Maximum negotiation rounds (1 = single-shot).
    """
    tasks = [agent.query(prompt, system=system) for agent in agents]
    responses_list = await asyncio.gather(*tasks)

    responses = {agent.agent_id: resp for agent, resp in zip(agents, responses_list)}
    parsed = {agent.agent_id: parse_numeric(resp) for agent, resp in zip(agents, responses_list)}

    result = ConsensusResult(responses=responses, parsed_values=parsed)

    # Check agreement
    valid_values = [v for v in parsed.values() if v is not None]
    if valid_values:
        ref = valid_values[0]
        if all(abs(v - ref) <= tolerance for v in valid_values):
            result.agreed = True
            result.agreed_value = ref

    return result
