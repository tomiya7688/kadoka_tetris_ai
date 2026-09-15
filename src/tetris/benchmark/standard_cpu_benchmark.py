"""Headless benchmark runner for the built-in standard CPU."""

from time import perf_counter

from tetris.application import InputRouter, TickEngine
from tetris.core import GameState
from tetris.cpu import (
    STANDARD_CPU_IMPLEMENTATION_ID,
    StandardCpuStrategy,
    VisibleCpuController,
    standard_cpu_profile,
)
from tetris.observation import VisiblePlayerObserver

from .board_metrics import VisibleBoardMetrics
from .result import CpuBenchmarkGameResult, CpuBenchmarkReport, CpuProfileSnapshot


class StandardCpuBenchmark:
    """Run reproducible standard-CPU games without opening the GUI."""

    def __init__(
        self,
        level: str,
        max_pieces: int = 100,
        max_ticks_per_piece: int = 120,
    ):
        if not isinstance(max_pieces, int) or isinstance(max_pieces, bool) or max_pieces < 1:
            raise ValueError("max_pieces must be a positive integer")
        if (
            not isinstance(max_ticks_per_piece, int)
            or isinstance(max_ticks_per_piece, bool)
            or max_ticks_per_piece < 1
        ):
            raise ValueError("max_ticks_per_piece must be a positive integer")

        self.profile = standard_cpu_profile(level)
        self.level = level
        self.max_pieces = max_pieces
        self.max_ticks_per_piece = max_ticks_per_piece
        self.observer = VisiblePlayerObserver()

    def run(self, game_count: int = 1, seed: int = 0) -> CpuBenchmarkReport:
        if not isinstance(game_count, int) or isinstance(game_count, bool) or game_count < 1:
            raise ValueError("game_count must be a positive integer")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")

        games = tuple(self._run_game(seed + index) for index in range(game_count))
        return CpuBenchmarkReport(
            level=self.level,
            max_pieces=self.max_pieces,
            profile=CpuProfileSnapshot(
                implementation_id=STANDARD_CPU_IMPLEMENTATION_ID,
                name=self.profile.name,
                search_depth=self.profile.search_depth,
                action_interval_ticks=self.profile.action_interval_ticks,
                lookahead_discount=self.profile.lookahead_discount,
            ),
            games=games,
        )

    def _run_game(self, seed: int) -> CpuBenchmarkGameResult:
        game = GameState(seed=seed)
        engine = TickEngine({0: game})
        router = InputRouter(engine)
        strategy = StandardCpuStrategy(self.profile)
        controller = VisibleCpuController(0, strategy, observer=self.observer)

        placements = 0
        ticks = 0
        decision_calls = 0
        decision_seconds = 0.0
        stack_height_sum = 0
        holes_sum = 0
        bumpiness_sum = 0
        peak_stack_height = 0
        peak_holes = 0
        peak_bumpiness = 0
        final_metrics = VisibleBoardMetrics(0, 0, 0)
        tick_limit = self.max_pieces * self.max_ticks_per_piece

        while placements < self.max_pieces and not game.game_over and ticks < tick_limit:
            decision_started = perf_counter()
            action = controller.choose_action(game)
            decision_seconds += perf_counter() - decision_started
            decision_calls += 1

            hard_drop = action is not None and action.action == "hard_drop"
            if action is not None:
                router.submit(action)
            engine.advance()
            ticks += 1

            if not hard_drop:
                continue

            placements += 1
            observation = self.observer.observe(game)
            final_metrics = VisibleBoardMetrics.from_observation(observation.board)
            stack_height_sum += final_metrics.stack_height
            holes_sum += final_metrics.holes
            bumpiness_sum += final_metrics.bumpiness
            peak_stack_height = max(peak_stack_height, final_metrics.stack_height)
            peak_holes = max(peak_holes, final_metrics.holes)
            peak_bumpiness = max(peak_bumpiness, final_metrics.bumpiness)

        return CpuBenchmarkGameResult(
            level=self.level,
            seed=seed,
            placements=placements,
            lines=game.lines,
            ticks=ticks,
            game_over=game.game_over,
            reached_piece_limit=placements >= self.max_pieces,
            tick_limit_reached=ticks >= tick_limit and placements < self.max_pieces,
            final_stack_height=final_metrics.stack_height,
            final_holes=final_metrics.holes,
            final_bumpiness=final_metrics.bumpiness,
            peak_stack_height=peak_stack_height,
            peak_holes=peak_holes,
            peak_bumpiness=peak_bumpiness,
            average_stack_height=stack_height_sum / max(1, placements),
            average_holes=holes_sum / max(1, placements),
            average_bumpiness=bumpiness_sum / max(1, placements),
            decision_calls=decision_calls,
            decision_seconds=decision_seconds,
        )
