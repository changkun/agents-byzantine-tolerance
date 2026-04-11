"""Base agent abstraction over multiple LLM providers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

import anthropic
import openai


class Provider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class AgentConfig:
    provider: Provider
    model: str
    temperature: float = 1.0


DEFAULT_CONFIGS = {
    "claude-sonnet": AgentConfig(Provider.ANTHROPIC, "claude-sonnet-4-6"),
    "claude-haiku": AgentConfig(Provider.ANTHROPIC, "claude-haiku-4-5-20251001"),
    "gpt-4o": AgentConfig(Provider.OPENAI, "gpt-4o"),
    "gpt-4o-mini": AgentConfig(Provider.OPENAI, "gpt-4o-mini"),
}


class Agent:
    """A single LLM agent that can participate in consensus protocols."""

    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config

        if config.provider == Provider.ANTHROPIC:
            self._client = anthropic.Anthropic()
        elif config.provider == Provider.OPENAI:
            self._client = openai.OpenAI()

    async def query(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the response text."""
        if self.config.provider == Provider.ANTHROPIC:
            client = anthropic.AsyncAnthropic()
            msg = await client.messages.create(
                model=self.config.model,
                max_tokens=1024,
                temperature=self.config.temperature,
                system=system or anthropic.NOT_GIVEN,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text

        elif self.config.provider == Provider.OPENAI:
            client = openai.AsyncOpenAI()
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = await client.chat.completions.create(
                model=self.config.model,
                max_tokens=1024,
                temperature=self.config.temperature,
                messages=messages,
            )
            return resp.choices[0].message.content

    def __repr__(self) -> str:
        return f"Agent({self.agent_id!r}, {self.config.model})"
