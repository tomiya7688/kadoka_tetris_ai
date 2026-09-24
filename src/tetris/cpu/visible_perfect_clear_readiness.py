"""Lightweight visible-only Perfect Clear readiness evaluation."""

from functools import lru_cache

from tetris.core import ActivePiece, PieceType
from tetris.observation import Cell


VISIBLE_PERFECT_CLEAR_READINESS_ID = "visible-perfect-clear-readiness-v1"


class VisiblePerfectClearReadinessEvaluator:
    """Estimate near-term Perfect Clear potential from visible board geometry.

    The evaluator never predicts hidden bag/RNG contents. Instead it asks whether the
    currently visible locked cells could be completed into fully filled bottom rows by
    at most max_completion_pieces generic tetrominoes, without completing a row before
    the final virtual placement.

    This is intentionally a bounded geometric readiness signal, not a promise that the
    actual future piece sequence can complete the Perfect Clear. Once pieces are
    visible, the normal planner remains responsible for evaluating executable moves.
    """

    def __init__(
        self,
        max_completion_pieces: int = 3,
        max_target_rows: int = 4,
    ):
        if (
            not isinstance(max_completion_pieces, int)
            or isinstance(max_completion_pieces, bool)
            or max_completion_pieces < 1
        ):
            raise ValueError("max_completion_pieces must be a positive integer")
        if (
            not isinstance(max_target_rows, int)
            or isinstance(max_target_rows, bool)
            or max_target_rows < 1
        ):
            raise ValueError("max_target_rows must be a positive integer")
        self.max_completion_pieces = max_completion_pieces
        self.max_target_rows = max_target_rows

    @lru_cache(maxsize=4096)
    def score(
        self,
        cells: frozenset[Cell],
        width: int,
        height: int,
    ) -> int:
        """Return a bounded readiness score; fewer virtual pieces score higher."""
        if width < 1 or height < 1 or not cells:
            return 0

        for pieces in range(1, self.max_completion_pieces + 1):
            total_cells = len(cells) + pieces * 4
            if total_cells % width:
                continue

            target_rows = total_cells // width
            if not 1 <= target_rows <= min(self.max_target_rows, height):
                continue

            top = height - target_rows
            if any(
                x < 0 or x >= width or y < top or y >= height
                for x, y in cells
            ):
                continue

            target = frozenset(
                (x, y)
                for y in range(top, height)
                for x in range(width)
            )
            missing = target - cells
            if len(missing) != pieces * 4:
                continue
            if self._can_complete(
                cells,
                missing,
                pieces,
                width,
                top,
                height,
            ):
                return self.max_completion_pieces + 1 - pieces

        return 0

    def _can_complete(
        self,
        initial_cells: frozenset[Cell],
        missing: frozenset[Cell],
        pieces: int,
        width: int,
        top: int,
        height: int,
    ) -> bool:
        shapes = self._tetromino_shapes()

        @lru_cache(maxsize=None)
        def search(remaining: frozenset[Cell], steps: int) -> bool:
            if not remaining:
                return steps == 0
            if steps <= 0 or len(remaining) != steps * 4:
                return False

            for placement in self._candidate_placements(remaining, shapes):
                next_remaining = remaining - placement
                if steps > 1:
                    filled = initial_cells | (missing - next_remaining)
                    if self._has_full_row(filled, width, top, height):
                        continue
                if search(next_remaining, steps - 1):
                    return True
            return False

        return search(missing, pieces)

    @staticmethod
    def _candidate_placements(
        remaining: frozenset[Cell],
        shapes: tuple[tuple[Cell, ...], ...],
    ) -> tuple[frozenset[Cell], ...]:
        placements: set[frozenset[Cell]] = set()
        for anchor_x, anchor_y in remaining:
            for shape in shapes:
                for local_x, local_y in shape:
                    origin_x = anchor_x - local_x
                    origin_y = anchor_y - local_y
                    placement = frozenset(
                        (origin_x + x, origin_y + y)
                        for x, y in shape
                    )
                    if placement.issubset(remaining):
                        placements.add(placement)
        return tuple(placements)

    @staticmethod
    def _has_full_row(
        cells: frozenset[Cell],
        width: int,
        top: int,
        height: int,
    ) -> bool:
        return any(
            all((x, y) in cells for x in range(width))
            for y in range(top, height)
        )

    @staticmethod
    @lru_cache(maxsize=1)
    def _tetromino_shapes() -> tuple[tuple[Cell, ...], ...]:
        shapes = []
        seen = set()
        for piece in PieceType:
            for rotation in range(4):
                raw = tuple(ActivePiece(piece, 0, 0, rotation).cells())
                min_x = min(x for x, _ in raw)
                min_y = min(y for _, y in raw)
                normalized = tuple(
                    sorted((x - min_x, y - min_y) for x, y in raw)
                )
                if normalized in seen:
                    continue
                seen.add(normalized)
                shapes.append(normalized)
        return tuple(shapes)
