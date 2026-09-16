"""Opponent-aware standard CPU strategy using only visible versus observations."""

from collections import deque
from dataclasses import replace

from tetris.observation import BoardObservation, VersusPlayerObservation

from .standard_cpu_profile import StandardCpuProfile
from .visible_board_evaluator import VisibleBoardEvaluator, VisibleBoardWeights
from .visible_placement_planner import VisiblePlacementPlanner


VERSUS_STANDARD_CPU_IMPLEMENTATION_ID = "standard-visible-versus-v1"


class VersusStandardCpuStrategy:
    """Keep standard planning simple while reacting to visible versus pressure.

    A mode is selected only when a new piece plan is required. The complete semantic
    action sequence is then retained until it is exhausted, so opponent changes do not
    make the CPU thrash between partially executed placements.
    """

    def __init__(
        self,
        profile: StandardCpuProfile,
        weights: VisibleBoardWeights | None = None,
    ):
        self.profile = profile
        self.base_weights = weights or VisibleBoardWeights()
        self._actions: deque[str] = deque()
        self._cooldown = 0
        self.last_mode = "neutral"

    def choose(self, observation: VersusPlayerObservation) -> str | None:
        if self._cooldown > 0:
            self._cooldown -= 1
            return None

        if not self._actions:
            mode = self._select_mode(observation)
            planner = self._planner_for_mode(mode)
            try:
                move = planner.choose(observation.own)
            except ValueError:
                return None
            self.last_mode = mode
            self._actions.extend(move.actions)

        action = self._actions.popleft()
        self._cooldown = self.profile.action_interval_ticks - 1
        return action

    def reset(self) -> None:
        self._actions.clear()
        self._cooldown = 0
        self.last_mode = "neutral"

    def _select_mode(self, observation: VersusPlayerObservation) -> str:
        own_height = self._stack_height(observation.own.board)
        opponent_height = self._stack_height(observation.opponent.board)

        # Incoming garbage and a high own stack are immediate survival concerns.
        if observation.incoming_garbage >= 3 or own_height >= 15:
            return "defense"

        # Push line efficiency when the opponent is visibly vulnerable or already
        # carrying a meaningful pending garbage queue.
        if opponent_height >= 14 or observation.opponent_incoming_garbage >= 4:
            return "pressure"

        return "neutral"

    def _planner_for_mode(self, mode: str) -> VisiblePlacementPlanner:
        weights = self._weights_for_mode(mode)
        return VisiblePlacementPlanner(
            evaluator=VisibleBoardEvaluator(weights),
            search_depth=self.profile.search_depth,
            lookahead_discount=self.profile.lookahead_discount,
        )

    def _weights_for_mode(self, mode: str) -> VisibleBoardWeights:
        if mode == "neutral":
            return self.base_weights
        if mode == "defense":
            return replace(
                self.base_weights,
                cleared_lines=self.base_weights.cleared_lines * 1.25,
                aggregate_height=self.base_weights.aggregate_height * 1.35,
                max_height=self.base_weights.max_height * 1.50,
                holes=self.base_weights.holes * 1.40,
                covered_hole_cells=self.base_weights.covered_hole_cells * 1.50,
                bumpiness=self.base_weights.bumpiness * 1.10,
            )
        if mode == "pressure":
            return replace(
                self.base_weights,
                cleared_lines=self.base_weights.cleared_lines * 1.75,
                aggregate_height=self.base_weights.aggregate_height * 0.85,
                max_height=self.base_weights.max_height * 0.85,
                bumpiness=self.base_weights.bumpiness * 0.90,
            )
        raise ValueError(f"unknown versus CPU mode: {mode}")

    @staticmethod
    def _stack_height(board: BoardObservation) -> int:
        if not board.locked_cells:
            return 0
        return board.height - min(y for _, y in board.locked_cells)
