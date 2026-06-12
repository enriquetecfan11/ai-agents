"""Ejecución de tools asociadas a skills Markdown."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.python_agents.skills.base import SkillContext
from src.python_agents.skills.loader import SkillDefinition
from src.python_agents.tools.base import BaseTool, ToolResult
from src.python_agents.tools.chroma_search import ChromaSearchTool
from src.python_agents.tools.example_tools import CalcTool, EchoTool

_TOOL_REGISTRY: dict[str, BaseTool] = {
    "chroma_search": ChromaSearchTool(),
    "echo_tool": EchoTool(),
    "calc_tool": CalcTool(),
}


def resolve_tools(definition: SkillDefinition) -> list[BaseTool]:
    tools: list[BaseTool] = []
    for name in definition.allowed_tools:
        tool = _TOOL_REGISTRY.get(name)
        if tool:
            tools.append(tool)
    return tools


class _ToolChoice(BaseModel):
    tool: str = Field(description="Nombre de la tool disponible")
    text: str = Field(default="", description="Texto para echo_tool")
    expression: str = Field(default="", description="Expresión para calc_tool")
    reasoning: str = Field(default="")


def _keyword_tool_fallback(query: str, available: list[str]) -> _ToolChoice:
    lower = query.lower()
    if "calc_tool" in available and any(
        kw in lower for kw in ("calcular", "calcula", "suma", "multiplica")
    ):
        expr = query
        for prefix in ("calcula ", "calcular ", "cuánto es ", "cuanto es "):
            if lower.startswith(prefix):
                expr = query[len(prefix) :].strip()
                break
        return _ToolChoice(tool="calc_tool", expression=expr, reasoning="keyword_fallback")
    if "echo_tool" in available:
        return _ToolChoice(tool="echo_tool", text=query, reasoning="keyword_fallback")
    return _ToolChoice(tool=available[0], reasoning="keyword_fallback")


def run_tools_for_skill(
    definition: SkillDefinition,
    query: str,
    context: SkillContext,
    call_tool,
) -> tuple[str, list[str], dict]:
    """Ejecuta tools según la skill y devuelve contexto, tools usadas y metadata."""
    tools = resolve_tools(definition)
    if not tools:
        return "", [], {}

    tool_names = [t.name for t in tools]

    if "chroma_search" in tool_names:
        search = _TOOL_REGISTRY["chroma_search"]
        result: ToolResult = call_tool(search, query=query)
        context.state["context"] = result.output
        return result.output, [search.name], {
            "doc_count": result.metadata.get("doc_count", 0),
            "sources": result.metadata.get("sources", []),
        }

    if tool_names and all(n in ("echo_tool", "calc_tool") for n in tool_names):
        tool_map = {t.name: t for t in tools}
        choice = _select_example_tool(query, context, tool_names)
        tool = tool_map.get(choice.tool, tools[0])
        if tool.name == "calc_tool":
            result = call_tool(tool, expression=choice.expression or query)
        else:
            result = call_tool(tool, text=choice.text or query)
        tool_context = f"Tool `{tool.name}` → {result.output}"
        return tool_context, [tool.name], {"tool_choice": choice.tool}

    return "", [], {}


def _select_example_tool(query: str, context: SkillContext, available: list[str]) -> _ToolChoice:
    tool_lines = "\n".join(f"- {name}" for name in available)
    prompt = f"""
El usuario escribió: {query}

Tools disponibles:
{tool_lines}

Elige la tool más adecuada y rellena los argumentos (text o expression).
"""
    try:
        structured_llm = context.llm.with_structured_output(_ToolChoice)
        return structured_llm.invoke(
            [
                SystemMessage(content="Elige una tool para la petición."),
                HumanMessage(content=prompt),
            ]
        )
    except Exception:
        return _keyword_tool_fallback(query, available)
