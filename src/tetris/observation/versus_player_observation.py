"""Immutable snapshot of information shown in the two-player versus UI."""

from dataclasses import dataclass

from .player_observation import PlayerObservation


@dataclass(frozen=True)
class VersusPlayerObservation:
    """Visible own/opponent state plus both displayed garbage meters."""

    own: PlayerObservation
    opponent: PlayerObservation
    incoming_garbage: int
    opponent_incoming_garbage: int

    def __post_init__(self) -> None:
        if not isinstance(self.own, PlayerObservation):
            raise ValueError("own must be a PlayerObservation")
        if not isinstance(self.opponent, PlayerObservation):
            raise ValueError("opponent must be a PlayerObservation")
        self._validate_garbage(self.incoming_garbage, "incoming_garbage")
        self._validate_garbage(
            self.opponent_incoming_garbage,
            "opponent_incoming_garbage",
        )

    def _validate_garbage(self, value: int, name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
