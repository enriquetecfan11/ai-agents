"""Indexa los archivos Markdown de documentos/ en ChromaDB."""

from src.python_agents.paths import setup_import_path

setup_import_path()

from src.python_agents.ingest import ingest_markdown_to_chroma  # noqa: E402


def main() -> None:
    ingest_markdown_to_chroma()


if __name__ == "__main__":
    main()
