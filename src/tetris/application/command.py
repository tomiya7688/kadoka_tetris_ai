from dataclasses import dataclass
from typing import Any

from .input_action import SEMANTIC_ACTIONS


ALLOWED = SEMANTIC_ACTIONS


@dataclass(frozen=True)
class Command:
    player: int
    tick: int
    sequence: int
    action: str

    def __post_init__(self) -> None:
        if not isinstance(self.player, int) or isinstance(self.player, bool) or self.player < 0:
            raise ValueError("player must be nonnegative integer")
        if (
            not isinstance(self.tick, int)
            or isinstance(self.tick, bool)
            or self.tick < 0
            or not isinstance(self.sequence, int)
            or isinstance(self.sequence, bool)
            or self.sequence < 0
        ):
            raise ValueError("tick and sequence must be nonnegative integers")
        if not isinstance(self.action, str) or self.action not in ALLOWED:
            raise ValueError("unknown action")

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        if not isinstance(data, dict):
            raise ValueError("command must be an object")
        try:
            return cls(
                player=data["player"],
                tick=data["tick"],
                sequence=data["sequence"],
                action=data["action"],
            )
        except KeyError as exc:
            raise ValueError(f"missing field: {exc.args[0]}") from exc
