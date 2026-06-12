"""Clasificación de intención para routing automático."""

from __future__ import annotations

from enum import Enum

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.python_agents.skills.registry import SkillRegistry


class Intent(str, Enum):
    RAG = "rag"
    EXAMPLE = "example"
    GENERAL = "general"


class _IntentClassification(BaseModel):
    intent: str = Field(description="Uno de: rag, example, general")
    confidence: float = Field(ge=0.0, le=1.0, description="Confianza de 0 a 1")
    reasoning: str = Field(default="", description="Breve justificación")


_RAG_KEYWORDS = ("cve", "documento", "documentación", "política", "vulnerabilidad", "índice")
_EXAMPLE_KEYWORDS = ("calcular", "calcula", "eco", "repite", "prueba la skill", "ejemplo")


def _keyword_fallback(query: str) -> Intent:
    lower = query.lower()
    if any(kw in lower for kw in _RAG_KEYWORDS):
        return Intent.RAG
    if any(kw in lower for kw in _EXAMPLE_KEYWORDS):
        return Intent.EXAMPLE
    return Intent.GENERAL


def classify_intent(
    query: str,
    llm: BaseChatModel,
    registry: SkillRegistry,
) -> tuple[Intent, dict]:
    descriptions = registry.intent_descriptions()
    options = "\n".join(f"- {k}: {v}" for k, v in descriptions.items())

    prompt = f"""
Clasifica la intención del usuario en una de estas categorías:
{options}

Mensaje del usuario:
{query}

Responde con el intent más adecuado (rag, example o general).
"""
    try:
        structured_llm = llm.with_structured_output(_IntentClassification)
        result = structured_llm.invoke(
            [
                SystemMessage(content="Eres un clasificador de intenciones. Responde en español."),
                HumanMessage(content=prompt),
            ]
        )
        intent_str = result.intent.lower().strip()
        if intent_str not in descriptions:
            intent = _keyword_fallback(query)
            meta = {"confidence": 0.5, "reasoning": "fallback_keywords", "raw_intent": intent_str}
        else:
            intent = Intent(intent_str)
            meta = {
                "confidence": result.confidence,
                "reasoning": result.reasoning,
            }
        return intent, meta
    except Exception:
        intent = _keyword_fallback(query)
        return intent, {"confidence": 0.5, "reasoning": "fallback_keywords", "error": True}
