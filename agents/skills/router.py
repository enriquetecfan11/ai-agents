"""Clasificación de intención para routing automático (Agent Skills catalog)."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agents.skills.registry import SkillRegistry

_RAG_KEYWORDS = ("cve", "documento", "documentación", "política", "vulnerabilidad", "índice")
_EXAMPLE_KEYWORDS = ("calcular", "calcula", "eco", "repite", "prueba la skill", "ejemplo")


class _IntentClassification(BaseModel):
    intent: str = Field(description="Nombre de la skill más adecuada")
    confidence: float = Field(ge=0.0, le=1.0, description="Confianza de 0 a 1")
    reasoning: str = Field(default="", description="Breve justificación")


def _keyword_fallback(query: str, valid_intents: set[str]) -> str:
    lower = query.lower()
    if "rag" in valid_intents and any(kw in lower for kw in _RAG_KEYWORDS):
        return "rag"
    if "example" in valid_intents and any(kw in lower for kw in _EXAMPLE_KEYWORDS):
        return "example"
    if "general" in valid_intents:
        return "general"
    return next(iter(valid_intents))


def classify_intent(
    query: str,
    llm: BaseChatModel,
    registry: SkillRegistry,
) -> tuple[str, dict]:
    descriptions = registry.intent_descriptions()
    if not descriptions:
        return "general", {"confidence": 0.0, "reasoning": "no_skills_loaded"}

    valid_intents = set(descriptions.keys())
    catalog = registry.catalog()
    skill_list = "\n".join(f"- {k}: {v}" for k, v in descriptions.items())

    prompt = f"""
Catálogo de skills disponibles (tier 1 — solo metadata):
{catalog}

Resumen:
{skill_list}

Clasifica la intención del usuario eligiendo el <name> de la skill más adecuada.

Mensaje del usuario:
{query}
"""
    try:
        structured_llm = llm.with_structured_output(_IntentClassification)
        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "Eres un clasificador de intenciones para Agent Skills. "
                        "Elige el name de la skill que mejor encaje."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )
        intent_str = result.intent.lower().strip()
        if intent_str not in valid_intents:
            intent = _keyword_fallback(query, valid_intents)
            meta = {
                "confidence": 0.5,
                "reasoning": "fallback_keywords",
                "raw_intent": intent_str,
            }
        else:
            intent = intent_str
            meta = {
                "confidence": result.confidence,
                "reasoning": result.reasoning,
            }
        return intent, meta
    except Exception:
        intent = _keyword_fallback(query, valid_intents)
        return intent, {"confidence": 0.5, "reasoning": "fallback_keywords", "error": True}
