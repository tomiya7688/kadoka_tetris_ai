"""Placement search that consumes only player-visible observations."""

from collections import deque
from dataclasses import dataclass

from tetris.core import ActivePiece, PieceType
from tetris.observation import Cell, PlayerObservation

from .visible_board_evaluator import VisibleBoardEvaluator


@dataclass(frozen=True)
class VisiblePlannedMove:
    rotation: int
    x: int
    score: float
    actions: tuple[str, ...]
    used_hold: bool = False


@dataclass(frozen=True)
class _PlacementResult:
    cells: frozenset[Cell]
    cleared_lines: int
    rotation: int
    x: int
    actions: tuple[str, ...] = ()
    last_rotation: bool = False


@dataclass(frozen=True)
class _SearchState:
    x: int
    y: int
    rotation: int
    last_rotation: bool
    actions: tuple[str, ...]


@dataclass(frozen=True)
class _RootOption:
    piece: PieceType
    future_pieces: tuple[PieceType, ...]
    used_hold: bool


class VisiblePlacementPlanner:
    """Search current/HOLD and visible NEXT pieces without bag or RNG access.

    The current piece is searched with semantic move/rotate/soft-drop transitions that
    mirror the public rules engine.  This guarantees that the emitted root action
    sequence is reachable instead of merely assuming that every final geometry can be
    produced.  Deeper NEXT lookahead remains a cheaper geometric drop approximation;
    every piece is replanned with reachable search once it becomes current.
    """

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
                score = self.evaluator.score(
                    placement.cells,
                    board.width,
                    board.height,
                    placement.cleared_lines,
                )
                if depth > 1:
                    future_score = self._best_future_score(
                        placement.cells,
                        option.future_pieces,
                        depth - 1,
                        board.width,
                        board.height,
                        memo,
                    )
                    score += self.lookahead_discount * future_score

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

    def _root_options(self, observation: PlayerObservation) -> tuple[_RootOption, ...]:
        current_piece = observation.current_piece
        if current_piece is None:
            return ()

        options = [
            _RootOption(
                piece=current_piece,
                future_pieces=observation.next_pieces,
                used_hold=False,
            )
        ]

        if observation.hold_piece is not None:
            options.append(
                _RootOption(
                    piece=observation.hold_piece,
                    future_pieces=observation.next_pieces,
                    used_hold=True,
                )
            )
        elif observation.next_pieces:
            options.append(
                _RootOption(
                    piece=observation.next_pieces[0],
                    future_pieces=observation.next_pieces[1:],
                    used_hold=True,
                )
            )

        return tuple(options)

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
        for placement in self._drop_placements(cells, pieces[0], width, height):
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

    def _reachable_placements(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        width: int,
        height: int,
    ) -> tuple[_PlacementResult, ...]:
        spawn = _SearchState(
            x=(width - 4) // 2,
            y=0,
            rotation=0,
            last_rotation=False,
            actions=(),
        )
        if not self._can_place_state(locked_cells, piece, spawn, width, height):
            return ()

        queue = deque([spawn])
        seen = {self._state_key(spawn)}
        placements: dict[
            tuple[frozenset[Cell], int, bool],
            _PlacementResult,
        ] = {}

        while queue:
            state = queue.popleft()
            placement = self._hard_drop_result(
                locked_cells,
                piece,
                state,
                width,
                height,
            )
            final_cells = self._absolute_cells(
                piece,
                placement.rotation,
                placement.x,
                self._hard_drop_y(
                    locked_cells,
                    piece,
                    state,
                    width,
                    height,
                ),
            )
            placement_key = (
                final_cells,
                placement.rotation % 4,
                placement.last_rotation,
            )
            previous = placements.get(placement_key)
            if previous is None or len(placement.actions) < len(previous.actions):
                placements[placement_key] = placement

            for next_state in self._successors(
                locked_cells,
                piece,
                state,
                width,
                height,
            ):
                key = self._state_key(next_state)
                if key in seen:
                    continue
                seen.add(key)
                queue.append(next_state)

        return tuple(placements.values())

    def _successors(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        state: _SearchState,
        width: int,
        height: int,
    ) -> tuple[_SearchState, ...]:
        successors = []

        for dx, action in ((-1, "move_left"), (1, "move_right")):
            candidate = _SearchState(
                state.x + dx,
                state.y,
                state.rotation,
                False,
                state.actions + (action,),
            )
            if self._can_place_state(locked_cells, piece, candidate, width, height):
                successors.append(candidate)

        for direction, action in ((1, "rotate_cw"), (-1, "rotate_ccw")):
            candidate = self._rotate_state(
                locked_cells,
                piece,
                state,
                direction,
                action,
                width,
                height,
            )
            if candidate is not None:
                successors.append(candidate)

        candidate = _SearchState(
            state.x,
            state.y + 1,
            state.rotation,
            state.last_rotation,
            state.actions + ("soft_drop",),
        )
        if self._can_place_state(locked_cells, piece, candidate, width, height):
            successors.append(candidate)

        return tuple(successors)

    def _rotate_state(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        state: _SearchState,
        direction: int,
        action: str,
        width: int,
        height: int,
    ) -> _SearchState | None:
        rotation = state.rotation + direction
        for dx in (0, -1, 1, -2, 2):
            candidate = _SearchState(
                state.x + dx,
                state.y,
                rotation,
                True,
                state.actions + (action,),
            )
            if self._can_place_state(locked_cells, piece, candidate, width, height):
                return candidate
        return None

    def _hard_drop_result(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        state: _SearchState,
        width: int,
        height: int,
    ) -> _PlacementResult:
        y = self._hard_drop_y(locked_cells, piece, state, width, height)
        placed = locked_cells | self._absolute_cells(
            piece,
            state.rotation,
            state.x,
            y,
        )
        cleared_cells, cleared_lines = self._clear_full_rows(placed, width, height)
        return _PlacementResult(
            cells=cleared_cells,
            cleared_lines=cleared_lines,
            rotation=state.rotation % 4,
            x=state.x,
            actions=state.actions + ("hard_drop",),
            last_rotation=state.last_rotation,
        )

    def _hard_drop_y(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        state: _SearchState,
        width: int,
        height: int,
    ) -> int:
        y = state.y
        while self._can_place(
            locked_cells,
            self._piece_cells(piece, state.rotation),
            state.x,
            y + 1,
            width,
            height,
        ):
            y += 1
        return y

    def _drop_placements(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        width: int,
        height: int,
    ) -> tuple[_PlacementResult, ...]:
        placements = []
        seen_shapes = set()
        for rotation in range(4):
            shape = self._piece_cells(piece, rotation)
            if shape in seen_shapes:
                continue
            seen_shapes.add(shape)
            min_x = min(x for x, _ in shape)
            max_x = max(x for x, _ in shape)
            for x in range(-min_x, width - max_x):
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

    @staticmethod
    def _piece_cells(piece: PieceType, rotation: int) -> tuple[Cell, ...]:
        return tuple(ActivePiece(piece, 0, 0, rotation).cells())

    def _can_place_state(
        self,
        locked_cells: frozenset[Cell],
        piece: PieceType,
        state: _SearchState,
        width: int,
        height: int,
    ) -> bool:
        return self._can_place(
            locked_cells,
            self._piece_cells(piece, state.rotation),
            state.x,
            state.y,
            width,
            height,
        )

    def _absolute_cells(
        self,
        piece: PieceType,
        rotation: int,
        x: int,
        y: int,
    ) -> frozenset[Cell]:
        return frozenset(
            (x + local_x, y + local_y)
            for local_x, local_y in self._piece_cells(piece, rotation)
        )

    @staticmethod
    def _state_key(state: _SearchState) -> tuple[int, int, int, bool]:
        return state.x, state.y, state.rotation % 4, state.last_rotation

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
