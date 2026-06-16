"""Chatbot con memoria de conversación usando LangGraph y Ollama."""

from typing import Annotated

from typing_extensions import TypedDict

from agents.paths import setup_import_path

setup_import_path()

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.graph.message import add_messages  # noqa: E402

from agents.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL  # noqa: E402


class State(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOllama(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

system_msg = SystemMessage(
    content="Eres un asistente útil, claro y breve. Responde en español."
)


def chatbot(state: State):
    response = llm.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


def chat() -> None:
    thread_id = "demo-chat-1"
    config = {"configurable": {"thread_id": thread_id}}

    print("Chatbot LangGraph + Ollama")
    print("Comandos: /exit, /reset, /thread <id>\n")

    while True:
        user_input = input("Tú: ").strip()

        if not user_input:
            continue

        if user_input in {"/exit", "/quit", "/salir"}:
            print("Saliendo.")
            break

        if user_input == "/reset":
            thread_id = "demo-chat-reset"
            config = {"configurable": {"thread_id": thread_id}}
            print("Memoria reiniciada.\n")
            continue

        if user_input.startswith("/thread "):
            thread_id = user_input.split(" ", 1)[1].strip()
            config = {"configurable": {"thread_id": thread_id}}
            print(f"Cambiado a thread_id={thread_id}\n")
            continue

        print("Bot: ", end="", flush=True)

        for chunk, _metadata in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessage) and chunk.content:
                text = chunk.content
                if isinstance(text, str):
                    print(text, end="", flush=True)

        print("\n")


if __name__ == "__main__":
    chat()
