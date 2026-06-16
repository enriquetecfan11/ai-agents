"""Contrato base para tools del agente."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolResult:
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(Protocol):
    name: str
    description: str

    def invoke(self, **kwargs: Any) -> ToolResult: ...
