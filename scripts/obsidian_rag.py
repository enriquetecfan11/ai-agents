"""
EXPERIMENTAL: RAG sobre un vault de Obsidian.

Requiere OBSIDIAN_VAULT_PATH en .env apuntando a la carpeta del vault.
"""

from pathlib import Path
from uuid import uuid4

from src.python_agents.paths import setup_import_path

setup_import_path()

from chromadb import PersistentClient  # noqa: E402
from langchain_chroma import Chroma  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from langchain_ollama import ChatOllama, OllamaEmbeddings  # noqa: E402

from src.python_agents.config import (  # noqa: E402
    OBSIDIAN_VAULT_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    OLLAMA_EMBED_MODEL,
)

CHROMA_PATH = "./data/chroma"
COLLECTION_NAME = "obsidian_notes"


def get_vault_path() -> Path:
    if not OBSIDIAN_VAULT_PATH:
        raise SystemExit(
            "Define OBSIDIAN_VAULT_PATH en .env con la ruta a tu vault de Obsidian."
        )

    vault = Path(OBSIDIAN_VAULT_PATH)
    if not vault.exists():
        raise SystemExit(f"La ruta del vault no existe: {vault}")

    return vault


embeddings = OllamaEmbeddings(
    model=OLLAMA_EMBED_MODEL,
    base_url=OLLAMA_BASE_URL,
)

llm = ChatOllama(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

client = PersistentClient(path=CHROMA_PATH)

vectorstore = Chroma(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
)


def load_markdown_documents(folder: Path) -> list[Document]:
    docs = []
    for path in folder.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        if not text.strip():
            continue

        docs.append(Document(page_content=text, metadata={"source": str(path)}))
    return docs


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def build_index(vault_path: Path) -> None:
    raw_docs = load_markdown_documents(vault_path)
    chunked_docs = []
    ids = []

    for doc in raw_docs:
        chunks = chunk_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            chunked_docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": doc.metadata["source"],
                        "chunk": i,
                    },
                )
            )
            ids.append(str(uuid4()))

    if chunked_docs:
        vectorstore.add_documents(documents=chunked_docs, ids=ids)
        print(f"Indexados {len(chunked_docs)} chunks.")
    else:
        print("No se encontraron documentos.")


def ask(query: str, k: int = 4) -> None:
    docs = vectorstore.similarity_search(query, k=k)
    context = "\n\n---\n\n".join(
        f"Fuente: {d.metadata.get('source')}\n{d.page_content}" for d in docs
    )

    prompt = f"""
Responde en español usando solo el contexto si es suficiente.
Si falta información, dilo claramente.

Pregunta:
{query}

Contexto:
{context}
"""

    response = llm.invoke(prompt)

    print("\nRespuesta:\n")
    print(response.content)
    print("\nFuentes:\n")
    for doc in docs:
        print("-", doc.metadata.get("source"))


def main() -> None:
    vault_path = get_vault_path()
    mode = input("Modo [index/query]: ").strip().lower()

    if mode == "index":
        build_index(vault_path)
    elif mode == "query":
        question = input("Pregunta: ").strip()
        ask(question)
    else:
        print("Modo no válido.")


if __name__ == "__main__":
    main()
