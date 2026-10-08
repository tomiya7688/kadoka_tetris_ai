"""Mirrored headless benchmark for visible opponent-aware standard CPUs."""

from time import perf_counter

from tetris.application import InputRouter, VersusSession
from tetris.core import GameState
from tetris.cpu import (
    VersusStandardCpuStrategy,
    VisibleBoardWeights,
    VisibleVersusCpuController,
    standard_cpu_profile,
)
from tetris.observation import VisiblePlayerObserver

from .board_metrics import VisibleBoardMetrics
from .versus_result import (
    StandardCpuVersusBenchmarkReport,
    VersusBenchmarkLegResult,
    VersusCpuSideResult,
)


# {
# 責務: [StandardCpuVersusBenchmark: 同じseedで左右を入れ替えたCPU対戦を実行し、対戦指標を集計する]
# フィールド: [profile_a / profile_b: 難易度別CPU設定, level_a / level_b: 報告用難易度名, max_pieces_per_player / max_ticks_per_piece: 実行上限, weights: 共有評価重み, player_observer: 終了盤面の観測器]
# 処理: [seedごとに通常配置と左右反転配置の2 legを実行してレポートを作る]
# }
class StandardCpuVersusBenchmark:
    """Run two mirrored legs per seed to reduce player-side bias."""

    # {
    # 責務: [__init__: 対戦するCPU難易度とゲーム上限を検証して保持する]
    # 処理: [上限を検証し、難易度profile、評価重み、盤面observerを準備する]
    # 引数: [self: 初期化するrunner, level_a / level_b: 比較するCPU難易度, max_pieces_per_player: 各側の配置上限, max_ticks_per_piece: 配置ごとのtick上限, weights: 両CPUで共有する盤面評価重み]
    # 戻り値: なし
    # エラー: 上限が正の整数でない場合、または難易度名が無効な場合にValueErrorを送出する
    # }
    def __init__(
        self,
        level_a: str,
        level_b: str,
        max_pieces_per_player: int = 100,
        max_ticks_per_piece: int = 120,
        weights: VisibleBoardWeights | None = None,
    ):
        if (
            not isinstance(max_pieces_per_player, int)
            or isinstance(max_pieces_per_player, bool)
            or max_pieces_per_player < 1
        ):
            raise ValueError("max_pieces_per_player must be a positive integer")
        if (
            not isinstance(max_ticks_per_piece, int)
            or isinstance(max_ticks_per_piece, bool)
            or max_ticks_per_piece < 1
        ):
            raise ValueError("max_ticks_per_piece must be a positive integer")

        # Resolve profiles here so invalid level names fail before a run starts.
        self.profile_a = standard_cpu_profile(level_a)
        self.profile_b = standard_cpu_profile(level_b)
        self.level_a = level_a
        self.level_b = level_b
        self.max_pieces_per_player = max_pieces_per_player
        self.max_ticks_per_piece = max_ticks_per_piece
        self.weights = weights or VisibleBoardWeights()
        self.player_observer = VisiblePlayerObserver()

    # {
    # 責務: [run: 連続seedごとに左右を入れ替えた対戦を実行してreportへまとめる]
    # 処理: [game_countとseedを検証し、各seedで通常配置と反転配置のlegを実行する]
    # 引数: [self: runner設定, game_count: 実行するseed数, seed: 最初の対戦seed]
    # 戻り値: 難易度、seed範囲、実行上限、各leg結果を持つStandardCpuVersusBenchmarkReport
    # エラー: game_countが正の整数でない場合、またはseedが整数でない場合にValueErrorを送出する
    # }
    def run(self, game_count: int = 1, seed: int = 0) -> StandardCpuVersusBenchmarkReport:
        if not isinstance(game_count, int) or isinstance(game_count, bool) or game_count < 1:
            raise ValueError("game_count must be a positive integer")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")

        legs = []
        for index in range(game_count):
            match_seed = seed + index
            # 同じseedで座席だけを交換し、プレイヤー番号による有利不利を平均化する。
            legs.append(self._run_leg(match_seed, mirrored=False))
            legs.append(self._run_leg(match_seed, mirrored=True))

        return StandardCpuVersusBenchmarkReport(
            level_a=self.level_a,
            level_b=self.level_b,
            seed_start=seed,
            seed_count=game_count,
            max_pieces_per_player=self.max_pieces_per_player,
            legs=tuple(legs),
        )

    # {
    # 責務: [_run_leg: 固定seedと座席配置で1対戦legを実行し、両者の成績を記録する]
    # 処理: [同seedの2盤面を作り、CPU提案を共通sessionへ送り、game overまたは上限までtickを進める]
    # 引数: [self: runner設定, seed: 盤面とgarbage列を再現するseed, mirrored: A/Bのplayer番号を交換するか]
    # 戻り値: 勝者、停止理由、対戦tick、両CPUの攻撃・受信・盤面・判断時間を持つVersusBenchmarkLegResult
    # }
    def _run_leg(self, seed: int, mirrored: bool) -> VersusBenchmarkLegResult:
        assignments = self._assignments(mirrored)
        games = {0: GameState(seed=seed), 1: GameState(seed=seed)}
        session = VersusSession(games, garbage_seed=seed)
        router = InputRouter(session.engine)

        strategies = {}
        controllers = {}
        for player, (_, level) in assignments.items():
            strategy = VersusStandardCpuStrategy(
                standard_cpu_profile(level),
                weights=self.weights,
            )
            strategies[player] = strategy
            controllers[player] = VisibleVersusCpuController(player, strategy)

        decision_calls = {0: 0, 1: 0}
        decision_seconds = {0: 0.0, 1: 0.0}
        ticks = 0
        tick_limit = self.max_pieces_per_player * self.max_ticks_per_piece

        while ticks < tick_limit:
            if any(game.game_over for game in games.values()):
                break
            if all(
                game.pieces_locked >= self.max_pieces_per_player
                for game in games.values()
            ):
                break

            for player in (0, 1):
                game = games[player]
                if game.game_over or game.pieces_locked >= self.max_pieces_per_player:
                    continue
                # 判断時間にはAIのaction選択だけを含め、session進行時間は含めない。
                started = perf_counter()
                action = controllers[player].choose_action(session)
                decision_seconds[player] += perf_counter() - started
                decision_calls[player] += 1
                if action is not None:
                    router.submit(action)

            session.advance()
            ticks += 1

        stop_reason = self._stop_reason(games, ticks, tick_limit)
        winner_player = self._winner_player(games)
        winner = (
            assignments[winner_player][0]
            if winner_player is not None
            else "draw"
        )

        side_results = {}
        for player, (competitor, level) in assignments.items():
            result = session.results[player]
            observation = self.player_observer.observe(games[player])
            metrics = VisibleBoardMetrics.from_observation(observation.board)
            side_results[competitor] = VersusCpuSideResult(
                competitor=competitor,
                level=level,
                player=player,
                placements=games[player].pieces_locked,
                lines=result.lines_cleared,
                outgoing_attack=result.outgoing_attack,
                cancelled_garbage=result.cancelled_garbage,
                garbage_received=result.garbage_received,
                t_spins=result.t_spins,
                perfect_clears=result.perfect_clears,
                max_combo=result.max_combo,
                defeated=result.defeated,
                final_stack_height=metrics.stack_height,
                final_holes=metrics.holes,
                decision_calls=decision_calls[player],
                decision_seconds=decision_seconds[player],
                mode_plan_counts=dict(strategies[player].mode_plan_counts),
            )

        return VersusBenchmarkLegResult(
            seed=seed,
            garbage_seed=seed,
            mirrored=mirrored,
            ticks=ticks,
            stop_reason=stop_reason,
            winner=winner,
            a=side_results["a"],
            b=side_results["b"],
        )

    # {
    # 責務: [_assignments: mirrored設定に応じた競技者とplayer番号の対応を返す]
    # 処理: [通常時はAをplayer 0、反転時はAをplayer 1へ割り当てる]
    # 引数: [self: 難易度設定を保持するrunner, mirrored: 座席を交換するか]
    # 戻り値: player番号から競技者名と難易度名への対応表
    # }
    def _assignments(self, mirrored: bool) -> dict[int, tuple[str, str]]:
        if mirrored:
            return {0: ("b", self.level_b), 1: ("a", self.level_a)}
        return {0: ("a", self.level_a), 1: ("b", self.level_b)}

    # {
    # 責務: [_stop_reason: 対戦が停止した最初の条件を識別する]
    # 処理: [KO、両者の配置上限、tick上限の順に判定する]
    # 引数: [self: runner設定, games: 両playerの盤面, ticks: 経過tick数, tick_limit: leg全体のtick上限]
    # 戻り値: ko / piece-limit / tick-limit / stopped のいずれか
    # }
    def _stop_reason(self, games, ticks: int, tick_limit: int) -> str:
        if any(game.game_over for game in games.values()):
            return "ko"
        if all(
            game.pieces_locked >= self.max_pieces_per_player
            for game in games.values()
        ):
            return "piece-limit"
        if ticks >= tick_limit:
            return "tick-limit"
        return "stopped"

    # {
    # 責務: [_winner_player: KO結果から勝者のplayer番号を判定する]
    # 処理: [生存者とgame over側が1人ずつの場合だけ生存者を勝者とする]
    # 引数: [games: player番号と盤面の対応表]
    # 戻り値: 勝者のplayer番号。勝敗が確定しない場合はNone
    # }
    @staticmethod
    def _winner_player(games) -> int | None:
        alive = [player for player, game in games.items() if not game.game_over]
        defeated = [player for player, game in games.items() if game.game_over]
        if len(alive) == 1 and len(defeated) == 1:
            return alive[0]
        return None
