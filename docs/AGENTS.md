# Agentes LangGraph

Este documento explica cómo funcionan los grafos de LangGraph en el proyecto.

## Conceptos básicos

- **Estado (`State`):** diccionario tipado que viaja entre nodos del grafo.
- **Nodo:** función que recibe el estado y devuelve actualizaciones parciales.
- **Grafo:** secuencia de nodos conectados por aristas.
- **Checkpointer:** guarda el historial de mensajes por `thread_id`.

## Chat simple (`chatbot_memory.py`)

### Grafo

```
START ──► chatbot ──► END
```

### Estado

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

El campo `messages` acumula el historial de conversación gracias al reducer `add_messages`.

### Flujo

1. El usuario escribe un mensaje.
2. El nodo `chatbot` invoca Ollama con el system prompt + historial.
3. La respuesta se añade al estado.
4. `MemorySaver` persiste el hilo identificado por `thread_id`.

### Hilos de conversación

Cada `thread_id` mantiene su propio historial. Puedes cambiar de hilo con `/thread otro-id` o reiniciar con `/reset`.

---

## Chat RAG (`chatbot_rag.py`)

### Grafo

```
START ──► retrieve ──► generate ──► END
```

### Estado

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
```

Además del historial, el estado incluye `context` con los documentos recuperados.

### Nodo `retrieve`

1. Toma la última pregunta del usuario.
2. Consulta ChromaDB con búsqueda MMR (`k=4`, `fetch_k=8`).
3. Concatena los chunks recuperados con sus fuentes.
4. Devuelve `{"context": "..."}`.

### Nodo `generate`

1. Construye un prompt con el contexto recuperado y la pregunta.
2. Invoca Ollama con instrucciones en español.
3. Devuelve la respuesta como nuevo mensaje AI.

### Por qué dos nodos

Separar retrieve y generate permite:

- Inspeccionar el contexto recuperado antes de generar (extensible con `/state`).
- Añadir nodos intermedios (re-ranking, filtrado, validación).
- Reutilizar el retriever sin regenerar respuesta.

---

## Ejemplo mínimo (`examples/simple_chat.py`)

Versión simplificada sin checkpointer:

```
START ──► chatbot ──► END
```

El historial se mantiene manualmente en una lista Python dentro del bucle `while`. No hay persistencia entre ejecuciones ni soporte de hilos.

---

## Agente con Skills (`chatbot_skills.py`)

Arquitectura modular con routing automático por intención, tools desacopladas y trazabilidad.

### Grafo

```
START ──► classify ──► execute_skill ──► END
```

### Estado

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    trace: Annotated[list[TraceEvent], append_trace]
    context: str
    last_skill: str
```

### Nodo `classify`

1. Toma la última pregunta del usuario.
2. Clasifica la intención con Ollama (`with_structured_output`).
3. Fallback por keywords si el parse falla.
4. Registra evento `intent_classified` en `trace`.

### Nodo `execute_skill`

1. Busca la skill en `SkillRegistry` por `intent`.
2. Ejecuta `skill.run(query, context)` con tools propias.
3. Devuelve respuesta AI, contexto RAG (si aplica) y eventos de trace.

### Formato Agent Skills ([agentskills.io](https://agentskills.io/home))

Las skills viven en carpetas con un `SKILL.md` (YAML frontmatter + instrucciones Markdown):

```
.agents/skills/
├── rag/SKILL.md
├── example/SKILL.md
└── general/SKILL.md
```

**Progressive disclosure:**

1. **Discovery (tier 1):** al arrancar, solo `name` + `description` → catálogo para el router.
2. **Activation (tier 2):** al ejecutar la skill, se carga el cuerpo de `SKILL.md`.
3. **Resources (tier 3):** `scripts/`, `references/`, `assets/` bajo la carpeta de la skill.

Rutas de búsqueda (en orden): `.agents/skills/`, `skills/` (configurable en `config.py`).

### Skills incluidas

| name | Tools (`allowed-tools`) |
|---|---|
| `rag` | `chroma_search` |
| `example` | `echo_tool`, `calc_tool` |
| `general` | (ninguna) |

### Trazabilidad

Cada ejecución acumula `TraceEvent` en el estado:

- `intent_classified` — intención detectada y confianza
- `skill_activated` — ruta del `SKILL.md` cargado
- `skill_start` / `skill_end` — inicio y fin de skill
- `tool_call` / `tool_result` — invocación y resultado de tools

Comando CLI: `/trace` imprime los últimos eventos del hilo.

### Ejemplo mínimo

`examples/skills_agent.py` — misma lógica sin `MemorySaver`, imprime intent y trace tras cada respuesta.

### Añadir una skill nueva

1. Crear `.agents/skills/<nombre>/SKILL.md` con frontmatter `name` y `description` (el `name` debe coincidir con el directorio).
2. Escribir instrucciones en el cuerpo Markdown.
3. Si necesita tools Python, declararlas en `allowed-tools` y registrar la tool en `src/python_agents/tools/`.
4. Reiniciar el agente — `discover_skills()` la carga automáticamente.

### Extensión MCP (futuro)

Las tools usan el contrato `invoke(**kwargs) -> ToolResult`. Un `McpToolAdapter` puede envolver tools MCP sin modificar skills ni el grafo.

---

## Configuración de modelos

Todos los agentes leen de `src/python_agents/config.py`:

| Parámetro | Uso |
|---|---|
| `OLLAMA_CHAT_MODEL` | Generación de respuestas |
| `OLLAMA_EMBED_MODEL` | Embeddings para ChromaDB (solo RAG) |
| `OLLAMA_BASE_URL` | Servidor Ollama |

---

## Extender los agentes

Ideas para evolucionar los grafos:

1. **Nodo de validación:** comprobar si el contexto recuperado es suficiente antes de generar.
2. **Nodo de re-ranking:** reordenar chunks por relevancia con un cross-encoder.
3. **Human-in-the-loop:** pausar antes de responder si la confianza es baja.
4. **Herramientas:** añadir nodos que llamen APIs externas (Wazuh, NVD, etc.).

LangGraph facilita añadir nodos y aristas condicionales sin reescribir el flujo completo.
