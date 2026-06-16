"""Indexa los archivos Markdown de documentos/ en ChromaDB."""

from agents.paths import setup_import_path

setup_import_path()

from agents.ingest import ingest_markdown_to_chroma  # noqa: E402


def main() -> None:
    ingest_markdown_to_chroma()


if __name__ == "__main__":
    main()
