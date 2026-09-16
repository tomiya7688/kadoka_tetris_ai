"""Built-in versus CPU boundary exposing only information rendered in versus play."""

from typing import Protocol

from tetris.application import InputAction, VersusSession
from tetris.observation import VersusPlayerObservation, VisibleVersusObserver


class VisibleVersusCpuStrategy(Protocol):
    """Decision logic intentionally isolated from VersusSession and GameState."""

    def choose(self, observation: VersusPlayerObservation) -> str | None:
        ...


class VisibleVersusCpuController:
    """Translate a visible versus decision into the shared semantic input path."""

    def __init__(
        self,
        player: int,
        strategy: VisibleVersusCpuStrategy,
        observer: VisibleVersusObserver | None = None,
    ):
        if player not in (0, 1):
            raise ValueError("versus CPU player must be 0 or 1")
        self.player = player
        self.strategy = strategy
        self.observer = observer or VisibleVersusObserver()

    def choose_action(self, session: VersusSession) -> InputAction | None:
        if self.player not in session.games or len(session.games) != 2:
            raise ValueError("controller player must belong to a two-player session")
        opponent = next(player for player in session.games if player != self.player)
        observation = self.observer.observe(
            own_state=session.games[self.player],
            opponent_state=session.games[opponent],
            incoming_garbage=session.results[self.player].incoming_garbage,
            opponent_incoming_garbage=session.results[opponent].incoming_garbage,
        )
        action = self.strategy.choose(observation)
        if action is None:
            return None
        return InputAction(self.player, action)
