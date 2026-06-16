# python-agents

Asistente RAG local con **Ollama**, **ChromaDB** y **LangGraph**. Descarga documentación web, la indexa como vectores y permite consultarla en español con contexto recuperado.

**Punto de entrada:** `main.py` (CLI). Atajo visual: `tui.py` o `python main.py tui`.

## Para qué sirve

Este proyecto automatiza un flujo de trabajo típico en ciberseguridad y documentación técnica:

1. Descargar páginas web como Markdown.
2. Indexarlas en una base vectorial local.
3. Consultarlas mediante un chatbot que recupera contexto relevante antes de responder.

## Qué problema resuelve

Evita copiar y pegar manualmente información de CVEs, advisories o notas técnicas. Centraliza la documentación en ChromaDB y permite hacer preguntas en lenguaje natural con respuestas basadas en el contenido indexado.

## Características principales

- Descarga de URLs a Markdown mediante [Jina Reader](https://jina.ai/reader/).
- Indexación en ChromaDB con embeddings de Ollama.
- Chatbot RAG con grafo LangGraph (nodos `retrieve` + `generate`).
- Chat con memoria de conversación por hilos (`thread_id`).
- Agente con **Agent Skills** (`skills/*/SKILL.md`).
- CLI unificada (`main.py`) y launcher TUI con **Textual** (`tui.py`).
- Utilidad para inspeccionar colecciones Chroma.
- Script experimental para vaults de Obsidian.

## Estructura del proyecto

```
python-agents/
├── main.py                   # CLI principal (entrypoint)
├── tui.py                    # Atajo → python main.py tui
├── script.ps1                # Setup + atajos PowerShell
├── requirements.txt
├── .env.example
├── urls.example.txt
├── skills/                 # Agent Skills (SKILL.md)
├── agents/                 # Scripts, configuración, ingest, skills, TUI
├── examples/                 # Ejemplos mínimos
├── docs/                     # Arquitectura y guías
├── data/                     # Runtime (gitignored)
└── documentos/               # Markdown descargado (gitignored)
```

## Requisitos

- Python 3.11 o superior
- [Ollama](https://ollama.com/) accesible (local o remoto)
- Modelos en Ollama: chat (`gemma4:e2b` por defecto) y embeddings (`mxbai-embed-large` por defecto)
- Conexión a internet para descargar URLs (solo en `fetch_and_index.py`)

## Instalación

```powershell
cd python-agents
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` con tu configuración real (especialmente `OLLAMA_BASE_URL`).

Para las URLs, copia la plantilla:

```powershell
copy urls.example.txt urls.txt
```

## Configuración de variables de entorno

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `OLLAMA_BASE_URL` | URL del servidor Ollama | `http://localhost:11434` |
| `OLLAMA_CHAT_MODEL` | Modelo de chat | `gemma4:e2b` |
| `OLLAMA_EMBED_MODEL` | Modelo de embeddings | `mxbai-embed-large` |
| `CHROMA_DIR` | Carpeta de persistencia Chroma | `chroma_db` |
| `CHROMA_COLLECTION` | Nombre de la colección | `web_docs` |
| `DOCUMENTS_DIR` | Carpeta de Markdown | `documentos` |
| `JINA_API_KEY` | Token opcional de Jina Reader | vacío |
| `OBSIDIAN_VAULT_PATH` | Ruta al vault Obsidian (experimental) | vacío |

## CLI (`main.py`)

Desde la raíz del proyecto:

```powershell
python main.py fetch              # Descargar URLs e indexar
python main.py fetch URL ...      # URLs opcionales por argumento
python main.py index              # Indexar documentos/ existentes
python main.py monitor            # Inspeccionar ChromaDB
python main.py all                # fetch + chat RAG (CLI)
python main.py simple             # Chat Ollama sin RAG
python main.py rag                # Chat RAG
python main.py memory             # Chat con memoria por hilos
python main.py skills             # Agente con skills y trace
python main.py tui                # Launcher visual (Textual)
```

### TUI (`tui.py`)

Equivalente a `python main.py tui`. Menú lateral con:

- **Pipeline:** fetch, index, monitor, all (fetch + abre RAG en pantalla)
- **Chat:** simple, rag, memory, skills

```powershell
python tui.py
```

### Scripts directos (compatibles)

Los guiones en `agents/` siguen siendo ejecutables de forma independiente:

```powershell
python agents/fetch_and_index.py
python agents/chatbot_rag.py
python agents/chatbot_memory.py
python agents/monitor_chroma.py
python examples/simple_chat.py      # ejemplo; preferir main.py simple
```

## Ejemplos de uso

### Flujo completo RAG

```powershell
copy .env.example .env
copy urls.example.txt urls.txt

python main.py fetch
python main.py rag
# o: python main.py tui
```

En el chat RAG:

- `/exit` — salir
- `/thread mi-hilo` — cambiar hilo de conversación
- `/state` — ver estado del grafo

## Flujo general de funcionamiento

```mermaid
flowchart LR
    urls[urls.txt] --> fetch[fetch_and_index]
    fetch --> jina[Jina Reader]
    jina --> docs[documentos/*.md]
    docs --> ingest[indexador Chroma]
    ingest --> chroma[chroma_db]
    chroma --> rag[chatbot_rag]
    ollama[Ollama] --> ingest
    ollama --> rag
```

1. **Ingesta:** se descargan URLs y se guardan como `.md` en `documentos/`.
2. **Indexación:** los documentos se dividen en chunks y se almacenan en ChromaDB con embeddings.
3. **Consulta:** el chatbot recupera los chunks más relevantes y genera una respuesta con Ollama.

## Tecnologías usadas

- [LangChain](https://python.langchain.com/) — loaders, splitters, integraciones
- [LangGraph](https://langchain-ai.github.io/langgraph/) — grafos de agentes con memoria
- [ChromaDB](https://www.trychroma.com/) — base de datos vectorial
- [Ollama](https://ollama.com/) — modelos LLM y embeddings locales/remotos
- [Jina Reader](https://jina.ai/reader/) — conversión de URLs a Markdown

## Estado actual del proyecto

**Experimental / en desarrollo activo.**

- El flujo principal (descarga → indexación → chat RAG) está funcional.
- `obsidian_rag.py` y `simple_chat.py` son utilidades secundarias o de ejemplo.
- No hay tests automatizados ni empaquetado como librería instalable.
- La licencia aún no está definida.

## Próximos pasos recomendados

- Añadir una licencia (MIT sugerida).
- Crear tests básicos de smoke para ingest y configuración.
- Unificar las dos rutas de Chroma (`chroma_db/` y `data/chroma/`).
- Soporte para reindexación incremental (evitar duplicados).

## Documentación adicional

- [Arquitectura](docs/ARCHITECTURE.md)
- [Guía de uso](docs/USAGE.md)
- [Agentes LangGraph](docs/AGENTS.md)

## Avisos importantes

- **No subas `.env`** ni bases vectoriales al repositorio.
- Los modelos y la URL de Ollama deben existir en tu entorno antes de ejecutar los módulos.
- `agents/obsidian_rag.py` es experimental y requiere configurar `OBSIDIAN_VAULT_PATH`.
- Sin `JINA_API_KEY`, Jina Reader funciona con límites de uso; consulta su documentación.

## Licencia

Pendiente de definir.
