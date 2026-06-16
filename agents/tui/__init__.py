"""Interfaz TUI (Textual) para lanzar acciones del proyecto."""

from .app import LauncherTUI


def run_tui() -> None:
    LauncherTUI().run()
