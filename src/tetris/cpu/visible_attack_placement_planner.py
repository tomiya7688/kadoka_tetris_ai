"""Attack-aware placement scoring built on the reachable visible planner."""

import math

from tetris.core import PieceType, attack_for_clear, is_t_spin_placement
from tetris.observation import Cell, PlayerObservation

from .visible_board_evaluator import VisibleBoardEvaluator
from .visible_placement_planner import (
    VisiblePlacementPlanner,
    VisiblePlannedMove,
    _PlacementResult,
    _SearchState,
)


VISIBLE_ATTACK_PLANNER_ID = "visible-attack-v2"


class VisibleAttackPlacementPlanner(VisiblePlacementPlanner):
    """Reward attack that can be inferred from visible state and reachable paths.

    The estimate deliberately excludes combo and back-to-back bonuses because those
    counters are not part of the current player-visible observation. It can safely use
    line count, perfect clear, and the runtime's current three-corner T-Spin rule.

    Current-piece placements always use reachable semantic-action search. Future
    non-T pieces keep the cheaper geometric drop approximation, while visible future
    T pieces use reachable search too. This lets Normal/Hard lookahead value a T-Spin
    that becomes available after one or more setup placements without reading hidden
    bag state.
    """

    def __init__(
        self,
        evaluator: VisibleBoardEvaluator | None = None,
        search_depth: int = 2,
        lookahead_discount: float = 0.35,
        spawn_y: int = -2,
        attack_weight: float = 2.0,
    ):
        if (
            not isinstance(attack_weight, (int, float))
            or isinstance(attack_weight, bool)
            or not math.isfinite(float(attack_weight))
            or attack_weight < 0
        ):
            raise ValueError("attack_weight must be a finite nonnegative number")
        super().__init__(
            evaluator=evaluator,
            search_depth=search_depth,
            lookahead_discount=lookahead_discount,
            spawn_y=spawn_y,
        )
        self.attack_weight = float(attack_weight)

    def choose(self, observation: PlayerObservation) -> VisiblePlannedMove:
        if observation.current_piece is None:
            raise ValueError("current piece is not visible")

        board = observation.board
        memo: dict[tuple[frozenset[Cell], tuple[PieceType, ...], int], float] = {}
        best_move = None

        for option in self._root_options(observation):
            depth = min(self.search_depth, 1 + len(option.future_pieces))
            for placement in self._reachable_placements(
                board.locked_cells,
                option.piece,
                board.width,
                board.height,
            ):
                score = self._root_score(
                    board.locked_cells,
                    option.piece,
                    placement,
                    board.width,
                    board.height,
                )
                if depth > 1:
                    score += self.lookahead_discount * self._best_attack_future_score(
                        placement.cells,
                        option.future_pieces,
                        depth - 1,
                        board.width,
                        board.height,
                        memo,
                    )

                actions = placement.actions
                if option.used_hold:
                    actions = ("hold",) + actions
                move = VisiblePlannedMove(
                    rotation=placement.rotation,
                    x=placement.x,
                    score=score,
                    actions=actions,
                    used_hold=option.used_hold,
                )
                if best_move is None or move.score > best_move.score:
                    best_move = move

        if best_move is None:
            raise ValueError("no legal visible placement")
        return best_move

    def _root_score(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        placement: _PlacementResult,
        width: int,
        height: int,
    ) -> float:
        board_score = self.evaluator.score(
            placement.cells,
            width,
            height,
            placement.cleared_lines,
        )
        attack = self._visible_attack_for_reachable_placement(
            locked_cells,
            piece,
            placement,
            width,
            height,
        )
        return board_score + self.attack_weight * attack

    def _visible_attack_for_reachable_placement(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        placement: _PlacementResult,
        width: int,
        height: int,
    ) -> int:
        state = self._replay_before_hard_drop(
            locked_cells,
            piece,
            placement.actions,
            width,
            height,
        )
        final_y = self._hard_drop_y(
            locked_cells,
            piece,
            state,
            width,
            height,
        )
        t_spin = is_t_spin_placement(
            piece,
            state.rotation,
            state.x,
            final_y,
            width=width,
            height=height,
            occupied=lambda x, y: (x, y) in locked_cells,
            last_rotation=state.last_rotation,
            top_out_of_bounds_occupied=False,
        )
        perfect_clear = placement.cleared_lines > 0 and not placement.cells
        return attack_for_clear(
            placement.cleared_lines,
            t_spin=t_spin,
            perfect_clear=perfect_clear,
        )

    def _replay_before_hard_drop(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        actions: tuple[str, ...],
        width: int,
        height: int,
    ) -> _SearchState:
        state = _SearchState(
            x=(width - 4) // 2,
            y=self.spawn_y,
            rotation=0,
            last_rotation=False,
        )
        for action in actions:
            if action == "hard_drop":
                break
            if action == "move_left" or action == "move_right":
                dx = -1 if action == "move_left" else 1
                candidate = _SearchState(
                    state.x + dx,
                    state.y,
                    state.rotation,
                    False,
                )
            elif action == "soft_drop":
                candidate = _SearchState(
                    state.x,
                    state.y + 1,
                    state.rotation,
                    state.last_rotation,
                )
            elif action == "rotate_cw" or action == "rotate_ccw":
                direction = 1 if action == "rotate_cw" else -1
                rotated = self._rotate_state(
                    locked_cells,
                    piece,
                    state,
                    direction,
                    width,
                    height,
                )
                if rotated is None:
                    raise ValueError("reachable placement contains an invalid rotation")
                state = rotated
                continue
            else:
                raise ValueError(f"unexpected reachable placement action: {action}")

            if not self._can_place_state(
                locked_cells,
                piece,
                candidate,
                width,
                height,
            ):
                raise ValueError("reachable placement contains an invalid movement")
            state = candidate
        return state

    def _best_attack_future_score(
        self,
        cells: frozenset[Cell],
        pieces: tuple[PieceType, ...],
        depth: int,
        width: int,
        height: int,
        memo: dict[tuple[frozenset[Cell], tuple[PieceType, ...], int], float],
    ) -> float:
        if depth <= 0 or not pieces:
            return 0.0

        key = (cells, pieces[:depth], depth)
        cached = memo.get(key)
        if cached is not None:
            return cached

        piece = pieces[0]
        if piece == PieceType.T:
            placements = self._reachable_placements(
                cells,
                piece,
                width,
                height,
            )
        else:
            placements = self._drop_placements(cells, piece, width, height)

        best = None
        for placement in placements:
            if piece == PieceType.T:
                attack = self._visible_attack_for_reachable_placement(
                    cells,
                    piece,
                    placement,
                    width,
                    height,
                )
            else:
                perfect_clear = placement.cleared_lines > 0 and not placement.cells
                attack = attack_for_clear(
                    placement.cleared_lines,
                    perfect_clear=perfect_clear,
                )
            score = self.evaluator.score(
                placement.cells,
                width,
                height,
                placement.cleared_lines,
            ) + self.attack_weight * attack
            if depth > 1 and len(pieces) > 1:
                score += self.lookahead_discount * self._best_attack_future_score(
                    placement.cells,
                    pieces[1:],
                    depth - 1,
                    width,
                    height,
                    memo,
                )
            if best is None or score > best:
                best = score

        result = best if best is not None else -1000000.0
        memo[key] = result
        return result
