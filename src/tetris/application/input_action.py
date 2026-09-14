"""Shared semantic input action model for human and external inputs."""

from dataclasses import dataclass


SEMANTIC_ACTIONS = frozenset(
    {
        "move_left",
        "move_right",
        "rotate_cw",
        "rotate_ccw",
        "soft_drop",
        "hard_drop",
        "hold",
    }
)


@dataclass(frozen=True)
class InputAction:
    """A player-visible semantic action before tick/sequence scheduling."""

    player: int
    action: str

    def __post_init__(self) -> None:
        if not isinstance(self.player, int) or isinstance(self.player, bool):
            raise ValueError("player must be a nonnegative integer")
        if self.player < 0:
            raise ValueError("player must be a nonnegative integer")
        if self.action not in SEMANTIC_ACTIONS:
            raise ValueError("unknown action")
