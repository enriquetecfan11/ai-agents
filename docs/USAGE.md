# Guía de uso

## CLI (`main.py`)

Comandos recomendados desde la raíz:

```powershell
python main.py fetch
python main.py index
python main.py monitor
python main.py rag
python main.py tui      # launcher visual Textual
```

Ver `python main.py --help` para la lista completa. Los scripts en `scripts/` siguen siendo válidos y son los que invoca `main.py` internamente.

---

## Preparación inicial

1. Clona el repositorio y entra en la carpeta.
2. Crea y activa un entorno virtual.
3. Instala dependencias: `pip install -r requirements.txt`
4. Copia `.env.example` a `.env` y configura `OLLAMA_BASE_URL`.
5. Asegúrate de que los modelos de Ollama estén disponibles:

```powershell
ollama pull gemma4:e2b
ollama pull mxbai-embed-large
```

> Si usas un servidor Ollama remoto, solo necesitas que los modelos estén disponibles en ese servidor.

---

## `fetch_and_index.py`

**Propósito:** descargar URLs como Markdown e indexarlas en ChromaDB.

### Con archivo de URLs

```powershell
copy config\urls.example.txt config\urls.txt
# Edita config/urls.txt con tus URLs (una por línea)
python scripts/fetch_and_index.py
```

### Con URLs por línea de comandos

```powershell
python scripts/fetch_and_index.py https://ejemplo.com/cve-2026-0001
```

### Salida esperada

- Archivos `.md` en `documentos/`
- Colección `web_docs` en `chroma_db/`
- Mensajes `[OK]` con conteo de documentos y chunks

---

## `index_documents.py`

**Propósito:** reindexar Markdown existente sin descargar URLs nuevas.

Útil cuando ya tienes archivos en `documentos/` y solo quieres actualizar ChromaDB.

```powershell
python scripts/index_documents.py
```

---

## `chatbot_rag.py`

**Propósito:** chat interactivo con recuperación de contexto desde ChromaDB.

```powershell
python scripts/chatbot_rag.py
```

### Comandos disponibles

| Comando | Acción |
|---|---|
| `/exit`, `/quit`, `/salir` | Terminar el chat |
| `/thread <id>` | Cambiar hilo de conversación |
| `/state` | Mostrar estado interno del grafo |

### Requisitos previos

- ChromaDB debe tener documentos indexados (`fetch_and_index` o `index_documents`).
- Ollama debe estar accesible y responder.

---

## `chatbot_memory.py`

**Propósito:** chat con Ollama y memoria por hilos, sin RAG.

```powershell
python scripts/chatbot_memory.py
```

| Comando | Acción |
|---|---|
| `/exit` | Salir |
| `/reset` | Reiniciar memoria (nuevo thread) |
| `/thread <id>` | Cambiar hilo |

---

## `monitor_chroma.py`

**Propósito:** inspeccionar colecciones y ver una muestra de registros.

```powershell
python scripts/monitor_chroma.py
```

Muestra nombre de colección, número de registros y preview de los primeros 3 documentos.

---

## `obsidian_rag.py` (experimental)

**Propósito:** indexar y consultar notas Markdown de un vault Obsidian.

1. Define `OBSIDIAN_VAULT_PATH` en `.env` con la ruta absoluta al vault.
2. Ejecuta:

```powershell
python scripts/obsidian_rag.py
```

3. Elige modo:
   - `index` — indexa todas las notas `.md` del vault.
   - `query` — hace una pregunta sobre el contenido indexado.

---

## `examples/simple_chat.py`

Ejemplo mínimo de chatbot sin memoria persistente ni RAG. Útil como punto de partida para entender LangGraph + Ollama.

```powershell
python examples/simple_chat.py
```

---

## Troubleshooting

### Ollama no responde

- Verifica `OLLAMA_BASE_URL` en `.env`.
- Prueba: `curl http://localhost:11434/api/tags`
- Confirma que los modelos están descargados.

### ChromaDB vacío

- Ejecuta `python scripts/monitor_chroma.py` para verificar colecciones.
- Asegúrate de que `documentos/` contiene archivos `.md`.
- Vuelve a indexar con `python scripts/index_documents.py`.

### Error al descargar URLs

- Comprueba conexión a internet.
- Si Jina limita peticiones, configura `JINA_API_KEY` en `.env`.
- Revisa que las URLs sean accesibles públicamente.

### `ModuleNotFoundError: src.python_agents`

Ejecuta los scripts desde la raíz del proyecto, no desde dentro de `scripts/`:

```powershell
cd C:\ruta\a\python-agents
python scripts/chatbot_rag.py
```
