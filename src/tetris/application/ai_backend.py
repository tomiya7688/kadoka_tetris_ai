from __future__ import annotations

import json
import queue
import subprocess
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from tetris.ai import PlacementPlanner
from tetris.core import GameState


class AIBackendKind(str, Enum):
    """Canonical Kadoka sibling-project backend vocabulary."""

    NATIVE = "native"
    DYNAMIC_LIBRARY = "dynamic_library"
    EXTERNAL_PROCESS = "external_process"
    SCRIPT = "script"
    NETWORK = "network"


@dataclass(frozen=True)
class AIProposal:
    """Non-authoritative semantic actions proposed by an AI backend."""

    actions: tuple[str, ...]
    diagnostics: Mapping[str, str] = field(default_factory=dict)


class AIBackend(ABC):
    """Runtime-facing AI boundary.

    Backends observe a game and propose semantic actions. They never mutate the
    authoritative GameState directly.
    """

    @property
    @abstractmethod
    def kind(self) -> AIBackendKind:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def decide(self, game: GameState) -> AIProposal:
        raise NotImplementedError

    def close(self) -> None:
        """Release backend resources. In-process backends have nothing to do."""


class NativePlannerBackend(AIBackend):
    """Fast adapter for the existing in-process PlacementPlanner."""

    def __init__(self, planner: PlacementPlanner | None = None, name: str = "placement_planner"):
        self._planner = planner or PlacementPlanner()
        self._name = name

    @property
    def kind(self) -> AIBackendKind:
        return AIBackendKind.NATIVE

    @property
    def name(self) -> str:
        return self._name

    def decide(self, game: GameState) -> AIProposal:
        planned = self._planner.choose(game)
        return AIProposal(
            actions=tuple(planned.actions),
            diagnostics={"score": str(planned.score)},
        )


class FunctionAIBackend(AIBackend):
    """Small adapter for dynamic-library/network integrations implemented elsewhere."""

    def __init__(
        self,
        kind: AIBackendKind,
        name: str,
        decide: Callable[[GameState], AIProposal],
    ):
        if not callable(decide):
            raise ValueError("decide must be callable")
        self._kind = kind
        self._name = name
        self._decide = decide

    @property
    def kind(self) -> AIBackendKind:
        return self._kind

    @property
    def name(self) -> str:
        return self._name

    def decide(self, game: GameState) -> AIProposal:
        proposal = self._decide(game)
        if not isinstance(proposal, AIProposal):
            raise TypeError("AI backend must return AIProposal")
        return proposal


def public_observation(game: GameState) -> dict[str, Any]:
    """Build a stable public observation without exposing mutable internals."""

    active = game.active
    return {
        "board": {
            "width": game.board.width,
            "height": game.board.height,
            "hidden_rows": game.board.hidden_rows,
            "occupied": [[x, y] for x, y in game.board.cells()],
        },
        "active": None
        if active is None
        else {
            "kind": active.kind.value,
            "x": active.x,
            "y": active.y,
            "rotation": active.rotation,
        },
        "hold": None if game.hold is None else game.hold.value,
        "hold_used": game.hold_used,
        "next": [piece.value for piece in game.next_pieces],
        "game_over": game.game_over,
        "lines": game.lines,
        "combo": game.combo,
        "back_to_back": game.back_to_back_active,
        "pieces_locked": game.pieces_locked,
    }


class PersistentProcessAIBackend(AIBackend):
    """Long-lived JSONL subprocess backend for external executable/script AIs."""

    def __init__(
        self,
        *,
        kind: AIBackendKind,
        name: str,
        executable: str,
        arguments: Sequence[str] = (),
        timeout_seconds: float = 5.0,
    ):
        if kind not in (AIBackendKind.EXTERNAL_PROCESS, AIBackendKind.SCRIPT):
            raise ValueError("persistent process backend kind must be external_process or script")
        if not executable:
            raise ValueError("executable must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self._kind = kind
        self._name = name
        self._timeout = timeout_seconds
        self._request_id = 1
        self._responses: queue.Queue[str | BaseException] = queue.Queue()
        self._process = subprocess.Popen(
            [executable, *arguments],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        if self._process.stdin is None or self._process.stdout is None:
            self._terminate()
            raise RuntimeError("failed to open external AI pipes")

        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    @property
    def kind(self) -> AIBackendKind:
        return self._kind

    @property
    def name(self) -> str:
        return self._name

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        try:
            for line in self._process.stdout:
                self._responses.put(line.rstrip("\r\n"))
        except BaseException as exc:  # transport failure is surfaced to decide()
            self._responses.put(exc)

    def decide(self, game: GameState) -> AIProposal:
        if self._process.poll() is not None:
            raise RuntimeError("external AI process is not running")

        request_id = self._request_id
        self._request_id += 1
        request = {
            "type": "decide",
            "request_id": request_id,
            "observation": public_observation(game),
        }

        assert self._process.stdin is not None
        try:
            self._process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError("failed to write external AI request") from exc

        try:
            item = self._responses.get(timeout=self._timeout)
        except queue.Empty as exc:
            raise TimeoutError("external AI response timed out") from exc

        if isinstance(item, BaseException):
            raise RuntimeError("external AI stdout reader failed") from item
        if not item:
            if self._process.poll() is not None:
                raise RuntimeError("external AI process exited before response")
            raise RuntimeError("external AI returned an empty response")

        try:
            response = json.loads(item)
        except json.JSONDecodeError as exc:
            raise RuntimeError("external AI returned malformed JSON") from exc
        if not isinstance(response, dict):
            raise RuntimeError("external AI response must be an object")
        if response.get("type") != "result" or response.get("request_id") != request_id:
            raise RuntimeError("external AI response has invalid request id")

        actions = response.get("actions")
        if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
            raise RuntimeError("external AI response requires string actions")
        diagnostics = response.get("diagnostics", {})
        if not isinstance(diagnostics, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in diagnostics.items()
        ):
            raise RuntimeError("external AI diagnostics must be string pairs")

        return AIProposal(tuple(actions), diagnostics)

    def _terminate(self) -> None:
        if self._process.stdin is not None:
            try:
                self._process.stdin.close()
            except OSError:
                pass
        if self._process.poll() is None:
            try:
                self._process.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                self._process.terminate()
                try:
                    self._process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=1.0)

    def close(self) -> None:
        self._terminate()

    def __enter__(self) -> "PersistentProcessAIBackend":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
