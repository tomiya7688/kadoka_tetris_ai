"""Metrics derived from the same visible board data available to players."""

from dataclasses import dataclass

from tetris.observation import BoardObservation


@dataclass(frozen=True)
class VisibleBoardMetrics:
    """Compact board-quality metrics for benchmark reporting."""

    stack_height: int
    holes: int
    bumpiness: int

    @classmethod
    def from_observation(cls, board: BoardObservation) -> "VisibleBoardMetrics":
        heights: list[int] = []
        holes = 0
        locked = board.locked_cells

        for x in range(board.width):
            occupied_rows = [y for y in range(board.height) if (x, y) in locked]
            if not occupied_rows:
                heights.append(0)
                continue

            top = min(occupied_rows)
            heights.append(board.height - top)
            holes += sum(
                1
                for y in range(top, board.height)
                if (x, y) not in locked
            )

        bumpiness = sum(
            abs(left - right)
            for left, right in zip(heights, heights[1:])
        )
        return cls(
            stack_height=max(heights, default=0),
            holes=holes,
            bumpiness=bumpiness,
        )
