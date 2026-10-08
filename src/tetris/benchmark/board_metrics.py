"""Metrics derived from the same visible board data available to players."""

from dataclasses import dataclass

from tetris.observation import BoardObservation


@dataclass(frozen=True)
# {
# 責務: [VisibleBoardMetrics: playerに公開される盤面からCPU評価指標を保持する]
# フィールド: [stack_height: 最大列高, holes: 各列の最上段より下にある空セル数, bumpiness: 隣接列高差の合計]
# 処理: [計測結果を不変値としてベンチマーク結果へ渡す]
# }
class VisibleBoardMetrics:
    """Compact board-quality metrics for benchmark reporting."""

    stack_height: int
    holes: int
    bumpiness: int

    @classmethod
    # {
    # 責務: [from_observation: 可視盤面から高さ・穴・凹凸を計算する]
    # 処理: [1: 列ごとの高さと最上段より下の穴を数える 2: 隣接列高差を合計する]
    # 引数: [cls: 生成する指標型, board: player向け盤面Observation]
    # 戻り値: stack_height、holes、bumpinessを持つVisibleBoardMetrics
    # }
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
