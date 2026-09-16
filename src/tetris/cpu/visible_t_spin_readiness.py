"""Lightweight visible-only T-Spin slot readiness evaluation."""

from functools import lru_cache

from tetris.core import ActivePiece, PieceType, attack_for_clear, is_t_spin_placement
from tetris.observation import Cell


VISIBLE_T_SPIN_READINESS_ID = "visible-t-spin-readiness-v1"


class VisibleTSpinReadinessEvaluator:
    """Estimate preserved T-Spin attack potential from visible board geometry.

    This evaluator does not assume that a T piece is currently available and never
    reads bag/RNG state.  It searches only fully visible geometric T placements that
    would be resting, satisfy the runtime three-corner T-Spin rule, and clear at least
    one line.  The returned value is the best base attack such a future T could make.

    Reachability is deliberately not searched here: this is a cheap long-horizon
    readiness signal, while actual visible T pieces are validated by the planner's
    semantic-action search before their attack is scored.
    """

    def best_attack(
        self,
        cells: frozenset[Cell],
        width: int,
        height: int,
    ) -> int:
        best = 0
        for rotation in range(4):
            shape = self._t_cells(rotation)
            min_x = min(x for x, _ in shape)
            max_x = max(x for x, _ in shape)
            min_y = min(y for _, y in shape)
            max_y = max(y for _, y in shape)

            for origin_x in range(-min_x, width - max_x):
                for origin_y in range(-min_y, height - max_y):
                    piece_cells = frozenset(
                        (origin_x + local_x, origin_y + local_y)
                        for local_x, local_y in shape
                    )
                    if piece_cells & cells:
                        continue
                    if self._can_move_down(piece_cells, cells, height):
                        continue
                    if not is_t_spin_placement(
                        PieceType.T,
                        rotation,
                        origin_x,
                        origin_y,
                        width=width,
                        height=height,
                        occupied=lambda x, y: (x, y) in cells,
                        last_rotation=True,
                        top_out_of_bounds_occupied=False,
                    ):
                        continue

                    placed = cells | piece_cells
                    full_rows = {
                        y
                        for y in range(height)
                        if all((x, y) in placed for x in range(width))
                    }
                    lines = len(full_rows)
                    if lines == 0:
                        continue

                    perfect_clear = all(y in full_rows for _, y in placed)
                    best = max(
                        best,
                        attack_for_clear(
                            lines,
                            t_spin=True,
                            perfect_clear=perfect_clear,
                        ),
                    )
        return best

    @staticmethod
    def _can_move_down(
        piece_cells: frozenset[Cell],
        locked_cells: frozenset[Cell],
        height: int,
    ) -> bool:
        for x, y in piece_cells:
            next_y = y + 1
            if next_y >= height or (x, next_y) in locked_cells:
                return False
        return True

    @staticmethod
    @lru_cache(maxsize=4)
    def _t_cells(rotation: int) -> tuple[Cell, ...]:
        return tuple(ActivePiece(PieceType.T, 0, 0, rotation % 4).cells())
