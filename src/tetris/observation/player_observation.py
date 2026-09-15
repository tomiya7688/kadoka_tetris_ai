"""Immutable snapshot of information currently visible to a player."""

from dataclasses import dataclass

from tetris.core import PieceType

from .board_observation import BoardObservation


@dataclass(frozen=True)
class PlayerObservation:
    """Visible board, active piece identity, HOLD, and displayed NEXT queue."""

    board: BoardObservation
    current_piece: PieceType | None
    hold_piece: PieceType | None
    next_pieces: tuple[PieceType, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.board, BoardObservation):
            raise ValueError("board must be a BoardObservation")
        self._validate_piece(self.current_piece, "current_piece")
        self._validate_piece(self.hold_piece, "hold_piece")

        normalized_next = tuple(self.next_pieces)
        for piece in normalized_next:
            if not isinstance(piece, PieceType):
                raise ValueError("next_pieces must contain PieceType values")
        object.__setattr__(self, "next_pieces", normalized_next)

    def _validate_piece(self, piece: PieceType | None, name: str) -> None:
        if piece is not None and not isinstance(piece, PieceType):
            raise ValueError(f"{name} must be PieceType or None")
