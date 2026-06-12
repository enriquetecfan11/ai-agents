"""
Ejemplo mínimo: agente con skills, routing por intención y trazabilidad.

Preguntas de prueba:
  - "¿Qué CVEs menciona la documentación?"  → rag
  - "Calcula 15 * 3"                         → example
  - "Hola"                                   → general
"""

from src.python_agents.paths import setup_import_path

setup_import_path()

from langchain_core.messages import HumanMessage  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

from src.python_agents.agents.skills_graph import build_skills_graph  # noqa: E402
from src.python_agents.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL  # noqa: E402


def main() -> None:
    llm = ChatOllama(
        model=OLLAMA_CHAT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.2,
    )
    graph = build_skills_graph(llm)

    print("Agente con Skills (LangGraph + Ollama)")
    print("Comandos: exit, quit, salir\n")

    while True:
        user_input = input("Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "salir"}:
            print("Saliendo.")
            break

        result = graph.invoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "trace": [],
                "context": "",
                "intent": "",
                "last_skill": "",
            }
        )

        answer = result["messages"][-1].content
        intent = result.get("intent", "?")
        skill = result.get("last_skill", "?")

        print(f"Bot: {answer}")
        print(f"  [intent={intent} | skill={skill}]")
        for event in result.get("trace", []):
            print(f"  {event.format_line()}")
        print()


if __name__ == "__main__":
    main()
