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
        peek = col.peek(limit=PEEK_LIMIT)

        print("=" * 80)
        print(f"Colección: {col.name}")
        print(f"Registros: {count}")
        print("-" * 80)

        ids = peek.get("ids", [])
        docs = peek.get("documents", [])
        metas = peek.get("metadatas", [])

        if not ids:
            print("Vacía.\n")
            continue

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
