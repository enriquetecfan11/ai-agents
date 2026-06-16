"""Chatbot RAG con LangGraph, Ollama y ChromaDB."""

from typing import Annotated

from typing_extensions import TypedDict

from agents.paths import setup_import_path

setup_import_path()

from langchain_chroma import Chroma  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: E402
from langchain_ollama import ChatOllama, OllamaEmbeddings  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.graph.message import add_messages  # noqa: E402

from agents.config import (  # noqa: E402
    CHROMA_DIR,
    COLLECTION_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    OLLAMA_EMBED_MODEL,
)
from agents.llm_feedback import print_response_feedback  # noqa: E402

embeddings = OllamaEmbeddings(
    model=OLLAMA_EMBED_MODEL,
    base_url=OLLAMA_BASE_URL,
)

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
)

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 8},
)

llm = ChatOllama(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str


system_msg = SystemMessage(
    content=(
        "Eres un asistente técnico en español. "
        "Usa el contexto recuperado si es relevante. "
        "Si no hay suficiente contexto, dilo claramente y no inventes."
    )
)


def retrieve_node(state: State):
    last_message = state["messages"][-1]
    query = last_message.content

    docs = retriever.invoke(query)
    context = "\n\n---\n\n".join(
        f"Fuente: {doc.metadata.get('source', 'desconocida')}\n{doc.page_content}"
        for doc in docs
    )

    return {"context": context}


def generate_node(state: State):
    messages = state["messages"]
    context = state.get("context", "")
    last_user_msg = messages[-1].content

    prompt = f"""
Contexto recuperado:
\"\"\"
{context}
\"\"\"

Pregunta del usuario:
{last_user_msg}

Instrucciones:
- Responde en español.
- Prioriza el contexto recuperado.
- Si el contexto no basta, dilo.
- Sé claro y técnico.
"""

    response = llm.invoke([system_msg, HumanMessage(content=prompt)])
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


def chat() -> None:
    thread_id = "rag-demo-1"
    config = {"configurable": {"thread_id": thread_id}}

    print("LangGraph + Ollama + Chroma")
    print("Comandos: /exit, /thread <id>, /state\n")

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

        if user_input == "/state":
            state = graph.get_state(config=config)
            print(state)
            print()
            continue

        print("Enviando mensaje...", flush=True)
        print("Recibiendo respuesta...", flush=True)
        print("Bot: ", end="", flush=True)

        final_response = None
        for chunk in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="values",
        ):
            messages = chunk.get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                final_response = messages[-1]

        if final_response:
            print(final_response.content)
            print_response_feedback(final_response)
            print()
        else:
            print("[Sin respuesta]\n")


if __name__ == "__main__":
    chat()
