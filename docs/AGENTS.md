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
