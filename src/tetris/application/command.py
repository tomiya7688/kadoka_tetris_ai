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

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        if not isinstance(data, dict):
            raise ValueError("command must be an object")
        try:
            player = data["player"]
            tick = data["tick"]
            sequence = data["sequence"]
            action = data["action"]
        except KeyError as exc:
            raise ValueError(f"missing field: {exc.args[0]}") from exc
        if not isinstance(player, int) or isinstance(player, bool) or player < 0:
            raise ValueError("player must be nonnegative integer")
        if (
            not isinstance(tick, int)
            or isinstance(tick, bool)
            or tick < 0
            or not isinstance(sequence, int)
            or isinstance(sequence, bool)
            or sequence < 0
        ):
            raise ValueError("tick and sequence must be nonnegative integers")
        if action not in ALLOWED:
            raise ValueError("unknown action")
        return cls(player, tick, sequence, action)
