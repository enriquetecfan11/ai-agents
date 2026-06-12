"""Skill RAG: consulta documentación indexada en ChromaDB."""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.python_agents.skills.base import BaseSkill, SkillContext, SkillResult
from src.python_agents.skills.tracing import trace_event
from src.python_agents.tools.chroma_search import ChromaSearchTool

_SYSTEM_MSG = SystemMessage(
    content=(
        "Eres un asistente técnico en español. "
        "Usa el contexto recuperado si es relevante. "
        "Si no hay suficiente contexto, dilo claramente y no inventes."
    )
)


class RagSkill(BaseSkill):
    name = "skill_rag"
    description = (
        "Responde preguntas sobre documentación técnica, CVEs, políticas "
        "y contenido indexado en la base de conocimiento."
    )
    intent_label = "rag"

    def __init__(self, search_tool: ChromaSearchTool | None = None) -> None:
        self.tools = [search_tool or ChromaSearchTool()]
        self._search = self.tools[0]

    def run(self, query: str, context: SkillContext) -> SkillResult:
        start = time.perf_counter()
        context.trace.append(trace_event("skill_start", skill=self.name))

        tool_result = self._call_tool(self._search, context, query=query)
        retrieved_context = tool_result.output
        context.state["context"] = retrieved_context

        prompt = f"""
Contexto recuperado:
\"\"\"
{retrieved_context or "(sin resultados)"}
\"\"\"

Pregunta del usuario:
{query}

Instrucciones:
- Responde en español.
- Prioriza el contexto recuperado.
- Si el contexto no basta, dilo.
- Sé claro y técnico.
"""
        response = context.llm.invoke([_SYSTEM_MSG, HumanMessage(content=prompt)])
        duration_ms = (time.perf_counter() - start) * 1000
        context.trace.append(
            trace_event("skill_end", skill=self.name, duration_ms=duration_ms)
        )

        return SkillResult(
            answer=response.content,
            skill_name=self.name,
            tools_used=[self._search.name],
            metadata={
                "doc_count": tool_result.metadata.get("doc_count", 0),
                "sources": tool_result.metadata.get("sources", []),
            },
        )
