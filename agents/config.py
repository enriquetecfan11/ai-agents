import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "gemma4:e2b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "web_docs")
DOCUMENTS_DIR = Path(os.getenv("DOCUMENTS_DIR", "documentos"))
JINA_API_KEY = os.getenv("JINA_API_KEY") or None
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "")
URLS_FILE = ROOT_DIR / "urls.txt"

# Agent Skills (agentskills.io): rutas de descubrimiento, en orden de precedencia
SKILLS_SEARCH_PATHS: list[Path] = [
    ROOT_DIR / "skills",
    ROOT_DIR / "skills",
]
