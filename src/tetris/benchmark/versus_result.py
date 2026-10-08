"""Serializable result models for mirrored CPU-versus-CPU benchmarks."""

from dataclasses import dataclass


VERSUS_BENCHMARK_SCHEMA_VERSION = 1


# {
# 責務: [VersusCpuSideResult: 対戦legごとの片側CPUの成果と計測値を保持する]
# フィールド: [competitor / level / player: 競技者・難易度・player識別, placements / lines: 配置数と消去行, outgoing_attack / cancelled_garbage / garbage_received: 攻撃とgarbage収支, t_spins / perfect_clears / max_combo: 戦闘実績, defeated / final_stack_height / final_holes: 終了状態と盤面指標, decision_calls / decision_seconds / mode_plan_counts: AI判断計測]
# 処理: [片側の生データを保持し、to_dictで配置数あたり指標を含む辞書へ変換する]
# }
@dataclass(frozen=True)
class VersusCpuSideResult:
    competitor: str
    level: str
    player: int
    placements: int
    lines: int
    outgoing_attack: int
    cancelled_garbage: int
    garbage_received: int
    t_spins: int
    perfect_clears: int
    max_combo: int
    defeated: bool
    final_stack_height: int
    final_holes: int
    decision_calls: int
    decision_seconds: float
    mode_plan_counts: dict[str, int]

    # {
    # 責務: [to_dict: 片側の対戦結果をJSON互換の辞書へ変換する]
    # 処理: [全計測値を出力し、攻撃効率と配置あたりAI判断時間を丸めて算出する]
    # 引数: [self: 変換する片側結果]
    # 戻り値: 保存・転送できるstr keyを持つ結果辞書
    # 補足: 配置数が0の場合は除算を避け、配置あたり指標を0として出力する
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "competitor": self.competitor,
            "level": self.level,
            "player": self.player,
            "placements": self.placements,
            "lines": self.lines,
            "outgoing_attack": self.outgoing_attack,
            "attack_per_placement": round(
                self.outgoing_attack / max(1, self.placements), 4
            ),
            "cancelled_garbage": self.cancelled_garbage,
            "garbage_received": self.garbage_received,
            "t_spins": self.t_spins,
            "perfect_clears": self.perfect_clears,
            "max_combo": self.max_combo,
            "defeated": self.defeated,
            "final_stack_height": self.final_stack_height,
            "final_holes": self.final_holes,
            "decision_calls": self.decision_calls,
            "decision_seconds": round(self.decision_seconds, 6),
            "decision_ms_per_placement": round(
                self.decision_seconds * 1000.0 / max(1, self.placements), 4
            ),
            "mode_plan_counts": dict(self.mode_plan_counts),
        }


# {
# 責務: [VersusBenchmarkLegResult: 1回の座席配置で行ったCPU対戦の結果を保持する]
# フィールド: [seed / garbage_seed: 盤面とgarbageの再現seed, mirrored: A/Bのplayer番号を交換したか, ticks / stop_reason: 経過量と終了条件, winner: 勝者またはdraw, a / b: 競技者ごとの片側結果]
# 処理: [対戦条件と両者の結果をto_dictで一つのleg辞書へまとめる]
# }
@dataclass(frozen=True)
class VersusBenchmarkLegResult:
    seed: int
    garbage_seed: int
    mirrored: bool
    ticks: int
    stop_reason: str
    winner: str
    a: VersusCpuSideResult
    b: VersusCpuSideResult

    # {
    # 責務: [to_dict: 1legの対戦条件と両競技者の結果を辞書へ変換する]
    # 処理: [seed、座席反転、停止理由、勝者とA/Bそれぞれの詳細結果を直列化する]
    # 引数: [self: 変換する対戦leg]
    # 戻り値: leg単位のJSON互換辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "garbage_seed": self.garbage_seed,
            "mirrored": self.mirrored,
            "ticks": self.ticks,
            "stop_reason": self.stop_reason,
            "winner": self.winner,
            "a": self.a.to_dict(),
            "b": self.b.to_dict(),
        }


# {
# 責務: [StandardCpuVersusBenchmarkReport: 複数seed・反転legの対戦結果を集約して公開する]
# フィールド: [level_a / level_b: 比較するCPU難易度, seed_start / seed_count: 評価seed範囲, max_pieces_per_player: 各ゲームの配置上限, legs: 全対戦legの結果]
# 処理: [競技者ごとの勝敗・攻撃・garbage・AI計測を集計し、schema version付き辞書を生成する]
# }
@dataclass(frozen=True)
class StandardCpuVersusBenchmarkReport:
    level_a: str
    level_b: str
    seed_start: int
    seed_count: int
    max_pieces_per_player: int
    legs: tuple[VersusBenchmarkLegResult, ...]

    # {
    # 責務: [_competitor_summary: 指定競技者の全leg成績を横断集計する]
    # 処理: [勝敗、配置数、攻撃、garbage、消去、特殊実績、AI判断時間、行動mode数を合算する]
    # 引数: [self: 集計対象report, competitor: 集計する競技者名aまたはb]
    # 戻り値: 競技者の難易度と勝敗・合計値・配置あたり指標を持つ辞書
    # 補足: 攻撃効率と判断時間は全leg合算値を配置数で割って丸める
    # }
    def _competitor_summary(self, competitor: str) -> dict[str, object]:
        sides = [getattr(leg, competitor) for leg in self.legs]
        wins = sum(1 for leg in self.legs if leg.winner == competitor)
        losses = sum(
            1
            for leg in self.legs
            if leg.winner not in (competitor, "draw")
        )
        draws = len(self.legs) - wins - losses
        placements = sum(side.placements for side in sides)
        attacks = sum(side.outgoing_attack for side in sides)
        decisions = sum(side.decision_calls for side in sides)
        decision_seconds = sum(side.decision_seconds for side in sides)
        mode_counts = {"neutral": 0, "defense": 0, "pressure": 0}
        for side in sides:
            for mode, count in side.mode_plan_counts.items():
                mode_counts[mode] = mode_counts.get(mode, 0) + count

        return {
            "level": self.level_a if competitor == "a" else self.level_b,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "total_placements": placements,
            "total_lines": sum(side.lines for side in sides),
            "total_attack": attacks,
            "attack_per_placement": round(attacks / max(1, placements), 4),
            "total_cancelled_garbage": sum(
                side.cancelled_garbage for side in sides
            ),
            "total_garbage_received": sum(side.garbage_received for side in sides),
            "t_spins": sum(side.t_spins for side in sides),
            "perfect_clears": sum(side.perfect_clears for side in sides),
            "max_combo": max((side.max_combo for side in sides), default=0),
            "decision_calls": decisions,
            "decision_ms_per_placement": round(
                decision_seconds * 1000.0 / max(1, placements), 4
            ),
            "mode_plan_counts": mode_counts,
        }

    # {
    # 責務: [to_dict: 対戦reportをversion付きJSON互換辞書へ変換する]
    # 処理: [report条件、A/Bの集計値、各seedの全leg詳細を一つのpayloadにまとめる]
    # 引数: [self: 直列化する対戦report]
    # 戻り値: schema version、summary、leg一覧を含む結果辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "versus_benchmark_schema_version": VERSUS_BENCHMARK_SCHEMA_VERSION,
            "mode": "cpu-versus",
            "level_a": self.level_a,
            "level_b": self.level_b,
            "seed_start": self.seed_start,
            "seed_count": self.seed_count,
            "mirrored_legs_per_seed": 2,
            "max_pieces_per_player": self.max_pieces_per_player,
            "summary": {
                "a": self._competitor_summary("a"),
                "b": self._competitor_summary("b"),
            },
            "legs": [leg.to_dict() for leg in self.legs],
        }
