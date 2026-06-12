"""Tools de demostración para skill_example."""

from __future__ import annotations

import ast
import operator
import re

from src.python_agents.tools.base import ToolResult

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    raise ValueError("Expresión no permitida")


class EchoTool:
    name = "echo_tool"
    description = "Repite y normaliza un texto de entrada (mayúsculas, sin espacios extra)."

    def invoke(self, *, text: str = "", **_: object) -> ToolResult:
        normalized = re.sub(r"\s+", " ", text.strip()).upper()
        return ToolResult(output=normalized, metadata={"input_len": len(text)})


class CalcTool:
    name = "calc_tool"
    description = "Evalúa una expresión aritmética segura (+, -, *, /, //, %, **)."

    def invoke(self, *, expression: str = "", **_: object) -> ToolResult:
        expr = expression.strip()
        if not expr:
            return ToolResult(output="Error: expresión vacía", metadata={"error": True})
        try:
            tree = ast.parse(expr, mode="eval")
            result = _safe_eval(tree.body)
            return ToolResult(output=str(result), metadata={"expression": expr})
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as exc:
            return ToolResult(
                output=f"Error: {exc}",
                metadata={"expression": expr, "error": True},
            )
