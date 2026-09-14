"""Route semantic input actions into the tick-scheduled command engine."""

from collections import defaultdict

from .command import Command
from .input_action import InputAction
from .tick_engine import TickEngine


class InputRouter:
    """Assign deterministic sequence numbers and submit current-tick commands."""

    def __init__(self, engine: TickEngine):
        self._engine = engine
        self._next_sequence: dict[int, int] = defaultdict(int)

    def submit(self, input_action: InputAction) -> Command:
        sequence = self._next_sequence[input_action.player]
        command = Command(
            player=input_action.player,
            tick=self._engine.tick,
            sequence=sequence,
            action=input_action.action,
        )
        self._engine.submit(command)
        self._next_sequence[input_action.player] = sequence + 1
        return command
