"""Character-specific board preferences for the Kadoka AI."""

from collections.abc import Mapping

from tetris.core import Board


DEFAULT_KADOKA_PREFERENCE_WEIGHTS = {
    "lines": 2.4,
    "holes": -0.35,
    "aggregate_height": -0.05,
    "bumpiness": -0.50,
    "flat_pairs": 0.90,
    "max_height": -0.12,
    "left_bias": 0.04,
}


class KadokaPreferenceEvaluator:
    """Score a board using intentionally quirky Kadoka preferences."""

    def __init__(self, weights: Mapping[str, float] | None = None):
        self.weights = dict(DEFAULT_KADOKA_PREFERENCE_WEIGHTS)
        if weights is not None:
            self._validate_weights(weights)
            self.weights.update(weights)

    def score(self, board: Board, cleared_lines: int = 0) -> float:
        heights = self._column_heights(board)
        holes = self._hole_count(board, heights)
        bumpiness = self._bumpiness(heights)
        flat_pairs = self._flat_pair_count(heights)
        max_height = max(heights, default=0)
        left_bias = self._left_bias(heights)

        return (
            self.weights["lines"] * cleared_lines
            + self.weights["holes"] * holes
            + self.weights["aggregate_height"] * sum(heights)
            + self.weights["bumpiness"] * bumpiness
            + self.weights["flat_pairs"] * flat_pairs
            + self.weights["max_height"] * max_height
            + self.weights["left_bias"] * left_bias
        )

    def _validate_weights(self, weights: Mapping[str, float]) -> None:
        unknown = set(weights) - set(self.weights)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"unknown Kadoka preference weights: {names}")

    def _column_heights(self, board: Board) -> tuple[int, ...]:
        heights = []
        for x in range(board.width):
            top = self._column_top(board, x)
            heights.append(board.height - top)
        return tuple(heights)

    def _column_top(self, board: Board, x: int) -> int:
        for y in range(board.height):
            if board.occupied(x, y):
                return y
        return board.height

    def _hole_count(self, board: Board, heights: tuple[int, ...]) -> int:
        holes = 0
        for x, height in enumerate(heights):
            if height == 0:
                continue
            top = board.height - height
            holes += sum(
                1
                for y in range(top, board.height)
                if not board.occupied(x, y)
            )
        return holes

    def _bumpiness(self, heights: tuple[int, ...]) -> int:
        return sum(abs(left - right) for left, right in zip(heights, heights[1:]))

    def _flat_pair_count(self, heights: tuple[int, ...]) -> int:
        return sum(left == right for left, right in zip(heights, heights[1:]))

    def _left_bias(self, heights: tuple[int, ...]) -> int:
        middle = len(heights) // 2
        left = sum(heights[:middle])
        right = sum(heights[-middle:]) if middle else 0
        return left - right
