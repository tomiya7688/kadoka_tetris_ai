"""Headless benchmark runner for the built-in standard CPU."""

from time import perf_counter

from tetris.application import InputRouter, TickEngine, attack_for_event
from tetris.core import GameState
from tetris.cpu import (
    STANDARD_CPU_IMPLEMENTATION_ID,
    VISIBLE_BOARD_EVALUATOR_ID,
    StandardCpuStrategy,
    VisibleBoardWeights,
    VisibleCpuController,
    standard_cpu_profile,
)
from tetris.observation import VisiblePlayerObserver

from .board_metrics import VisibleBoardMetrics
from .result import (
    CpuBenchmarkGameResult,
    CpuBenchmarkReport,
    CpuEvaluatorSnapshot,
    CpuProfileSnapshot,
)


# {
# 責務: [StandardCpuBenchmark: 可視情報だけを使う標準CPUの単独ゲームをheadlessで評価する]
# フィールド: [profile / level: CPU難易度設定, max_pieces / max_ticks_per_piece: 実行上限, weights: 評価重み, observer: 可視盤面取得]
# 処理: [seed別のゲーム結果、火力、盤面品質、CPU判断時間を測定する]
# }
class StandardCpuBenchmark:
    """Run reproducible standard-CPU games without opening the GUI."""

    # {
    # 責務: [__init__: 標準CPUベンチマークの難易度と1ゲームあたりの上限を設定する]
    # 処理: [piece/tick上限を検証し、CPU profile、評価重み、可視Observerを保持する]
    # 引数: [self: 初期化するrunner, level: CPU難易度, max_pieces: 最大配置数, max_ticks_per_piece: 1配置あたりのtick上限, weights: 盤面評価重み]
    # 戻り値: なし
    # エラー: piece/tick上限が正の整数でない場合にValueErrorを送出する
    # }
    def __init__(
        self,
        level: str,
        max_pieces: int = 100,
        max_ticks_per_piece: int = 120,
        weights: VisibleBoardWeights | None = None,
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
        self.weights = weights or VisibleBoardWeights()
        self.observer = VisiblePlayerObserver()

    # {
    # 責務: [run: 連続seedの複数ゲームを実行し、条件と結果をreportへまとめる]
    # 処理: [game_countとseedを検証し、seed + indexで各ゲームを実行してCPU設定をsnapshotにする]
    # 引数: [self: runner設定, game_count: 実行ゲーム数, seed: 最初のゲームseed]
    # 戻り値: profile、evaluator、seed別game resultを含むCpuBenchmarkReport
    # エラー: game_countが正の整数でない場合、seedが整数でない場合にValueErrorを送出する
    # }
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
            evaluator=CpuEvaluatorSnapshot(
                evaluator_id=VISIBLE_BOARD_EVALUATOR_ID,
                cleared_lines=self.weights.cleared_lines,
                aggregate_height=self.weights.aggregate_height,
                max_height=self.weights.max_height,
                holes=self.weights.holes,
                covered_hole_cells=self.weights.covered_hole_cells,
                bumpiness=self.weights.bumpiness,
            ),
            games=games,
        )

    # {
    # 責務: [_run_game: 固定seedの1ゲームをheadlessで実行し、成績と盤面品質を計測する]
    # 処理: [AI判断時間とtickを計測し、hard dropごとの攻撃・盤面指標を集計して上限またはgame overで停止する]
    # 引数: [self: runner設定, seed: ゲームを再現する初期seed]
    # 戻り値: placements、lines、attack、board metrics、decision timingを含むCpuBenchmarkGameResult
    # }
    def _run_game(self, seed: int) -> CpuBenchmarkGameResult:
        game = GameState(seed=seed)
        engine = TickEngine({0: game})
        router = InputRouter(engine)
        strategy = StandardCpuStrategy(self.profile, weights=self.weights)
        controller = VisibleCpuController(0, strategy, observer=self.observer)

        placements = 0
        ticks = 0
        decision_calls = 0
        decision_seconds = 0.0
        attack_generated = 0
        t_spins = 0
        perfect_clears = 0
        back_to_back_clears = 0
        max_combo = 0
        stack_height_sum = 0
        holes_sum = 0
        bumpiness_sum = 0
        peak_stack_height = 0
        peak_holes = 0
        peak_bumpiness = 0
        final_metrics = VisibleBoardMetrics(0, 0, 0)
        tick_limit = self.max_pieces * self.max_ticks_per_piece

        # 長時間停止しないよう、配置数と全体tickの両方に上限を設ける。
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

            # 盤面品質と配置数は、ミノがlockされたhard dropの後だけ記録する。
            if not hard_drop:
                continue

            placements += 1
            event = game.last_lock_event
            if event is not None:
                attack_generated += attack_for_event(event)
                t_spins += int(event.t_spin)
                perfect_clears += int(event.perfect_clear)
                back_to_back_clears += int(event.back_to_back)
                max_combo = max(max_combo, event.combo)

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
            attack_generated=attack_generated,
            t_spins=t_spins,
            perfect_clears=perfect_clears,
            back_to_back_clears=back_to_back_clears,
            max_combo=max_combo,
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
