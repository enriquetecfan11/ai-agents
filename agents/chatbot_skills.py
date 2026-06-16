"""Chatbot interactivo con skills, routing por intención y trazabilidad."""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

from agents.skills_graph import build_skills_graph
from agents.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL
from agents.llm_feedback import print_response_feedback
from agents.paths import setup_import_path

setup_import_path()

llm = ChatOllama(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

memory = MemorySaver()
graph = build_skills_graph(llm, checkpointer=memory)


def _print_trace(events: list, limit: int = 20) -> None:
    for event in events[-limit:]:
        print(event.format_line())


def chat() -> None:
    thread_id = "skills-demo-1"
    config = {"configurable": {"thread_id": thread_id}}

    print("Agente con Skills (LangGraph + Ollama + Chroma)")
    print("Comandos: /exit, /thread <id>, /trace, /state\n")

    while True:
        user_input = input("Tú: ").strip()

        if not user_input:
            continue

        if user_input in {"/exit", "/quit", "/salir"}:
            print("Saliendo.")
            break

        if user_input.startswith("/thread "):
            thread_id = user_input.split(" ", 1)[1].strip()
            config = {"configurable": {"thread_id": thread_id}}
            print(f"thread_id cambiado a: {thread_id}\n")
            continue

        if user_input == "/trace":
            state = graph.get_state(config=config)
            values = state.values if state else {}
            _print_trace(values.get("trace", []))
            print()
            continue

        if user_input == "/state":
            state = graph.get_state(config=config)
            print(state)
            print()
            continue

        print("Enviando mensaje...", flush=True)
        print("Recibiendo respuesta...", flush=True)
        print("Bot: ", end="", flush=True)

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
            config=config,
            stream_mode="values",
        ):
            messages = chunk.get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                final_response = messages[-1]
            final_intent = chunk.get("intent", final_intent)
            final_skill = chunk.get("last_skill", final_skill)

        if final_response:
            print(final_response.content)
            print_response_feedback(final_response)
            print(f"  [intent={final_intent} | skill={final_skill}]")
            print()
        else:
            print("[Sin respuesta]\n")


if __name__ == "__main__":
    chat()
