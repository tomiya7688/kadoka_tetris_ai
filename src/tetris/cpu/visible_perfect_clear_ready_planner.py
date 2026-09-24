"""T-Spin planner with bounded long-horizon Perfect Clear readiness."""

import math

from .visible_board_evaluator import VisibleBoardEvaluator
from .visible_perfect_clear_readiness import VisiblePerfectClearReadinessEvaluator
from .visible_t_spin_ready_planner import VisibleTSpinReadyPlanner


VISIBLE_PERFECT_CLEAR_READY_PLANNER_ID = "visible-perfect-clear-ready-v1"


class _PerfectClearAwareEvaluator(VisibleBoardEvaluator):
    def __init__(
        self,
        base_evaluator: VisibleBoardEvaluator,
        readiness_evaluator: VisiblePerfectClearReadinessEvaluator,
        readiness_weight: float,
    ):
        self.base_evaluator = base_evaluator
        self.readiness_evaluator = readiness_evaluator
        self.readiness_weight = readiness_weight
        self.weights = base_evaluator.weights

    def score(
        self,
        cells,
        width: int,
        height: int,
        cleared_lines: int = 0,
    ) -> float:
        return self.base_evaluator.score(
            cells,
            width,
            height,
            cleared_lines,
        ) + self.readiness_weight * self.readiness_evaluator.score(
            cells,
            width,
            height,
        )


class VisiblePerfectClearReadyPlanner(VisibleTSpinReadyPlanner):
    """Preserve nearby geometric Perfect Clear completions without hidden state.

    Immediate Perfect Clears are already rewarded by the attack-aware parent planner.
    This class only adds a small board-shape signal when the visible stack can be
    completed into empty-board clears within a few generic tetrominoes. It does not
    assume that those hidden future pieces will actually arrive.
    """

    def __init__(
        self,
        evaluator: VisibleBoardEvaluator | None = None,
        search_depth: int = 2,
        lookahead_discount: float = 0.35,
        spawn_y: int = -2,
        attack_weight: float = 2.0,
        readiness_weight: float = 0.75,
        perfect_clear_readiness_weight: float = 0.5,
    ):
        if (
            not isinstance(perfect_clear_readiness_weight, (int, float))
            or isinstance(perfect_clear_readiness_weight, bool)
            or not math.isfinite(float(perfect_clear_readiness_weight))
            or perfect_clear_readiness_weight < 0
        ):
            raise ValueError(
                "perfect_clear_readiness_weight must be a finite nonnegative number"
            )

        base_evaluator = evaluator or VisibleBoardEvaluator()
        self.perfect_clear_readiness_evaluator = (
            VisiblePerfectClearReadinessEvaluator()
        )
        self.perfect_clear_readiness_weight = float(
            perfect_clear_readiness_weight
        )
        self.base_board_evaluator = base_evaluator

        super().__init__(
            evaluator=_PerfectClearAwareEvaluator(
                base_evaluator,
                self.perfect_clear_readiness_evaluator,
                self.perfect_clear_readiness_weight,
            ),
            search_depth=search_depth,
            lookahead_discount=lookahead_discount,
            spawn_y=spawn_y,
            attack_weight=attack_weight,
            readiness_weight=readiness_weight,
        )
