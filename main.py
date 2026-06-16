import argparse
import sys

from agents.paths import setup_import_path

setup_import_path()


def _run_fetch(args: argparse.Namespace) -> None:
    from agents.fetch_and_index import main
    if args.urls:
        sys.argv = ["fetch_and_index.py", *args.urls]
    main()


def _run_index(_: argparse.Namespace) -> None:
    from agents.index_documents import main
    main()


def _run_simple(_: argparse.Namespace) -> None:
    from agents.chatbot_simple import chat
    chat()


def _run_rag(_: argparse.Namespace) -> None:
    from agents.chatbot_rag import chat
    chat()


def _run_memory(_: argparse.Namespace) -> None:
    from agents.chatbot_memory import chat
    chat()


def _run_monitor(_: argparse.Namespace) -> None:
    from agents.monitor_chroma import main
    main()


def _run_skills(_: argparse.Namespace) -> None:
    from agents.chatbot_skills import chat
    chat()


def _run_all(_: argparse.Namespace) -> None:
    from agents.fetch_and_index import main as fetch_main
    from agents.chatbot_rag import chat
    fetch_main()
    chat()


def _run_tui(_: argparse.Namespace) -> None:
    from agents.tui import run_tui
    run_tui()


COMMANDS = {
    "fetch": _run_fetch,
    "index": _run_index,
    "simple": _run_simple,
    "rag": _run_rag,
    "memory": _run_memory,
    "monitor": _run_monitor,
    "skills": _run_skills,
    "all": _run_all,
    "tui": _run_tui,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Asistente RAG local con Ollama, ChromaDB y LangGraph.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Descargar URLs e indexar en Chroma")
    fetch_parser.add_argument("urls", nargs="*", help="URLs opcionales (si no, usa urls.txt)")
    fetch_parser.set_defaults(func=COMMANDS["fetch"])

    subparsers.add_parser("index", help="Indexar Markdown existente en documentos/").set_defaults(func=COMMANDS["index"])
    subparsers.add_parser("simple", help="Chat simple con Ollama (sin RAG)").set_defaults(func=COMMANDS["simple"])
    subparsers.add_parser("rag", help="Chat RAG interactivo").set_defaults(func=COMMANDS["rag"])
    subparsers.add_parser("memory", help="Chat con memoria por hilos").set_defaults(func=COMMANDS["memory"])
    subparsers.add_parser("monitor", help="Inspeccionar colecciones ChromaDB").set_defaults(func=COMMANDS["monitor"])
    subparsers.add_parser("skills", help="Chat con skills, routing por intención y trazabilidad").set_defaults(func=COMMANDS["skills"])
    subparsers.add_parser("all", help="Flujo completo: fetch + rag").set_defaults(func=COMMANDS["all"])
    subparsers.add_parser("tui", help="Interfaz TUI para lanzar acciones").set_defaults(func=COMMANDS["tui"])

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()