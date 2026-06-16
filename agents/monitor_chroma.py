"""Inspecciona colecciones y registros en ChromaDB."""

import json

import chromadb

from agents.paths import setup_import_path

setup_import_path()

from agents.config import CHROMA_DIR  # noqa: E402

PEEK_LIMIT = 3


def main() -> None:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collections = client.list_collections()

    if not collections:
        print("No hay colecciones en ChromaDB.")
        return

    print(f"Ruta Chroma: {CHROMA_DIR}\n")
    print(f"Colecciones encontradas: {len(collections)}\n")

    for col_info in collections:
        col = client.get_collection(col_info.name)
        count = col.count()
        all_data = col.get()

        print("=" * 80)
        print(f"Colección: {col.name}")
        print(f"Total de registros: {count}")

        # Estadísticas de fuentes
        source_counts: dict[str, int] = {}
        metadatas = all_data.get("metadatas", []) or []
        for meta in metadatas:
            if meta and "source" in meta:
                source = meta["source"]
                source_counts[source] = source_counts.get(source, 0) + 1

        if source_counts:
            print(f"Fuentes únicas: {len(source_counts)}")
            print("-" * 80)
            for source, count_chunks in sorted(source_counts.items(), key=lambda x: -x[1]):
                print(f"  {source}: {count_chunks} chunks")
        print("-" * 80)

        # Preview de algunos registros
        peek = col.peek(limit=PEEK_LIMIT)
        ids = peek.get("ids", [])
        docs = peek.get("documents", [])
        metas = peek.get("metadatas", [])

        if not ids:
            print("Colección vacía.\n")
            continue

        print(f"Preview ({len(ids)} de {count} registros):")
        for i, doc_id in enumerate(ids):
            print(f"[{i + 1}] ID: {doc_id}")

            meta = metas[i] if i < len(metas) else None
            if meta:
                print("Metadata:")
                print(json.dumps(meta, indent=2, ensure_ascii=False))

            doc = docs[i] if i < len(docs) else None
            if doc:
                preview = doc[:500].replace("\n", " ")
                print(f"Doc preview: {preview}")

            print("-" * 40)

        print()


if __name__ == "__main__":
    main()
