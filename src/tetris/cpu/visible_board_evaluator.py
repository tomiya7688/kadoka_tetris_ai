"""Heuristic evaluation using only player-visible board cells."""

from dataclasses import dataclass

from tetris.observation import Cell


@dataclass(frozen=True)
class VisibleBoardWeights:
    cleared_lines: float = 3.0
    aggregate_height: float = -0.35
    max_height: float = -0.45
    holes: float = -7.0
    covered_hole_cells: float = -1.25
    bumpiness: float = -0.25


class VisibleBoardEvaluator:
    """Score a visible board with a mild preference for easier downstacking."""

    def __init__(self, weights: VisibleBoardWeights | None = None):
        self.weights = weights or VisibleBoardWeights()

    def score(
        self,
        cells: frozenset[Cell],
        width: int,
        height: int,
        cleared_lines: int = 0,
    ) -> float:
        heights = self._column_heights(cells, width, height)
        holes, covered_hole_cells = self._hole_features(cells, width, height)
        bumpiness = sum(
            abs(left - right)
            for left, right in zip(heights, heights[1:])
        )
        max_height = max(heights, default=0)

        return (
            cleared_lines * self.weights.cleared_lines
            + sum(heights) * self.weights.aggregate_height
            + max_height * self.weights.max_height
            + holes * self.weights.holes
            + covered_hole_cells * self.weights.covered_hole_cells
            + bumpiness * self.weights.bumpiness
        )

    def _column_heights(
        self,
        cells: frozenset[Cell],
        width: int,
        height: int,
    ) -> tuple[int, ...]:
        heights = []
        for x in range(width):
            occupied_rows = [y for cell_x, y in cells if cell_x == x]
            if not occupied_rows:
                heights.append(0)
                continue
            heights.append(height - min(occupied_rows))
        return tuple(heights)

    def _hole_features(
        self,
        cells: frozenset[Cell],
        width: int,
        height: int,
    ) -> tuple[int, int]:
        holes = 0
        covered_hole_cells = 0
        for x in range(width):
            seen_blocks = 0
            for y in range(height):
                if (x, y) in cells:
                    seen_blocks += 1
                elif seen_blocks:
                    holes += 1
                    covered_hole_cells += seen_blocks
        return holes, covered_hole_cells
