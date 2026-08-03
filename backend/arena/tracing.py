"""Ordered trace recorder with recursive secret redaction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from arena.domain import TraceEvent, TraceKind

SENSITIVE_KEYS = re.compile(r"(api[_-]?key|authorization|cookie|secret|token|password)", re.I)
TOKEN_PATTERN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]{8,})\b", re.I)


def redact(value: Any, protected_values: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]"
            if SENSITIVE_KEYS.search(str(key))
            else redact(item, protected_values)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, protected_values) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item, protected_values) for item in value)
    if isinstance(value, str):
        cleaned = TOKEN_PATTERN.sub("[REDACTED]", value)
        for secret in protected_values:
            if secret:
                cleaned = cleaned.replace(secret, "[REDACTED]")
        return cleaned
    return value


@dataclass
class TraceRecorder:
    run_id: str
    protected_values: tuple[str, ...] = ()
    events: list[TraceEvent] = field(default_factory=list)

    def record(
        self,
        kind: TraceKind,
        name: str,
        payload: dict[str, Any] | None = None,
        **metrics: Any,
    ) -> TraceEvent:
        event = TraceEvent(
            id=f"evt-{uuid4().hex[:12]}",
            run_id=self.run_id,
            sequence=len(self.events) + 1,
            kind=kind,
            name=name,
            payload=redact(payload or {}, self.protected_values),
            **metrics,
        )
        self.events.append(event)
        return event
