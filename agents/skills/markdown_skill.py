"""Skill cargada desde SKILL.md (Agent Skills spec)."""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage, SystemMessage

from agents.skills.base import BaseSkill, SkillContext, SkillResult
from agents.skills.executors import resolve_tools, run_tools_for_skill
from agents.skills.loader import SkillDefinition
from agents.skills.tracing import trace_event


class MarkdownSkill(BaseSkill):
    """Ejecuta una skill definida en SKILL.md con progressive disclosure."""

    def __init__(self, definition: SkillDefinition) -> None:
        self.definition = definition
        self.name = definition.name
        self.description = definition.description
        self.intent_label = definition.name
        self.tools = resolve_tools(definition)

    def activate(self) -> str:
        """Tier 2: cuerpo de instrucciones sin frontmatter."""
        return self.definition.body

    def run(self, query: str, context: SkillContext) -> SkillResult:
        start = time.perf_counter()
        context.trace.append(trace_event("skill_start", skill=self.name))
        context.trace.append(
            trace_event(
                "skill_activated",
                skill=self.name,
                detail={
                    "location": str(self.definition.location),
                    "resources": self.definition.list_resources(),
                },
            )
        )

        tool_context, tools_used, tool_meta = run_tools_for_skill(
            self.definition,
            query,
            context,
            lambda tool, **kwargs: self._call_tool(tool, context, **kwargs),
        )

        instructions = self.activate()
        resources = self.definition.list_resources()
        resource_note = ""
        if resources:
            resource_note = "\n\nRecursos disponibles en el directorio de la skill:\n" + "\n".join(
                f"- {r}" for r in resources
            )

        messages = context.state.get("messages", [])

        system = SystemMessage(
            content=(
                f"Eres un agente ejecutando la skill '{self.name}'.\n\n"
                f"## Instrucciones\n\n{instructions}{resource_note}\n\n"
                "Responde en español siguiendo estas instrucciones."
            )
        )

        user_prompt = f"""
## Contexto de tools
{tool_context or "(sin contexto de tools)"}

## Pregunta del usuario
{query}
"""

        if messages and self.name == "general":
            prior = messages[:-1] if messages else []
            llm_messages = [system, *prior, HumanMessage(content=user_prompt)]
        else:
            llm_messages = [system, HumanMessage(content=user_prompt)]

        response = context.llm.invoke(llm_messages)
        duration_ms = (time.perf_counter() - start) * 1000
        context.trace.append(
            trace_event("skill_end", skill=self.name, duration_ms=duration_ms)
        )

        return SkillResult(
            answer=response.content,
            skill_name=self.name,
            tools_used=tools_used,
            metadata={
                "skill_location": str(self.definition.location),
                **tool_meta,
            },
        )
