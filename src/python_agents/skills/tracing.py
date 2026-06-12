"""Trazabilidad simple para skills y tools."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceEvent:
    ts: float
    event: str
    skill: str | None = None
    tool: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None

    def format_line(self) -> str:
        parts = [f"[{self.duration_ms or 0:.1f}ms]", self.event]
        if self.skill:
            parts.append(f"skill={self.skill}")
        if self.tool:
            parts.append(f"tool={self.tool}")
        if self.detail:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.detail.items())
            parts.append(f"({detail_str})")
        return " ".join(parts)


def append_trace(existing: list[TraceEvent], new: list[TraceEvent]) -> list[TraceEvent]:
    """Reducer para acumular eventos de trazabilidad en el estado del grafo."""
    return existing + new


def trace_event(
    event: str,
    *,
    skill: str | None = None,
    tool: str | None = None,
    detail: dict[str, Any] | None = None,
    duration_ms: float | None = None,
) -> TraceEvent:
    return TraceEvent(
        ts=time.time(),
        event=event,
        skill=skill,
        tool=tool,
        detail=detail or {},
        duration_ms=duration_ms,
    )
