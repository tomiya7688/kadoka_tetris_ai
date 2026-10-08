"""Compare all standard CPU levels over an identical seed range."""

from tetris.cpu import VisibleBoardWeights

from .result import CpuBenchmarkComparisonReport
from .standard_cpu_benchmark import StandardCpuBenchmark


STANDARD_CPU_COMPARISON_LEVELS = ("easy", "normal", "hard")


# {
# 責務: [StandardCpuComparison: Easy/Normal/Hardを同じseed条件で比較する]
# フィールド: [max_pieces / max_ticks_per_piece: 共通実行上限, weights: 各levelで共有する評価重み]
# 処理: [各難易度のStandardCpuBenchmarkを実行し、CpuBenchmarkComparisonReportへまとめる]
# }
class StandardCpuComparison:
    """Run Easy, Normal, and Hard on exactly the same reproducible games."""

    # {
    # 責務: [__init__: CPU難易度間で共有する上限と評価重みを設定する]
    # 処理: [runner共通のpiece/tick上限と任意の盤面評価重みを保持する]
    # 引数: [self: 初期化する比較runner, max_pieces: 各ゲームの配置上限, max_ticks_per_piece: 配置ごとのtick上限, weights: 全難易度へ適用する評価重み]
    # 戻り値: なし
    # }
    def __init__(
        self,
        max_pieces: int = 100,
        max_ticks_per_piece: int = 120,
        weights: VisibleBoardWeights | None = None,
    ):
        self.max_pieces = max_pieces
        self.max_ticks_per_piece = max_ticks_per_piece
        self.weights = weights or VisibleBoardWeights()

    # {
    # 責務: [run: Easy/Normal/Hardを同一seed範囲で実行して難易度比較reportを作る]
    # 処理: [各levelへ同じgame_count、seed、上限、評価重みを渡し、結果を一つのcomparison reportへ集約する]
    # 引数: [self: 比較条件, game_count: 各levelの実行ゲーム数, seed: 各levelで共通に使う開始seed]
    # 戻り値: level別CpuBenchmarkReportを持つCpuBenchmarkComparisonReport
    # }
    def run(self, game_count: int = 1, seed: int = 0) -> CpuBenchmarkComparisonReport:
        reports = tuple(
            StandardCpuBenchmark(
                level,
                max_pieces=self.max_pieces,
                max_ticks_per_piece=self.max_ticks_per_piece,
                weights=self.weights,
            ).run(game_count=game_count, seed=seed)
            for level in STANDARD_CPU_COMPARISON_LEVELS
        )
        return CpuBenchmarkComparisonReport(
            seed_start=seed,
            game_count=game_count,
            max_pieces=self.max_pieces,
            reports=reports,
        )
