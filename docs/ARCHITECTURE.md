# Arquitectura

## Visión general

`ai-agents` es una colección de scripts que implementan un pipeline RAG (Retrieval-Augmented Generation) local. No es una aplicación web ni un paquete instalable: cada script es un punto de entrada independiente que comparte configuración y utilidades en `agents/`.

## Componentes

### `agents/config.py`

Carga variables de entorno desde `.env` y expone constantes usadas por todos los scripts:

- Conexión a Ollama (URL, modelos de chat y embeddings).
- Rutas de ChromaDB y documentos.
- Token opcional de Jina Reader.
- Ruta del vault Obsidian (experimental).

### `agents/jina_fetcher.py`

Responsable de la ingesta de contenido web:

- Descarga URLs mediante `https://r.jina.ai/{url}`.
- Guarda Markdown en `documentos/` con metadatos YAML front matter.
- Soporta reintentos HTTP y nombres de archivo derivados de la URL.

### `agents/ingest.py`

Lógica compartida de indexación:

1. Carga archivos `.md` con `DirectoryLoader`.
2. Enriquece metadatos (`filename`, `folder`).
3. Divide en chunks con `RecursiveCharacterTextSplitter`.
4. Genera embeddings con Ollama y persiste en ChromaDB.

### Módulos de ejecución (`agents/`)

| Módulo | Rol |
|---|---|
| `agents/fetch_and_index.py` | Orquesta descarga Jina + indexación Chroma |
| `agents/index_documents.py` | Solo indexación de `documentos/` |
| `agents/chatbot_rag.py` | Grafo LangGraph con retrieve + generate |
| `agents/chatbot_memory.py` | Chat simple con memoria por hilos |
| `agents/chatbot_skills.py` | Agente con skills, routing por intención y trace |
| `agents/monitor_chroma.py` | Inspección de colecciones |
| `agents/obsidian_rag.py` | RAG sobre vault Obsidian (experimental) |

## Flujo de datos

```
URLs ──► Jina Reader ──► documentos/*.md ──► Text Splitter ──► ChromaDB
                                                                    │
                                                                    ▼
Usuario ──► chatbot_rag ──► Retriever (MMR) ──► Contexto ──► Ollama LLM ──► Respuesta

Usuario ──► chatbot_skills ──► classify (intent) ──► Skill ──► Tools ──► Ollama LLM ──► Respuesta
                                      │
                                      └── trace events
```

### Capa de Skills (`agents/skills/`)

Formato [Agent Skills](https://agentskills.io/specification): cada skill es una carpeta con `SKILL.md` bajo `skills/`.

| Módulo | Rol |
|---|---|
| `loader.py` | Descubrimiento y parseo de `SKILL.md` (YAML + Markdown) |
| `markdown_skill.py` | Ejecutor que activa instrucciones y tools declaradas |
| `executors.py` | Mapeo `allowed-tools` → tools Python |
| `registry.py` | Registro automático desde skills descubiertas |
| `router.py` | Clasificación por catálogo (tier 1) + LLM |
| `tracing.py` | `TraceEvent` y reducer `append_trace` |
| `base.py` | Contrato `BaseSkill`, `SkillContext`, `SkillResult` |

### Tools (`tools/`)

| Tool | Rol |
|---|---|
| `chroma_search` | Búsqueda MMR sobre ChromaDB (compartida con RAG) |
| `echo_tool` / `calc_tool` | Demostración para `ExampleSkill` |

### Grafo de skills (`agents/skills_graph.py`)

Compila el grafo `classify → execute_skill` con `SkillRegistry` inyectable. Preparado para ampliar con adapters MCP en la capa de tools.

## Colecciones ChromaDB

| Colección | Script | Persistencia |
|---|---|---|
| `web_docs` | `fetch_and_index`, `index_documents`, `chatbot_rag` | `chroma_db/` |
| `obsidian_notes` | `obsidian_rag` | `data/chroma/` |

> **Nota:** Existen dos rutas de persistencia por diseño históico. Unificarlas es un posible refactor futuro.

## Decisiones de diseño

- **Ollama como backend único:** tanto embeddings como generación pasan por el mismo servidor Ollama, configurable vía `.env`.
- **LangGraph para orquestación:** el chat RAG usa un grafo de dos nodos en lugar de una cadena lineal, lo que facilita extender con nodos adicionales (validación, re-ranking, etc.).
- **MMR en retrieval:** `chatbot_rag.py` usa Maximum Marginal Relevance para diversificar los chunks recuperados.
- **Memoria en memoria:** `MemorySaver` de LangGraph guarda el historial por `thread_id` solo durante la ejecución del proceso.

## Dependencias entre módulos

```
agents/*.py
    └── agents/paths.py      (sys.path setup)
    └── agents/config.py     (env vars)
    └── agents/ingest.py     (indexación)
    └── agents/jina_fetcher.py (descarga web)
    └── agents/skills_graph.py       (grafos LangGraph)
    └── agents/skills/       (skills y routing)
    └── tools/        (tools desacopladas)
```

## Datos excluidos del repositorio

Por `.gitignore`:

- `env/`, `.venv/` — entornos virtuales
- `chroma_db/`, `data/chroma/` — bases vectoriales
- `documentos/*` — contenido descargado
- `.env` — secretos y configuración local
