"""Skill general: conversación sin tools."""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.python_agents.skills.base import BaseSkill, SkillContext, SkillResult
from src.python_agents.skills.tracing import trace_event

_SYSTEM_MSG = SystemMessage(
    content="Eres un asistente útil y breve. Responde en español."
)


class GeneralSkill(BaseSkill):
    name = "skill_general"
    description = "Conversación general, saludos y preguntas que no requieren documentación ni tools."
    intent_label = "general"
    tools: list = []

    def run(self, query: str, context: SkillContext) -> SkillResult:
        start = time.perf_counter()
        context.trace.append(trace_event("skill_start", skill=self.name))

        messages = context.state.get("messages", [])
        if messages:
            llm_messages = [_SYSTEM_MSG, *messages]
        else:
            llm_messages = [_SYSTEM_MSG, HumanMessage(content=query)]
        response = context.llm.invoke(llm_messages)

        duration_ms = (time.perf_counter() - start) * 1000
        context.trace.append(
            trace_event("skill_end", skill=self.name, duration_ms=duration_ms)
        )

        return SkillResult(
            answer=response.content,
            skill_name=self.name,
            tools_used=[],
        )
