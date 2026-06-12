from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.python_agents.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    DOCUMENTS_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
)


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def load_markdown_documents(folder: Path) -> list:
    if not folder.exists():
        return []

    loader = DirectoryLoader(
        path=str(folder),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    return loader.load()


def enrich_document_metadata(documents: list) -> None:
    for doc in documents:
        source = doc.metadata.get("source", "")
        path = Path(source)
        doc.metadata["filename"] = path.name
        doc.metadata["folder"] = str(path.parent)


def split_documents(documents: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_documents(documents)


def ingest_markdown_to_chroma(
    documents_dir: Path | None = None,
    chroma_dir: str | None = None,
    collection_name: str | None = None,
) -> tuple[int, int]:
    """Indexa archivos Markdown en ChromaDB. Devuelve (documentos, chunks)."""
    docs_path = documents_dir or DOCUMENTS_DIR
    persist_dir = chroma_dir or CHROMA_DIR
    collection = collection_name or COLLECTION_NAME

    if not docs_path.exists():
        print(f"[INFO] No existe la carpeta {docs_path}. Nada que indexar.")
        return 0, 0

    documents = load_markdown_documents(docs_path)
    if not documents:
        print("[INFO] No hay archivos .md para indexar.")
        return 0, 0

    enrich_document_metadata(documents)
    chunks = split_documents(documents)
    if not chunks:
        print("[INFO] No se generaron chunks.")
        return len(documents), 0

    vectorstore = Chroma(
        collection_name=collection,
        persist_directory=persist_dir,
        embedding_function=get_embeddings(),
    )
    vectorstore.add_documents(chunks)

    print(f"[OK] Documentos cargados: {len(documents)}")
    print(f"[OK] Chunks generados: {len(chunks)}")
    print(f"[OK] Colección: {collection}")
    print(f"[OK] Persistido en: {persist_dir}")
    return len(documents), len(chunks)
