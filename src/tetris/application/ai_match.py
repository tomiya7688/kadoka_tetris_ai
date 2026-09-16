from __future__ import annotations

from collections.abc import Mapping

from tetris.core import GameState

from .ai_backend import AIBackend, NativePlannerBackend
from .ai_runner import run_ai_turn
from .versus import VersusSession


class AIMatchRunner:
    def __init__(
        self,
        seed_a: int = 1,
        seed_b: int = 2,
        backends: Mapping[int, AIBackend] | None = None,
    ):
        self.session = VersusSession({0: GameState(seed_a), 1: GameState(seed_b)})
        self.backends = dict(backends) if backends is not None else {
            0: NativePlannerBackend(name="placement_planner_a"),
            1: NativePlannerBackend(name="placement_planner_b"),
        }
        if set(self.backends) != set(self.session.games):
            raise ValueError("AI match requires one backend per player")
        self.sequences = {0: 0, 1: 0}

    def step(self):
        for player in self.session.games:
            result = run_ai_turn(
                self.session,
                self.backends[player],
                player=player,
                sequence_start=self.sequences[player],
            )
            self.sequences[player] = result.next_sequence
        self.session.advance()

    def run(self, max_steps: int = 100):
        if max_steps < 0:
            raise ValueError("max_steps must be nonnegative")
        for _ in range(max_steps):
            if any(result.defeated for result in self.session.results.values()):
                break
            self.step()
        return self.session.results

    def close(self) -> None:
        seen: set[int] = set()
        for backend in self.backends.values():
            backend_identity = id(backend)
            if backend_identity in seen:
                continue
            seen.add(backend_identity)
            backend.close()

    def __enter__(self) -> "AIMatchRunner":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
