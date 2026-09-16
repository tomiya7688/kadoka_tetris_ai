"""Attack planner with a lightweight long-horizon T-Spin readiness signal."""

import math

from .visible_attack_placement_planner import VisibleAttackPlacementPlanner
from .visible_board_evaluator import VisibleBoardEvaluator
from .visible_t_spin_readiness import VisibleTSpinReadinessEvaluator


VISIBLE_T_SPIN_READY_PLANNER_ID = "visible-t-spin-ready-v1"


class _ReadinessAwareEvaluator(VisibleBoardEvaluator):
    def __init__(
        self,
        base_evaluator: VisibleBoardEvaluator,
        readiness_evaluator: VisibleTSpinReadinessEvaluator,
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
        ) + self.readiness_weight * self.readiness_evaluator.best_attack(
            cells,
            width,
            height,
        )


class VisibleTSpinReadyPlanner(VisibleAttackPlacementPlanner):
    """Preserve useful visible T-Spin slots even when T is beyond search depth.

    Actual current/visible-NEXT T pieces still use the parent's reachable semantic
    action search.  This class only adds a cheap geometric readiness signal to board
    evaluation so a good T slot is less likely to be filled before a future T becomes
    visible within the search horizon.
    """

    def __init__(
        self,
        evaluator: VisibleBoardEvaluator | None = None,
        search_depth: int = 2,
        lookahead_discount: float = 0.35,
        spawn_y: int = -2,
        attack_weight: float = 2.0,
        readiness_weight: float = 0.75,
    ):
        if (
            not isinstance(readiness_weight, (int, float))
            or isinstance(readiness_weight, bool)
            or not math.isfinite(float(readiness_weight))
            or readiness_weight < 0
        ):
            raise ValueError("readiness_weight must be a finite nonnegative number")

        base_evaluator = evaluator or VisibleBoardEvaluator()
        self.readiness_evaluator = VisibleTSpinReadinessEvaluator()
        self.readiness_weight = float(readiness_weight)
        self.base_evaluator = base_evaluator
        super().__init__(
            evaluator=_ReadinessAwareEvaluator(
                base_evaluator,
                self.readiness_evaluator,
                self.readiness_weight,
            ),
            search_depth=search_depth,
            lookahead_discount=lookahead_discount,
            spawn_y=spawn_y,
            attack_weight=attack_weight,
        )
