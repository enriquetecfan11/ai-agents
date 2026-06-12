"""Interfaz TUI (Textual) para lanzar acciones del proyecto."""

from src.python_agents.tui.app import LauncherTUI


def run_tui() -> None:
    LauncherTUI().run()
