"""Compare all standard CPU levels over an identical seed range."""

from tetris.cpu import VisibleBoardWeights

from .result import CpuBenchmarkComparisonReport
from .standard_cpu_benchmark import StandardCpuBenchmark


STANDARD_CPU_COMPARISON_LEVELS = ("easy", "normal", "hard")


class StandardCpuComparison:
    """Run Easy, Normal, and Hard on exactly the same reproducible games."""

    def __init__(
        self,
        max_pieces: int = 100,
        max_ticks_per_piece: int = 120,
        weights: VisibleBoardWeights | None = None,
    ):
        self.max_pieces = max_pieces
        self.max_ticks_per_piece = max_ticks_per_piece
        self.weights = weights or VisibleBoardWeights()

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
