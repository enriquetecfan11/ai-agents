"""Pantalla de chat interactivo para la TUI."""

from __future__ import annotations

import threading

from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from agents.tui.chat_backends import ChatBackend, ChatReply


class ChatScreen(Screen):
    """Chat con un backend LangGraph (simple, rag, memory, skills)."""

    BINDINGS = [
        ("escape", "go_back", "Volver"),
    ]

    CSS = """
    ChatScreen {
        layout: vertical;
    }

    #chat-info {
        height: auto;
        max-height: 5;
        border: round $accent;
        padding: 0 1;
        background: $surface-darken-1;
    }

    #chat-log {
        height: 1fr;
        border: round $primary;
        padding: 0 1;
        scrollbar-gutter: stable;
    }

    #chat-input {
        margin: 1 0;
        border: tall $primary;
    }

    #chat-status {
        height: 3;
        border: round $warning;
        padding: 0 1;
        content-align: left middle;
    }
    """

    def __init__(self, backend: ChatBackend) -> None:
        super().__init__()
        self._backend = backend
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"[b]{self._backend.title}[/b] — {self._backend.help_text}",
            id="chat-info",
        )
        yield RichLog(
            id="chat-log",
            markup=True,
            wrap=True,
            highlight=False,
            auto_scroll=True,
        )
        yield Static("Listo.", id="chat-status")
        yield Input(
            placeholder="Escribe un mensaje…  (/exit volver · /thread · /trace · /reset)",
            id="chat-input",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#chat-input", Input).focus()
        self._append_system("Escribe /exit o pulsa Esc para volver al launcher.")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return

        if text in {"/exit", "/quit", "/salir"}:
            self.app.pop_screen()
            return

        slash_reply = self._backend.handle_slash(text)
        if slash_reply is not None:
            self._append_system(slash_reply)
            return

        if self._busy:
            self._append_system("[WARN] Espera a que termine la respuesta anterior.")
            return

        self._append_user(text)
        self._set_busy(True)
        self._generate_reply(text)

    @work(thread=True)
    def _generate_reply(self, text: str) -> None:
        try:
            reply = self._backend.send(text)
            self.app.call_from_thread(self._append_bot, reply)
        except Exception as exc:
            self.app.call_from_thread(self._append_system, f"[ERROR] {exc}")
        finally:
            self.app.call_from_thread(self._set_busy, False)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        status = self.query_one("#chat-status", Static)
        chat_input = self.query_one("#chat-input", Input)
        status.update("Pensando…" if busy else "Listo.")
        chat_input.disabled = busy
        if not busy:
            chat_input.focus()

    def _append_user(self, text: str) -> None:
        self._write_markup(f"[bold cyan]Tú[/]  {escape(text)}")

    def _append_bot(self, reply: ChatReply) -> None:
        self._write_markup(f"[bold green]Bot[/] {escape(reply.text)}")
        if reply.meta:
            self._write_markup(f"       [dim italic]{escape(reply.meta)}[/]")

    def _append_system(self, text: str) -> None:
        self._write_markup(f"[dim]— {escape(text)}[/]")

    def _write_markup(self, message: str) -> None:
        def write() -> None:
            log = self.query_one("#chat-log", RichLog)
            log.write(message)
            log.write("")

        if threading.current_thread() is threading.main_thread():
            write()
        else:
            self.app.call_from_thread(write)
