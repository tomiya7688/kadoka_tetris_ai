"""Seeded Monte Carlo lookahead over player-visible NEXT pieces only."""
from dataclasses import dataclass
import random
from tetris.observation import PlayerObservation


@dataclass(frozen=True)
class MonteCarloPlannedMove:
    rotation: int
    x: int
    score: float
    actions: tuple[str, ...]
    used_hold: bool = False


@dataclass(frozen=True)
class MonteCarloSettings:
    rollouts: int = 8
    rollout_width: int = 2
    max_visible_future: int = 3
    seed: int = 0
    discount: float = 0.5

    def __post_init__(self):
        if not isinstance(self.rollouts, int) or isinstance(self.rollouts, bool) or not 1 <= self.rollouts <= 10000:
            raise ValueError('rollouts must be between 1 and 10000')
        if not isinstance(self.rollout_width, int) or isinstance(self.rollout_width, bool) or self.rollout_width < 1:
            raise ValueError('rollout_width must be positive')
        if not isinstance(self.max_visible_future, int) or isinstance(self.max_visible_future, bool) or self.max_visible_future < 0:
            raise ValueError('max_visible_future must be nonnegative')
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError('seed must be an integer')
        if not isinstance(self.discount, (int, float)) or isinstance(self.discount, bool) or not 0.0 <= self.discount <= 1.0:
            raise ValueError('discount must be between 0 and 1')


class MonteCarloPlanner:
    """Sample future placements from visible NEXT, without bag or RNG access."""

    def __init__(self, evaluator=None, settings=None):
        from tetris.cpu.visible_placement_planner import VisiblePlacementPlanner
        if evaluator is None:
            from tetris.cpu.visible_board_evaluator import VisibleBoardEvaluator
            evaluator = VisibleBoardEvaluator()
        self.evaluator = evaluator
        self.settings = settings or MonteCarloSettings()
        self.placement_planner = VisiblePlacementPlanner(evaluator=self.evaluator, search_depth=1)

    def choose(self, observation: PlayerObservation) -> MonteCarloPlannedMove:
        if observation.current_piece is None:
            raise ValueError('current piece is not visible')
        board = observation.board
        rng = random.Random(self.settings.seed)
        best_move = None
        future_limit = min(self.settings.max_visible_future, len(observation.next_pieces))
        for option in self.placement_planner._root_options(observation):
            for placement in self.placement_planner._reachable_placements(
                board.locked_cells, option.piece, board.width, board.height
            ):
                immediate = self.evaluator.score(
                    placement.cells, board.width, board.height, placement.cleared_lines
                )
                returns = [
                    self._rollout(
                        placement.cells, option.future_pieces[:future_limit],
                        board.width, board.height, rng,
                    )
                    for _ in range(self.settings.rollouts)
                ]
                score = immediate + self.settings.discount * (sum(returns) / len(returns))
                actions = placement.actions
                if option.used_hold:
                    actions = ('hold',) + actions
                move = MonteCarloPlannedMove(
                    rotation=placement.rotation,
                    x=placement.x,
                    score=score,
                    actions=actions,
                    used_hold=option.used_hold,
                )
                if best_move is None or move.score > best_move.score:
                    best_move = move
        if best_move is None:
            raise ValueError('no legal visible placement')
        return best_move

    def _rollout(self, cells, future_pieces, width, height, rng):
        total = 0.0
        discount = 1.0
        for piece in future_pieces:
            placements = self.placement_planner._drop_placements(cells, piece, width, height)
            if not placements:
                return total - 1000000.0 * discount
            ranked = sorted(
                placements,
                key=lambda item: self.evaluator.score(
                    item.cells, width, height, item.cleared_lines
                ),
                reverse=True,
            )
            selected = rng.choice(ranked[:self.settings.rollout_width])
            total += discount * self.evaluator.score(
                selected.cells, width, height, selected.cleared_lines
            )
            discount *= self.settings.discount
            cells = selected.cells
        return total
