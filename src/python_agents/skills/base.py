"""Contrato base para skills del agente."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from src.python_agents.skills.tracing import TraceEvent, trace_event
from src.python_agents.tools.base import BaseTool, ToolResult


@dataclass
class SkillContext:
    llm: BaseChatModel
    trace: list[TraceEvent]
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    answer: str
    skill_name: str
    tools_used: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    name: str
    description: str
    intent_label: str
    tools: list[BaseTool]

    @abstractmethod
    def run(self, query: str, context: SkillContext) -> SkillResult: ...

    def _call_tool(
        self,
        tool: BaseTool,
        context: SkillContext,
        **kwargs: Any,
    ) -> ToolResult:
        start = time.perf_counter()
        context.trace.append(
            trace_event("tool_call", skill=self.name, tool=tool.name, detail=kwargs)
        )
        result = tool.invoke(**kwargs)
        duration_ms = (time.perf_counter() - start) * 1000
        context.trace.append(
            trace_event(
                "tool_result",
                skill=self.name,
                tool=tool.name,
                detail={"output_len": len(result.output)},
                duration_ms=duration_ms,
            )
        )
        return result
