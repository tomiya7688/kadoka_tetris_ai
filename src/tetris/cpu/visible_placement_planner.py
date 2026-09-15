"""Placement search that consumes only player-visible observations."""

from dataclasses import dataclass

from tetris.core import PieceType
from tetris.core.tetromino import SHAPES
from tetris.observation import Cell, PlayerObservation

from .visible_board_evaluator import VisibleBoardEvaluator


@dataclass(frozen=True)
class VisiblePlannedMove:
    rotation: int
    x: int
    score: float
    actions: tuple[str, ...]


@dataclass(frozen=True)
class _PlacementResult:
    cells: frozenset[Cell]
    cleared_lines: int
    rotation: int
    x: int


class VisiblePlacementPlanner:
    """Search current and visible NEXT pieces without accessing the bag or RNG."""

    def __init__(
        self,
        evaluator: VisibleBoardEvaluator | None = None,
        search_depth: int = 2,
        lookahead_discount: float = 0.35,
    ):
        if search_depth < 1:
            raise ValueError("search_depth must be at least 1")
        if not 0.0 <= lookahead_discount <= 1.0:
            raise ValueError("lookahead_discount must be between 0 and 1")
        self.evaluator = evaluator or VisibleBoardEvaluator()
        self.search_depth = search_depth
        self.lookahead_discount = lookahead_discount

    def choose(self, observation: PlayerObservation) -> VisiblePlannedMove:
        if observation.current_piece is None:
            raise ValueError("current piece is not visible")

        board = observation.board
        pieces = (observation.current_piece,) + observation.next_pieces
        depth = min(self.search_depth, len(pieces))
        memo: dict[tuple[frozenset[Cell], tuple[PieceType, ...], int], float] = {}
        best_move = None

        for placement in self._placements(
            board.locked_cells,
            pieces[0],
            board.width,
            board.height,
        ):
            score = self.evaluator.score(
                placement.cells,
                board.width,
                board.height,
                placement.cleared_lines,
            )
            if depth > 1:
                future_score = self._best_future_score(
                    placement.cells,
                    pieces[1:],
                    depth - 1,
                    board.width,
                    board.height,
                    memo,
                )
                score += self.lookahead_discount * future_score

            move = VisiblePlannedMove(
                rotation=placement.rotation,
                x=placement.x,
                score=score,
                actions=self._actions_for(
                    placement.rotation,
                    placement.x,
                    board.width,
                ),
            )
            if best_move is None or move.score > best_move.score:
                best_move = move

        if best_move is None:
            raise ValueError("no legal visible placement")
        return best_move

    def _best_future_score(
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

        best = None
        for placement in self._placements(cells, pieces[0], width, height):
            score = self.evaluator.score(
                placement.cells,
                width,
                height,
                placement.cleared_lines,
            )
            if depth > 1 and len(pieces) > 1:
                score += self.lookahead_discount * self._best_future_score(
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

    def _placements(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        width: int,
        height: int,
    ) -> tuple[_PlacementResult, ...]:
        placements = []
        for rotation, shape in self._rotations(piece):
            shape_width = max(x for x, _ in shape) + 1
            for x in range(0, width - shape_width + 1):
                y = 0
                if not self._can_place(locked_cells, shape, x, y, width, height):
                    continue
                while self._can_place(
                    locked_cells,
                    shape,
                    x,
                    y + 1,
                    width,
                    height,
                ):
                    y += 1

                placed = locked_cells | frozenset(
                    (x + local_x, y + local_y)
                    for local_x, local_y in shape
                )
                cleared_cells, cleared_lines = self._clear_full_rows(
                    placed,
                    width,
                    height,
                )
                placements.append(
                    _PlacementResult(
                        cells=cleared_cells,
                        cleared_lines=cleared_lines,
                        rotation=rotation,
                        x=x,
                    )
                )
        return tuple(placements)

    def _rotations(
        self,
        piece: PieceType,
    ) -> tuple[tuple[int, tuple[Cell, ...]], ...]:
        shape = tuple(SHAPES[piece])
        rotations = []
        seen = set()
        for rotation in range(4):
            normalized = self._normalize(shape)
            if normalized not in seen:
                seen.add(normalized)
                rotations.append((rotation, normalized))
            shape = tuple((-y, x) for x, y in shape)
        return tuple(rotations)

    def _normalize(self, shape: tuple[Cell, ...]) -> tuple[Cell, ...]:
        min_x = min(x for x, _ in shape)
        min_y = min(y for _, y in shape)
        return tuple(sorted((x - min_x, y - min_y) for x, y in shape))

    def _can_place(
        self,
        locked_cells: frozenset[Cell],
        shape: tuple[Cell, ...],
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> bool:
        for local_x, local_y in shape:
            cell_x = x + local_x
            cell_y = y + local_y
            if cell_x < 0 or cell_x >= width or cell_y < 0 or cell_y >= height:
                return False
            if (cell_x, cell_y) in locked_cells:
                return False
        return True

    def _clear_full_rows(
        self,
        cells: frozenset[Cell],
        width: int,
        height: int,
    ) -> tuple[frozenset[Cell], int]:
        full_rows = {
            y
            for y in range(height)
            if sum(1 for x in range(width) if (x, y) in cells) == width
        }
        if not full_rows:
            return cells, 0

        remaining = []
        for x, y in cells:
            if y in full_rows:
                continue
            drop = sum(1 for full_y in full_rows if full_y > y)
            remaining.append((x, y + drop))
        return frozenset(remaining), len(full_rows)

    def _actions_for(
        self,
        rotation: int,
        target_x: int,
        width: int,
    ) -> tuple[str, ...]:
        if rotation == 0:
            rotation_actions = ()
        elif rotation == 1:
            rotation_actions = ("rotate_cw",)
        elif rotation == 2:
            rotation_actions = ("rotate_cw", "rotate_cw")
        else:
            rotation_actions = ("rotate_ccw",)

        spawn_x = (width - 4) // 2
        delta_x = target_x - spawn_x
        if delta_x < 0:
            movement_actions = ("move_left",) * -delta_x
        else:
            movement_actions = ("move_right",) * delta_x
        return rotation_actions + movement_actions + ("hard_drop",)
