"""Build a player-visible observation without exposing engine internals."""

from tetris.core import GameState

from .player_observation import PlayerObservation
from .visible_board_observer import VisibleBoardObserver


class VisiblePlayerObserver:
    """Create the same information contract that the current UI displays."""

    def __init__(self, board_observer: VisibleBoardObserver | None = None):
        self.board_observer = board_observer or VisibleBoardObserver()

    def observe(self, state: GameState) -> PlayerObservation:
        current_piece = state.active.kind if state.active is not None else None
        return PlayerObservation(
            board=self.board_observer.observe(state),
            current_piece=current_piece,
            hold_piece=state.hold,
            next_pieces=state.next_pieces,
        )
