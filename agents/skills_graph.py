"""Grafo LangGraph con routing por intención y ejecución de skills."""

from __future__ import annotations

from typing import Annotated

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agents.skills.base import SkillContext
from agents.skills.registry import SkillRegistry, build_default_registry
from agents.skills.router import classify_intent
from agents.skills.tracing import TraceEvent, append_trace, trace_event


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    trace: Annotated[list[TraceEvent], append_trace]
    context: str
    last_skill: str


def build_skills_graph(
    llm: BaseChatModel,
    registry: SkillRegistry | None = None,
    *,
    checkpointer: BaseCheckpointSaver | None = None,
):
    registry = registry or build_default_registry()

    def classify_node(state: AgentState) -> dict:
        last_message = state["messages"][-1]
        query = last_message.content
        intent, meta = classify_intent(query, llm, registry)
        return {
            "intent": intent,
            "trace": [
                trace_event(
                    "intent_classified",
                    detail={"intent": intent, **meta},
                )
            ],
        }

    def execute_skill_node(state: AgentState) -> dict:
        query = state["messages"][-1].content
        intent = state.get("intent", "general")
        skill = registry.get_by_intent(intent)

        local_trace: list[TraceEvent] = []
        skill_context = SkillContext(
            llm=llm,
            trace=local_trace,
            state={"messages": state["messages"]},
        )
        result = skill.run(query, skill_context)

        return {
            "messages": [AIMessage(content=result.answer)],
            "trace": local_trace,
            "context": skill_context.state.get("context", ""),
            "last_skill": result.skill_name,
        }

    builder = StateGraph(AgentState)
    builder.add_node("classify", classify_node)
    builder.add_node("execute_skill", execute_skill_node)
    builder.add_edge(START, "classify")
    builder.add_edge("classify", "execute_skill")
    builder.add_edge("execute_skill", END)

    return builder.compile(checkpointer=checkpointer)
