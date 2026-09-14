"""Selectable lightweight Kadoka character AI."""

from tetris.core import GameState

from .kadoka_evaluator import KadokaEvaluator
from .planner import PlacementPlanner, PlannedMove


class KadokaAI:
    """Lightweight character AI backed by the existing placement planner."""

    DEFAULT_SPEED_MULTIPLIER = 0.4

    def __init__(
        self,
        seed: int = 0,
        speed_multiplier: float = DEFAULT_SPEED_MULTIPLIER,
        evaluator: KadokaEvaluator | None = None,
    ):
        if speed_multiplier <= 0:
            raise ValueError("speed_multiplier must be greater than zero")

        self.speed_multiplier = float(speed_multiplier)
        self.evaluator = evaluator or KadokaEvaluator(seed=seed)
        self.planner = PlacementPlanner(self.evaluator)

    def choose(self, state: GameState) -> PlannedMove:
        return self.planner.choose(state)
