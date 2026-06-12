from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, Log, Static, Button

from main import (
    _run_fetch,
    _run_index,
    _run_monitor,
)

import argparse
import io
import contextlib
import threading


ACTIONS = [
    ("fetch", "Descargar URLs e indexar"),
    ("index", "Indexar documentos"),
    ("monitor", "Inspeccionar ChromaDB"),
]


class LauncherTUI(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #menu {
        width: 30%;
        border: round $primary;
    }

    #right {
        width: 70%;
    }

    #info {
        height: 5;
        border: round $accent;
        padding: 1;
    }

    #log {
        height: 1fr;
        border: round $success;
    }
    """

    BINDINGS = [
        ("q", "quit", "Salir"),
        ("r", "run_selected", "Ejecutar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="menu"):
                yield Static("Acciones", id="info")
                yield ListView(
                    *[ListItem(Label(f"{name} — {desc}")) for name, desc in ACTIONS],
                    id="actions",
                )
                yield Button("Ejecutar", id="run_button", variant="primary")
            with Vertical(id="right"):
                yield Static("Salida", id="info")
                yield Log(id="log")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(ListView).index = 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_button":
            self.action_run_selected()

    def action_run_selected(self) -> None:
        list_view = self.query_one("#actions", ListView)
        log = self.query_one("#log", Log)

        if list_view.index is None:
            log.write_line("No hay acción seleccionada.")
            return

        action_name = ACTIONS[list_view.index][0]
        log.write_line(f"> Ejecutando: {action_name}")

        thread = threading.Thread(target=self._execute_action, args=(action_name,), daemon=True)
        thread.start()

    def _execute_action(self, action_name: str) -> None:
        log = self.query_one("#log", Log)
        buffer = io.StringIO()

        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                if action_name == "fetch":
                    _run_fetch(argparse.Namespace(urls=[]))
                elif action_name == "index":
                    _run_index(argparse.Namespace())
                elif action_name == "monitor":
                    _run_monitor(argparse.Namespace())

            output = buffer.getvalue().strip() or "[OK] Sin salida."
            self.call_from_thread(log.write_line, output)

        except Exception as e:
            self.call_from_thread(log.write_line, f"[ERROR] {e}")


def run_tui():
    LauncherTUI().run()