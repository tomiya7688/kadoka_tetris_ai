"""Built-in CPU boundary that exposes only player-visible observations."""

from typing import Protocol

from tetris.application import InputAction
from tetris.core import GameState
from tetris.observation import PlayerObservation, VisiblePlayerObserver


class VisibleCpuStrategy(Protocol):
    """Decision logic that is intentionally isolated from GameState."""

    def choose(self, observation: PlayerObservation) -> str | None:
        ...


class VisibleCpuController:
    """Translate a visible-only CPU decision into the shared input path."""

    def __init__(
        self,
        player: int,
        strategy: VisibleCpuStrategy,
        observer: VisiblePlayerObserver | None = None,
    ):
        if not isinstance(player, int) or isinstance(player, bool) or player < 0:
            raise ValueError("player must be a nonnegative integer")
        self.player = player
        self.strategy = strategy
        self.observer = observer or VisiblePlayerObserver()

    def choose_action(self, state: GameState) -> InputAction | None:
        observation = self.observer.observe(state)
        action = self.strategy.choose(observation)
        if action is None:
            return None
        return InputAction(self.player, action)
