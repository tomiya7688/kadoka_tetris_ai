from dataclasses import dataclass
from typing import Any
ALLOWED={"move_left","move_right","rotate_cw","rotate_ccw","soft_drop","hard_drop","hold"}
@dataclass(frozen=True)
class Command:
    player: int
    tick: int
    sequence: int
    action: str
    @classmethod
    def from_dict(cls,data: dict[str,Any]):
        if not isinstance(data,dict): raise ValueError("command must be an object")
        try: player,tick,sequence,action=data["player"],data["tick"],data["sequence"],data["action"]
        except KeyError as e: raise ValueError(f"missing field: {e.args[0]}") from e
        if not isinstance(player,int) or player<0: raise ValueError("player must be nonnegative integer")
        if not isinstance(tick,int) or tick<0 or not isinstance(sequence,int) or sequence<0: raise ValueError("tick and sequence must be nonnegative integers")
        if action not in ALLOWED: raise ValueError("unknown action")
        return cls(player,tick,sequence,action)
