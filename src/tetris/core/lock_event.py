"""Normalized result of locking one tetromino into the field."""

from dataclasses import dataclass

from .tetromino import PieceType


@dataclass(frozen=True)
class LockEvent:
    """Combat-relevant result of one completed placement.

    The event is an internal game result, not an AI observation.  Consumers such as
    versus coordination and benchmarks may use it for scoring/measurement, while
    visible-only CPUs must continue to receive PlayerObservation instead.
    """

    lock_id: int
    piece: PieceType
    lines: int
    t_spin: bool
    combo: int
    back_to_back: bool
    perfect_clear: bool

    @property
    def difficult_clear(self) -> bool:
        return self.lines == 4 or (self.t_spin and self.lines > 0)
