"""Stateful standard CPU strategy using only PlayerObservation."""

from collections import deque

from tetris.observation import PlayerObservation

from .standard_cpu_profile import StandardCpuProfile
from .visible_board_evaluator import VisibleBoardEvaluator, VisibleBoardWeights
from .visible_placement_planner import VisiblePlacementPlanner


class StandardCpuStrategy:
    """Emit one semantic action at a time from a visible-only placement plan."""

    def __init__(
        self,
        profile: StandardCpuProfile,
        planner: VisiblePlacementPlanner | None = None,
        weights: VisibleBoardWeights | None = None,
    ):
        if planner is not None and weights is not None:
            raise ValueError("planner and weights cannot both be supplied")
        self.profile = profile
        self.planner = planner or VisiblePlacementPlanner(
            evaluator=VisibleBoardEvaluator(weights),
            search_depth=profile.search_depth,
            lookahead_discount=profile.lookahead_discount,
        )
        self._actions: deque[str] = deque()
        self._cooldown = 0

    def choose(self, observation: PlayerObservation) -> str | None:
        if self._cooldown > 0:
            self._cooldown -= 1
            return None

        if not self._actions:
            try:
                move = self.planner.choose(observation)
            except ValueError:
                return None
            self._actions.extend(move.actions)

        action = self._actions.popleft()
        self._cooldown = self.profile.action_interval_ticks - 1
        return action

    def reset(self) -> None:
        self._actions.clear()
        self._cooldown = 0
