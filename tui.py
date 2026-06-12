"""Punto de entrada: python tui.py"""

from src.python_agents.paths import setup_import_path

setup_import_path()

from src.python_agents.tui import run_tui

if __name__ == "__main__":
    run_tui()
