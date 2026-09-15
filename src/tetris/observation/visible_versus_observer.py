"""Build versus observations only from information rendered to both players."""

from tetris.core import GameState

from .versus_player_observation import VersusPlayerObservation
from .visible_player_observer import VisiblePlayerObserver


class VisibleVersusObserver:
    """Compose two visible player observations with displayed garbage meters."""

    def __init__(self, player_observer: VisiblePlayerObserver | None = None):
        self.player_observer = player_observer or VisiblePlayerObserver()

    def observe(
        self,
        own_state: GameState,
        opponent_state: GameState,
        incoming_garbage: int,
        opponent_incoming_garbage: int,
    ) -> VersusPlayerObservation:
        return VersusPlayerObservation(
            own=self.player_observer.observe(own_state),
            opponent=self.player_observer.observe(opponent_state),
            incoming_garbage=incoming_garbage,
            opponent_incoming_garbage=opponent_incoming_garbage,
        )
