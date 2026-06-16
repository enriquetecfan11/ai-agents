"""Tool de búsqueda semántica sobre ChromaDB."""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from agents.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
)
from tools.base import ToolResult


class ChromaSearchTool:
    name = "chroma_search"
    description = (
        "Busca documentos relevantes en la base vectorial ChromaDB "
        "usando búsqueda semántica MMR."
    )

    def __init__(
        self,
        *,
        k: int = 4,
        fetch_k: int = 8,
        vectorstore: Chroma | None = None,
    ) -> None:
        self._k = k
        self._fetch_k = fetch_k
        self._vectorstore = vectorstore or self._build_vectorstore()

    def _build_vectorstore(self) -> Chroma:
        embeddings = OllamaEmbeddings(
            model=OLLAMA_EMBED_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
        return Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
        )

    def invoke(self, *, query: str, **_: object) -> ToolResult:
        retriever = self._vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": self._k, "fetch_k": self._fetch_k},
        )
        docs = retriever.invoke(query)
        if not docs:
            return ToolResult(
                output="",
                metadata={"doc_count": 0, "sources": []},
            )

        sources: list[str] = []
        chunks: list[str] = []
        for doc in docs:
            source = doc.metadata.get("source", "desconocida")
            sources.append(source)
            chunks.append(f"Fuente: {source}\n{doc.page_content}")

        context = "\n\n---\n\n".join(chunks)
        return ToolResult(
            output=context,
            metadata={"doc_count": len(docs), "sources": sources},
        )
