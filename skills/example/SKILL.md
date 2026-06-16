---
name: example
description: Demuestra tools de ejemplo (eco y cálculos aritméticos). Usa para pruebas del sistema, cuando pidan calcular expresiones o repetir/normalizar texto.
metadata:
  tools: echo_tool calc_tool
allowed-tools: echo_tool calc_tool
---

# Skill de ejemplo

## Cuándo usar esta skill

- El usuario pide calcular una expresión (`Calcula 15 * 3`)
- El usuario pide repetir o normalizar texto (`Eco: hola mundo`)
- Pruebas del sistema de skills y tools

## Instrucciones

1. El sistema ya ejecutó la tool adecuada (`echo_tool` o `calc_tool`).
2. Presenta el resultado de forma clara al usuario.
3. Explica brevemente qué tool se usó si ayuda a entender la respuesta.
4. Responde siempre en español.

## Tools disponibles

| Tool | Uso |
|------|-----|
| `echo_tool` | Repite y normaliza texto (mayúsculas, sin espacios extra) |
| `calc_tool` | Evalúa expresiones aritméticas seguras (+, -, *, /) |

## Ejemplo

**Entrada:** Calcula 15 * 3

**Salida esperada:** El resultado `45` con breve explicación.
