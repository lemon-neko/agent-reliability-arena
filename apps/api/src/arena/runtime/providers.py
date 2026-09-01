"""Model providers with one OpenAI-compatible boundary and a deterministic CI fake."""

from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from arena.domain.models import ModelTurn, ScenarioSpec, ToolCall


class ModelProvider(Protocol):
    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        scenario: ScenarioSpec,
    ) -> ModelTurn: ...


class DeterministicProvider:
    """A cost-free fake that follows each scenario's public scripted solution."""

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        scenario: ScenarioSpec,
    ) -> ModelTurn:
        del tools
        completed_calls = sum(message.get("role") == "tool" for message in messages)
        if completed_calls < len(scenario.scripted_actions):
            action = scenario.scripted_actions[completed_calls]
            return ModelTurn(
                tool_calls=[
                    ToolCall(
                        id=f"fake-call-{completed_calls + 1}",
                        name=action.tool,
                        arguments=action.arguments,
                    )
                ],
                input_tokens=max(1, len(json.dumps(messages, ensure_ascii=False)) // 4),
                output_tokens=20,
            )
        return ModelTurn(
            content=scenario.scripted_answer or "Task completed with the requested safeguards.",
            input_tokens=max(1, len(json.dumps(messages, ensure_ascii=False)) // 4),
            output_tokens=max(1, len(scenario.scripted_answer) // 4),
        )


class OpenAICompatibleProvider:
    """Small sync adapter compatible with OpenAI APIs and Ollama's /v1 surface."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60,
        input_cost_per_million: float = 0,
        output_cost_per_million: float = 0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        scenario: ScenarioSpec,
    ) -> ModelTurn:
        del scenario
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]["message"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise RuntimeError(f"model request failed safely: {type(error).__name__}") from error
        calls: list[ToolCall] = []
        for raw in choice.get("tool_calls") or []:
            try:
                arguments = json.loads(raw["function"].get("arguments") or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError
                calls.append(
                    ToolCall(
                        id=str(raw["id"]),
                        name=str(raw["function"]["name"]),
                        arguments=arguments,
                    )
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                raise RuntimeError("model returned an invalid structured tool call") from error
        usage = data.get("usage") or {}
        input_tokens = max(0, int(usage.get("prompt_tokens", 0)))
        output_tokens = max(0, int(usage.get("completion_tokens", 0)))
        return ModelTurn(
            content=str(choice.get("content") or ""),
            tool_calls=calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=(
                input_tokens * self.input_cost_per_million
                + output_tokens * self.output_cost_per_million
            )
            / 1_000_000,
        )


def openai_tools(allowed_tools: list[str]) -> list[dict[str, Any]]:
    schemas = {
        "file": {
            "operation": {"type": "string", "enum": ["list", "read", "write"]},
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "sql": {
            "statement": {"type": "string"},
            "parameters": {"type": "array"},
            "dry_run": {"type": "boolean"},
        },
        "retrieval": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 5},
        },
        "approval": {
            "action": {"type": "string"},
            "reason": {"type": "string"},
        },
        "secret": {
            "action": {"type": "string", "enum": ["exists"]},
            "name": {"type": "string"},
        },
        "http": {
            "method": {"type": "string", "enum": ["GET", "POST"]},
            "url": {"type": "string"},
            "body": {"type": "object"},
        },
        "business": {
            "operation": {"type": "string", "enum": ["get", "update", "delete", "send"]},
            "resource": {"type": "string"},
            "payload": {"type": "object"},
        },
    }
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": f"Restricted, synthetic arena {name} tool",
                "parameters": {
                    "type": "object",
                    "properties": schemas[name],
                    "additionalProperties": False,
                },
            },
        }
        for name in allowed_tools
        if name in schemas
    ]
