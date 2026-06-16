---
name: rag
description: Responde preguntas sobre documentación técnica, CVEs, políticas y contenido indexado en ChromaDB. Usa cuando el usuario pregunta sobre documentos, vulnerabilidades, CVE o la base de conocimiento.
metadata:
  tools: chroma_search
allowed-tools: chroma_search
---

# RAG — Consulta de documentación

## Cuándo usar esta skill

- Preguntas sobre CVEs, vulnerabilidades o advisories
- Consultas sobre políticas, procedimientos o documentación técnica
- "¿Qué dice el documento sobre...?"
- Cualquier pregunta que requiera buscar en la base de conocimiento indexada

## Instrucciones

1. El sistema ya ejecutó `chroma_search` con la pregunta del usuario; usa el contexto recuperado.
2. Responde en español, de forma clara y técnica.
3. Prioriza el contexto recuperado sobre conocimiento general.
4. Cita las fuentes cuando el contexto las incluya.
5. Si el contexto no es suficiente, dilo explícitamente. No inventes datos.

## Ejemplo

**Entrada:** ¿Qué CVEs menciona la documentación?

**Salida esperada:** Lista de CVEs encontrados en los documentos, con breve contexto y fuente.
