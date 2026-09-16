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


class StandardCpuVersusBenchmark:
    """Run two mirrored legs per seed to reduce player-side bias."""

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

        self.profile_a = standard_cpu_profile(level_a)
        self.profile_b = standard_cpu_profile(level_b)
        self.level_a = level_a
        self.level_b = level_b
        self.max_pieces_per_player = max_pieces_per_player
        self.max_ticks_per_piece = max_ticks_per_piece
        self.weights = weights or VisibleBoardWeights()
        self.player_observer = VisiblePlayerObserver()

    def run(self, game_count: int = 1, seed: int = 0) -> StandardCpuVersusBenchmarkReport:
        if not isinstance(game_count, int) or isinstance(game_count, bool) or game_count < 1:
            raise ValueError("game_count must be a positive integer")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")

        legs = []
        for index in range(game_count):
            match_seed = seed + index
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
        winner = assignments[winner_player][0] if winner_player is not None else "draw"

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

    def _assignments(self, mirrored: bool) -> dict[int, tuple[str, str]]:
        if mirrored:
            return {0: ("b", self.level_b), 1: ("a", self.level_a)}
        return {0: ("a", self.level_a), 1: ("b", self.level_b)}

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

    @staticmethod
    def _winner_player(games) -> int | None:
        alive = [player for player, game in games.items() if not game.game_over]
        defeated = [player for player, game in games.items() if game.game_over]
        if len(alive) == 1 and len(defeated) == 1:
            return alive[0]
        return None
