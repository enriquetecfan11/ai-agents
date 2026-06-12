"""Backends de chat reutilizables desde CLI y TUI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage


@dataclass
class ChatReply:
    text: str
    meta: str = ""


@dataclass
class ChatBackend(ABC):
    title: str
    help_text: str

    @abstractmethod
    def send(self, user_input: str) -> ChatReply:
        """Envía un mensaje y devuelve la respuesta del asistente."""

    def handle_slash(self, user_input: str) -> str | None:
        """Procesa comandos. Devuelve mensaje de sistema o None si no aplica."""
        return None


@dataclass
class SimpleChatBackend(ChatBackend):
    title: str = "Chat simple"
    help_text: str = "LangGraph + Ollama sin memoria persistente."
    _history: list = field(default_factory=list)

    def send(self, user_input: str) -> ChatReply:
        from scripts.chatbot_simple import graph

        self._history.append(HumanMessage(content=user_input))
        result = graph.invoke({"messages": self._history})
        self._history = result["messages"]
        reply = self._history[-1]
        return ChatReply(text=str(reply.content))


@dataclass
class MemoryChatBackend(ChatBackend):
    title: str = "Memory"
    help_text: str = "Memoria por hilos. Comandos: /thread <id>, /reset"
    thread_id: str = "tui-memory-1"
    _config: dict = field(init=False)

    def __post_init__(self) -> None:
        self._config = {"configurable": {"thread_id": self.thread_id}}

    def handle_slash(self, user_input: str) -> str | None:
        if user_input == "/reset":
            self.thread_id = f"tui-memory-reset-{id(self)}"
            self._config = {"configurable": {"thread_id": self.thread_id}}
            return "Memoria reiniciada."
        if user_input.startswith("/thread "):
            self.thread_id = user_input.split(" ", 1)[1].strip()
            self._config = {"configurable": {"thread_id": self.thread_id}}
            return f"thread_id = {self.thread_id}"
        return None

    def send(self, user_input: str) -> ChatReply:
        from scripts.chatbot_memory import graph

        parts: list[str] = []
        for chunk, _metadata in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=self._config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage) and chunk.content:
                text = chunk.content
                if isinstance(text, str):
                    parts.append(text)
        return ChatReply(text="".join(parts) or "[Sin respuesta]")


@dataclass
class RagChatBackend(ChatBackend):
    title: str = "RAG"
    help_text: str = "Recuperación sobre ChromaDB. Comandos: /thread <id>, /state"
    thread_id: str = "tui-rag-1"
    _config: dict = field(init=False)

    def __post_init__(self) -> None:
        self._config = {"configurable": {"thread_id": self.thread_id}}

    def handle_slash(self, user_input: str) -> str | None:
        if user_input.startswith("/thread "):
            self.thread_id = user_input.split(" ", 1)[1].strip()
            self._config = {"configurable": {"thread_id": self.thread_id}}
            return f"thread_id = {self.thread_id}"
        if user_input == "/state":
            from scripts.chatbot_rag import graph

            state = graph.get_state(config=self._config)
            return str(state)
        return None

    def send(self, user_input: str) -> ChatReply:
        from scripts.chatbot_rag import graph

        final_response = None
        for chunk in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=self._config,
            stream_mode="values",
        ):
            messages = chunk.get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                final_response = messages[-1]

        if final_response:
            return ChatReply(text=str(final_response.content))
        return ChatReply(text="[Sin respuesta]")


@dataclass
class SkillsChatBackend(ChatBackend):
    title: str = "Skills"
    help_text: str = "Routing por intención. Comandos: /thread <id>, /trace, /state"
    thread_id: str = "tui-skills-1"
    _config: dict = field(init=False)

    def __post_init__(self) -> None:
        self._config = {"configurable": {"thread_id": self.thread_id}}

    def handle_slash(self, user_input: str) -> str | None:
        if user_input.startswith("/thread "):
            self.thread_id = user_input.split(" ", 1)[1].strip()
            self._config = {"configurable": {"thread_id": self.thread_id}}
            return f"thread_id = {self.thread_id}"
        if user_input == "/trace":
            from scripts.chatbot_skills import graph

            state = graph.get_state(config=self._config)
            values = state.values if state else {}
            lines = [event.format_line() for event in values.get("trace", [])[-20:]]
            return "\n".join(lines) or "(sin eventos de trace)"
        if user_input == "/state":
            from scripts.chatbot_skills import graph

            state = graph.get_state(config=self._config)
            return str(state)
        return None

    def send(self, user_input: str) -> ChatReply:
        from scripts.chatbot_skills import graph

        final_response = None
        final_intent = ""
        final_skill = ""

        for chunk in graph.stream(
            {
                "messages": [HumanMessage(content=user_input)],
                "trace": [],
                "context": "",
                "intent": "",
                "last_skill": "",
            },
            config=self._config,
            stream_mode="values",
        ):
            messages = chunk.get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                final_response = messages[-1]
            final_intent = chunk.get("intent", final_intent)
            final_skill = chunk.get("last_skill", final_skill)

        if final_response:
            meta = f"intent={final_intent} | skill={final_skill}"
            return ChatReply(text=str(final_response.content), meta=meta)
        return ChatReply(text="[Sin respuesta]")


def get_chat_backend(mode: str) -> ChatBackend:
    backends = {
        "simple": SimpleChatBackend,
        "rag": RagChatBackend,
        "memory": MemoryChatBackend,
        "skills": SkillsChatBackend,
    }
    factory = backends.get(mode)
    if factory is None:
        raise ValueError(f"Modo de chat desconocido: {mode}")
    return factory()
