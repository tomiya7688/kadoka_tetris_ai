"""Socket request handler for the local JSONL input API."""

import socketserver
from queue import Queue

from tetris.application.input_action import InputAction

from .jsonl import decode_input_action, encode_event


class JsonlApiHandler(socketserver.StreamRequestHandler):
    """Decode one semantic input action per line and queue it for the game loop."""

    def handle(self) -> None:
        action_queue = self._action_queue()
        allowed_players = self._allowed_players()

        for raw_line in self.rfile:
            response = self._process_line(raw_line, action_queue, allowed_players)
            self.wfile.write((encode_event(response) + "\n").encode("utf-8"))
            self.wfile.flush()

    def _process_line(
        self,
        raw_line: bytes,
        action_queue: Queue[InputAction],
        allowed_players: frozenset[int],
    ) -> dict:
        try:
            line = raw_line.decode("utf-8")
            input_action = decode_input_action(line)
            if input_action.player not in allowed_players:
                raise ValueError(f"unknown player: {input_action.player}")
            action_queue.put(input_action)
            return {"ok": True, "queued": True}
        except (UnicodeDecodeError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    def _action_queue(self) -> Queue[InputAction]:
        action_queue = getattr(self.server, "action_queue", None)
        if not isinstance(action_queue, Queue):
            raise RuntimeError("JSONL API server is missing its action queue")
        return action_queue

    def _allowed_players(self) -> frozenset[int]:
        allowed_players = getattr(self.server, "allowed_players", None)
        if not isinstance(allowed_players, frozenset):
            raise RuntimeError("JSONL API server is missing its player set")
        return allowed_players
