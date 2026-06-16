from typing import Any

from langchain_core.messages import AIMessage


def _format_duration_ns(ns: int | None) -> str:
    if ns is None:
        return "desconocido"
    ms = ns / 1_000_000
    if ms < 1000:
        return f"{ms:.0f} ms"
    return f"{ms/1000:.2f} s"


def print_response_feedback(message: AIMessage) -> None:
    usage = getattr(message, "usage_metadata", None) or {}
    response_meta = getattr(message, "response_metadata", None) or {}
    parts: list[str] = []

    if usage:
        tokens = []
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            value = usage.get(key)
            if value is not None:
                tokens.append(f"{key}={value}")
        if tokens:
            parts.append("tokens=" + ",".join(tokens))

    if response_meta:
        model = response_meta.get("model_name") or response_meta.get("model")
        if model:
            parts.append(f"modelo={model}")
        duration = _format_duration_ns(response_meta.get("total_duration"))
        parts.append(f"tiempo={duration}")
        eval_count = response_meta.get("eval_count")
        if eval_count is not None:
            parts.append(f"evals={eval_count}")

    if parts:
        print("  [" + " | ".join(parts) + "]")
