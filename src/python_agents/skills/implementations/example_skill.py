"""Skill de ejemplo: demuestra el patrón de tools desacopladas."""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.python_agents.skills.base import BaseSkill, SkillContext, SkillResult
from src.python_agents.skills.tracing import trace_event
from src.python_agents.tools.example_tools import CalcTool, EchoTool


class _ToolChoice(BaseModel):
    tool: str = Field(description="Nombre de la tool: echo_tool o calc_tool")
    text: str = Field(default="", description="Texto para echo_tool")
    expression: str = Field(default="", description="Expresión para calc_tool")
    reasoning: str = Field(default="", description="Breve justificación de la elección")


class ExampleSkill(BaseSkill):
    name = "skill_example"
    description = (
        "Demuestra tools de ejemplo: repetir texto (eco) o calcular expresiones aritméticas. "
        "Úsala para pruebas del sistema de skills."
    )
    intent_label = "example"

    def __init__(self) -> None:
        self._echo = EchoTool()
        self._calc = CalcTool()
        self.tools = [self._echo, self._calc]
        self._tool_map = {t.name: t for t in self.tools}

    def _select_tool(self, query: str, context: SkillContext) -> _ToolChoice:
        structured_llm = context.llm.with_structured_output(_ToolChoice)
        prompt = f"""
El usuario escribió: {query}

Tools disponibles:
- echo_tool: repite y normaliza texto. Usa el campo "text".
- calc_tool: evalúa expresiones aritméticas. Usa el campo "expression".

Elige la tool más adecuada y rellena los argumentos correspondientes.
"""
        try:
            return structured_llm.invoke(
                [
                    SystemMessage(content="Clasifica la petición y elige una tool."),
                    HumanMessage(content=prompt),
                ]
            )
        except Exception:
            return self._keyword_fallback(query)

    def _keyword_fallback(self, query: str) -> _ToolChoice:
        lower = query.lower()
        if any(kw in lower for kw in ("calcular", "calcula", "suma", "multiplica")):
            expr = query
            for prefix in ("calcula ", "calcular ", "cuánto es ", "cuanto es "):
                if lower.startswith(prefix):
                    expr = query[len(prefix) :].strip()
                    break
            return _ToolChoice(tool="calc_tool", expression=expr, reasoning="keyword_fallback")
        return _ToolChoice(tool="echo_tool", text=query, reasoning="keyword_fallback")

    def run(self, query: str, context: SkillContext) -> SkillResult:
        start = time.perf_counter()
        context.trace.append(trace_event("skill_start", skill=self.name))

        choice = self._select_tool(query, context)
        tool = self._tool_map.get(choice.tool, self._echo)

        if tool.name == "calc_tool":
            tool_result = self._call_tool(tool, context, expression=choice.expression or query)
        else:
            tool_result = self._call_tool(tool, context, text=choice.text or query)

        answer = (
            f"Tool `{tool.name}` ejecutada.\n"
            f"Resultado: {tool_result.output}"
        )
        if choice.reasoning:
            answer += f"\n(Razón: {choice.reasoning})"

        duration_ms = (time.perf_counter() - start) * 1000
        context.trace.append(
            trace_event("skill_end", skill=self.name, duration_ms=duration_ms)
        )

        return SkillResult(
            answer=answer,
            skill_name=self.name,
            tools_used=[tool.name],
            metadata={"tool_choice": choice.tool},
        )
