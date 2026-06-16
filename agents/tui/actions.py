"""Definición de acciones disponibles en el launcher TUI."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Callable, Literal


Runner = Callable[[argparse.Namespace], None]
ActionKind = Literal["pipeline", "chat"]


@dataclass(frozen=True)
class ActionDef:
    id: str
    label: str
    description: str
    category: str
    kind: ActionKind = "pipeline"
    enabled: bool = True
    runner: Runner | None = None


def _lazy_runner(name: str) -> Runner:
    def _run(args: argparse.Namespace) -> None:
        import main

        getattr(main, name)(args)

    return _run


PIPELINE_ACTIONS: tuple[ActionDef, ...] = (
    ActionDef(
        id="fetch",
        label="Fetch",
        description="Descarga URLs (urls.txt) y las indexa en ChromaDB.",
        category="pipeline",
        runner=_lazy_runner("_run_fetch"),
    ),
    ActionDef(
        id="index",
        label="Index",
        description="Indexa los Markdown existentes en documentos/.",
        category="pipeline",
        runner=_lazy_runner("_run_index"),
    ),
    ActionDef(
        id="monitor",
        label="Monitor",
        description="Inspecciona colecciones y metadatos en ChromaDB.",
        category="pipeline",
        runner=_lazy_runner("_run_monitor"),
    ),
    ActionDef(
        id="all",
        label="All",
        description="Flujo fetch + chat RAG (mismo que python main.py all, sin bloquear la TUI).",
        category="pipeline",
        runner=_lazy_runner("_run_fetch"),
    ),
)

CHAT_ACTIONS: tuple[ActionDef, ...] = (
    ActionDef(
        id="simple",
        label="Simple",
        description="Chat directo con Ollama, sin RAG ni memoria persistente.",
        category="chat",
        kind="chat",
    ),
    ActionDef(
        id="rag",
        label="RAG",
        description="Chat con recuperación de documentos desde ChromaDB.",
        category="chat",
        kind="chat",
    ),
    ActionDef(
        id="memory",
        label="Memory",
        description="Chat con memoria por hilos (MemorySaver).",
        category="chat",
        kind="chat",
    ),
    ActionDef(
        id="skills",
        label="Skills",
        description="Agente con routing por intención y trazabilidad.",
        category="chat",
        kind="chat",
    ),
)

ALL_ACTIONS: tuple[ActionDef, ...] = PIPELINE_ACTIONS + CHAT_ACTIONS

ACTION_BY_ID: dict[str, ActionDef] = {action.id: action for action in ALL_ACTIONS}
