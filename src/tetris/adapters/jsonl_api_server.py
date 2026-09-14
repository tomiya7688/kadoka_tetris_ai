"""Localhost-only JSONL/TCP semantic input server."""

import socketserver
import threading
from queue import Empty, Queue

from tetris.application.input_action import InputAction

from .jsonl_api_handler import JsonlApiHandler


class JsonlApiServer:
    """Receive external semantic actions without mutating game state off-thread."""

    def __init__(
        self,
        port: int,
        allowed_players: set[int] | frozenset[int],
        host: str = "127.0.0.1",
    ):
        if not isinstance(port, int) or isinstance(port, bool):
            raise ValueError("port must be an integer")
        if port < 0 or port > 65535:
            raise ValueError("port must be between 0 and 65535")
        if not allowed_players:
            raise ValueError("at least one allowed player is required")

        self._actions: Queue[InputAction] = Queue()
        self._server = socketserver.ThreadingTCPServer((host, port), JsonlApiHandler)
        self._server.daemon_threads = True
        self._server.action_queue = self._actions
        self._server.allowed_players = frozenset(allowed_players)
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._server.server_address
        return str(host), int(port)

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("JSONL API server is already started")
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="kadoka-jsonl-api",
            daemon=True,
        )
        self._thread.start()

    def drain(self) -> tuple[InputAction, ...]:
        actions = []
        while True:
            try:
                actions.append(self._actions.get_nowait())
            except Empty:
                return tuple(actions)

    def close(self) -> None:
        if self._thread is not None:
            self._server.shutdown()
            self._thread.join(timeout=2)
            self._thread = None
        self._server.server_close()
