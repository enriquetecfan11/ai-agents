"""
Ejemplo mínimo: chatbot con LangGraph y Ollama sin memoria persistente.
"""

from typing import Annotated

from typing_extensions import TypedDict

from src.python_agents.paths import setup_import_path

setup_import_path()

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.graph.message import add_messages  # noqa: E402

from src.python_agents.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL  # noqa: E402


class State(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOllama(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

system_msg = SystemMessage(
    content="Eres un asistente útil y breve. Responde en español."
)


def chatbot(state: State):
    response = llm.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()


def main() -> None:
    history = []

    print("Chatbot LangGraph + Ollama. Escribe 'exit' para salir.\n")

    while True:
        user_input = input("Tú: ").strip()
        if user_input.lower() in {"exit", "quit", "salir"}:
            print("Saliendo.")
            break

        history.append(HumanMessage(content=user_input))
        result = graph.invoke({"messages": history})
        history = result["messages"]

        assistant_msg = history[-1]
        print(f"Bot: {assistant_msg.content}\n")


if __name__ == "__main__":
    main()
