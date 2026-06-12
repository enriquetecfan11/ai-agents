"""Aplicación Textual del launcher."""

from __future__ import annotations

import argparse
import contextlib
import io
import threading
from datetime import datetime

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Log, Static

from src.python_agents.tui.actions import ALL_ACTIONS, ActionDef
from src.python_agents.tui.chat_backends import get_chat_backend
from src.python_agents.tui.chat_screen import ChatScreen


class LauncherTUI(App):
    """Launcher visual para comandos de pipeline; base extensible para chats."""

    TITLE = "python-agents"
    SUB_TITLE = "Launcher"

    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #sidebar {
        width: 32;
        border: round $primary;
        padding: 0 1;
    }

    #sidebar-title {
        text-style: bold;
        color: $primary;
        margin: 1 0 0 0;
    }

    #actions {
        height: 1fr;
        border: none;
    }

    ListItem {
        padding: 0 1;
    }

    ListItem.-disabled {
        opacity: 0.45;
    }

    ListItem.-section {
        text-style: bold;
        color: $text-muted;
        background: transparent;
    }

    #main {
        width: 1fr;
    }

    #description {
        height: auto;
        max-height: 8;
        border: round $accent;
        padding: 1;
    }

    #status {
        height: 3;
        border: round $warning;
        padding: 0 1;
        content-align: left middle;
    }

    #log {
        height: 1fr;
        border: round $success;
    }

    #toolbar {
        height: auto;
        align: left middle;
        margin-top: 1;
    }

    #run_button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Salir"),
        ("enter", "run_selected", "Ejecutar"),
        ("r", "run_selected", "Ejecutar"),
        ("c", "clear_log", "Limpiar log"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._selectable_indices: list[int] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Acciones", id="sidebar-title")
                yield ListView(id="actions")
            with Vertical(id="main"):
                yield Static("Selecciona una acción del menú.", id="description")
                yield Static("Listo.", id="status")
                yield Log(id="log", highlight=True)
                with Horizontal(id="toolbar"):
                    yield Button("Ejecutar", id="run_button", variant="primary")
                    yield Button("Limpiar log", id="clear_button")
        yield Footer()

    def on_mount(self) -> None:
        list_view = self.query_one("#actions", ListView)
        pipeline = [a for a in ALL_ACTIONS if a.category == "pipeline"]
        chat = [a for a in ALL_ACTIONS if a.category == "chat"]

        list_view.append(ListItem(Label("— Pipeline —"), classes="-section"))
        for action in pipeline:
            self._append_action_item(list_view, action)

        list_view.append(ListItem(Label("— Chat —"), classes="-section"))
        for action in chat:
            self._append_action_item(list_view, action)

        list_view.index = self._selectable_indices[0]
        self._update_selection()

    def _append_action_item(self, list_view: ListView, action: ActionDef) -> None:
        item = ListItem(Label(action.label))
        if not action.enabled:
            item.add_class("-disabled")
        list_view.append(item)
        self._selectable_indices.append(len(list_view.children) - 1)

    def _action_at_index(self, index: int | None) -> ActionDef | None:
        if index is None:
            return None

        selectable = [a for a in ALL_ACTIONS if a.category == "pipeline"] + [
            a for a in ALL_ACTIONS if a.category == "chat"
        ]
        try:
            pos = self._selectable_indices.index(index)
        except ValueError:
            return None
        return selectable[pos]

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id != "actions":
            return
        if event.list_view.index in self._selectable_indices:
            self._update_selection()

    def _update_selection(self) -> None:
        list_view = self.query_one("#actions", ListView)
        action = self._action_at_index(list_view.index)
        description = self.query_one("#description", Static)

        if action is None:
            description.update("Selecciona una acción del menú.")
            return

        if action.kind == "chat":
            hint = "Pulsa Enter o `r` para abrir el chat."
        elif action.enabled:
            hint = "Pulsa Enter o `r` para ejecutar."
        else:
            hint = f"CLI: python main.py {action.id}"
        description.update(f"[bold]{action.label}[/]\n{action.description}\n\n{hint}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_button":
            self.action_run_selected()
        elif event.button.id == "clear_button":
            self.action_clear_log()

    def action_clear_log(self) -> None:
        self.query_one("#log", Log).clear()

    def _chat_screen_active(self) -> bool:
        return isinstance(self.screen, ChatScreen)

    def _open_chat(self, action: ActionDef) -> None:
        if self._chat_screen_active():
            self._write_log(f"[INFO] Ya estás en {action.label}. Pulsa Esc para volver.")
            return
        backend = get_chat_backend(action.id)
        self.push_screen(ChatScreen(backend))

    def action_run_selected(self) -> None:
        list_view = self.query_one("#actions", ListView)
        action = self._action_at_index(list_view.index)
        if action is None:
            self._write_log("[WARN] No hay acción seleccionada.")
            return

        if action.kind == "chat":
            self._open_chat(action)
            return

        if self._running:
            self._write_log("[WARN] Ya hay una acción de pipeline en ejecución.")
            return

        if not action.enabled or action.runner is None:
            self._write_log(f"[INFO] {action.label} no disponible. Usa: python main.py {action.id}")
            return

        self._set_running(True)
        self._write_log(f"> {self._timestamp()} — Iniciando {action.id}")
        self._run_action(action)

    @work(thread=True)
    def _run_action(self, action: ActionDef) -> None:
        buffer = io.StringIO()
        args = argparse.Namespace(urls=[])

        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                assert action.runner is not None
                action.runner(args)

            output = buffer.getvalue().strip()
            if output:
                self._write_log_lines(output.splitlines())
            else:
                self._write_log("[OK] Completado sin salida.")

            if action.id == "all":
                self._write_log("[INFO] Fetch listo. Abre RAG desde el menú Chat.")

        except Exception as exc:
            self._write_log(f"[ERROR] {exc}")
        finally:
            self.call_from_thread(self._set_running, False)

    def _set_running(self, running: bool) -> None:
        self._running = running
        status = self.query_one("#status", Static)
        run_button = self.query_one("#run_button", Button)

        if running:
            status.update("Ejecutando…")
            run_button.disabled = True
        else:
            status.update("Listo.")
            run_button.disabled = False

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _write_log(self, message: str) -> None:
        def write() -> None:
            self.query_one("#log", Log).write_line(message)

        if threading.current_thread() is threading.main_thread():
            write()
        else:
            self.call_from_thread(write)

    def _write_log_lines(self, lines: list[str]) -> None:
        for line in lines:
            self._write_log(line)
