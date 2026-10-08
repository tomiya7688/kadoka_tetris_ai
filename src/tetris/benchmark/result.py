"""Serializable benchmark result models."""

from dataclasses import dataclass


BENCHMARK_SCHEMA_VERSION = 3


@dataclass(frozen=True)
# {
# 責務: [CpuProfileSnapshot: ベンチマークで使ったCPU実装と探索設定を保存する]
# フィールド: [implementation_id: 実装識別子, name: 表示名, search_depth: 探索深度, action_interval_ticks: 行動間隔, lookahead_discount: 先読み割引率]
# 処理: [to_dictで設定をJSON互換の辞書へ変換する]
# }
class CpuProfileSnapshot:
    implementation_id: str
    name: str
    search_depth: int
    action_interval_ticks: int
    lookahead_discount: float

    # {
    # 責務: [to_dict: CPUプロファイルをシリアライズ可能な辞書へ変換する]
    # 処理: [実装識別子と設定値を名前付き項目として返す]
    # 引数: [self: 変換対象のプロファイル]
    # 戻り値: プロファイル設定を含む辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "implementation_id": self.implementation_id,
            "name": self.name,
            "search_depth": self.search_depth,
            "action_interval_ticks": self.action_interval_ticks,
            "lookahead_discount": self.lookahead_discount,
        }


@dataclass(frozen=True)
# {
# 責務: [CpuEvaluatorSnapshot: ベンチマークで使った盤面評価器と全重みを保存する]
# フィールド: [evaluator_id: 評価器識別子, cleared_lines / aggregate_height / max_height / holes / covered_hole_cells / bumpiness: 評価重み]
# 処理: [評価器識別子と重みをJSON互換の辞書へまとめる]
# }
class CpuEvaluatorSnapshot:
    evaluator_id: str
    cleared_lines: float
    aggregate_height: float
    max_height: float
    holes: float
    covered_hole_cells: float
    bumpiness: float

    # {
    # 責務: [to_dict: 評価器の識別子と重みを辞書へ変換する]
    # 処理: [すべての評価重みをweights項目にまとめて返す]
    # 引数: [self: 変換対象の評価器設定]
    # 戻り値: 評価器識別子と重みを含む辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "evaluator_id": self.evaluator_id,
            "weights": {
                "cleared_lines": self.cleared_lines,
                "aggregate_height": self.aggregate_height,
                "max_height": self.max_height,
                "holes": self.holes,
                "covered_hole_cells": self.covered_hole_cells,
                "bumpiness": self.bumpiness,
            },
        }


@dataclass(frozen=True)
# {
# 責務: [CpuBenchmarkGameResult: 1ゲームのCPU行動・火力・盤面・時間計測結果を保持する]
# フィールド: [level / seed: 実行条件, placements / lines / attack_generated: 成績, stack/holes/bumpiness: 盤面指標, decision_calls / decision_seconds: 思考計測]
# 処理: [to_dictで比率と丸め済みの指標を含む結果を出力する]
# }
class CpuBenchmarkGameResult:
    level: str
    seed: int
    placements: int
    lines: int
    attack_generated: int
    t_spins: int
    perfect_clears: int
    back_to_back_clears: int
    max_combo: int
    ticks: int
    game_over: bool
    reached_piece_limit: bool
    tick_limit_reached: bool
    final_stack_height: int
    final_holes: int
    final_bumpiness: int
    peak_stack_height: int
    peak_holes: int
    peak_bumpiness: int
    average_stack_height: float
    average_holes: float
    average_bumpiness: float
    decision_calls: int
    decision_seconds: float

    # {
    # 責務: [to_dict: 1ゲームの生計測値と派生指標を辞書へ変換する]
    # 処理: [placement・line当たりの火力、平均盤面値、思考時間などを算出し、丸めて返す]
    # 引数: [self: 変換対象のゲーム結果]
    # 戻り値: ゲーム条件・計測結果・派生指標を含む辞書
    # 補足: 0除算を避けるため、比率の分母には最低1を使う
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "seed": self.seed,
            "placements": self.placements,
            "lines": self.lines,
            "lines_per_placement": round(self.lines / max(1, self.placements), 4),
            "attack_generated": self.attack_generated,
            "attack_per_placement": round(
                self.attack_generated / max(1, self.placements),
                4,
            ),
            "attack_per_line": round(
                self.attack_generated / max(1, self.lines),
                4,
            ),
            "t_spins": self.t_spins,
            "perfect_clears": self.perfect_clears,
            "back_to_back_clears": self.back_to_back_clears,
            "max_combo": self.max_combo,
            "ticks": self.ticks,
            "game_over": self.game_over,
            "reached_piece_limit": self.reached_piece_limit,
            "tick_limit_reached": self.tick_limit_reached,
            "final_stack_height": self.final_stack_height,
            "final_holes": self.final_holes,
            "final_bumpiness": self.final_bumpiness,
            "peak_stack_height": self.peak_stack_height,
            "peak_holes": self.peak_holes,
            "peak_bumpiness": self.peak_bumpiness,
            "average_stack_height": round(self.average_stack_height, 4),
            "average_holes": round(self.average_holes, 4),
            "average_bumpiness": round(self.average_bumpiness, 4),
            "decision_calls": self.decision_calls,
            "decision_seconds": round(self.decision_seconds, 6),
            "decision_ms_per_placement": round(
                self.decision_seconds * 1000.0 / max(1, self.placements),
                4,
            ),
            "ticks_per_placement": round(
                self.ticks / max(1, self.placements),
                4,
            ),
        }


@dataclass(frozen=True)
# {
# 責務: [CpuBenchmarkReport: 同一CPU設定で実行した複数ゲームの結果と集計条件を保持する]
# フィールド: [level / max_pieces: 実行条件, profile / evaluator: 使用設定, games: seed別結果]
# 処理: [summary_dictで全ゲームを集計し、to_dictでschema versionと各ゲーム結果を出力する]
# }
class CpuBenchmarkReport:
    level: str
    max_pieces: int
    profile: CpuProfileSnapshot
    evaluator: CpuEvaluatorSnapshot
    games: tuple[CpuBenchmarkGameResult, ...]

    # {
    # 責務: [summary_dict: 複数ゲームの成績と計測値を集計する]
    # 処理: [総数・平均・placement当たり比率・peak盤面指標・思考時間を計算する]
    # 引数: [self: 集計対象のレポート]
    # 戻り値: 集計済みベンチマーク指標の辞書
    # 補足: ゲーム数や成績が0の場合も除算できるよう分母を最低1にする
    # }
    def summary_dict(self) -> dict[str, object]:
        count = len(self.games)
        total_placements = sum(game.placements for game in self.games)
        total_lines = sum(game.lines for game in self.games)
        total_attack = sum(game.attack_generated for game in self.games)
        total_ticks = sum(game.ticks for game in self.games)
        total_decision_seconds = sum(game.decision_seconds for game in self.games)
        total_game_overs = sum(1 for game in self.games if game.game_over)

        return {
            "total_placements": total_placements,
            "total_lines": total_lines,
            "total_attack_generated": total_attack,
            "total_t_spins": sum(game.t_spins for game in self.games),
            "total_perfect_clears": sum(game.perfect_clears for game in self.games),
            "total_back_to_back_clears": sum(
                game.back_to_back_clears for game in self.games
            ),
            "max_combo": max((game.max_combo for game in self.games), default=0),
            "game_overs": total_game_overs,
            "average_placements": round(total_placements / max(1, count), 4),
            "average_lines": round(total_lines / max(1, count), 4),
            "lines_per_placement": round(
                total_lines / max(1, total_placements),
                4,
            ),
            "attack_per_placement": round(
                total_attack / max(1, total_placements),
                4,
            ),
            "attack_per_line": round(
                total_attack / max(1, total_lines),
                4,
            ),
            "average_ticks_per_placement": round(
                total_ticks / max(1, total_placements),
                4,
            ),
            "decision_ms_per_placement": round(
                total_decision_seconds * 1000.0 / max(1, total_placements),
                4,
            ),
            "average_peak_stack_height": round(
                sum(game.peak_stack_height for game in self.games)
                / max(1, count),
                4,
            ),
            "average_peak_holes": round(
                sum(game.peak_holes for game in self.games) / max(1, count),
                4,
            ),
            "average_peak_bumpiness": round(
                sum(game.peak_bumpiness for game in self.games) / max(1, count),
                4,
            ),
        }

    # {
    # 責務: [to_dict: 集計・seed別結果・CPU設定をschema version付きで出力する]
    # 処理: [profile、evaluator、summary、gamesをJSON互換形式へ変換する]
    # 引数: [self: 変換対象のレポート]
    # 戻り値: single-level形式のベンチマーク辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
            "mode": "single-level",
            "level": self.level,
            "game_count": len(self.games),
            "max_pieces": self.max_pieces,
            "profile": self.profile.to_dict(),
            "evaluator": self.evaluator.to_dict(),
            "summary": self.summary_dict(),
            "games": [game.to_dict() for game in self.games],
        }


@dataclass(frozen=True)
# {
# 責務: [CpuBenchmarkComparisonReport: 同じseed範囲で比較したCPUレベル別レポートを保持する]
# フィールド: [seed_start / game_count / max_pieces: 共通実行条件, reports: レベル別結果]
# 処理: [各レベルの集計と詳細をcomparison形式へまとめる]
# }
class CpuBenchmarkComparisonReport:
    seed_start: int
    game_count: int
    max_pieces: int
    reports: tuple[CpuBenchmarkReport, ...]

    # {
    # 責務: [to_dict: CPUレベルごとの比較結果をschema version付き辞書へ変換する]
    # 処理: [評価器、レベル別summary、詳細reportを名前付きmapにまとめる]
    # 引数: [self: 変換対象の比較結果]
    # 戻り値: comparison形式のベンチマーク辞書
    # 補足: レポートが空ならevaluatorをNoneとして出力する
    # }
    def to_dict(self) -> dict[str, object]:
        evaluator = self.reports[0].evaluator.to_dict() if self.reports else None
        return {
            "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
            "mode": "comparison",
            "seed_start": self.seed_start,
            "game_count": self.game_count,
            "max_pieces": self.max_pieces,
            "evaluator": evaluator,
            "summary_by_level": {
                report.level: report.summary_dict() for report in self.reports
            },
            "levels": {
                report.level: report.to_dict() for report in self.reports
            },
        }


@dataclass(frozen=True)
# {
# 責務: [CpuWeightSweepCandidateResult: 重み候補の変更内容と対応するCPU評価結果を保持する]
# フィールド: [label: 候補名, changed_weight: 変更重み, baseline_value / candidate_value / multiplier: 変更値, report: 候補のゲーム結果]
# 処理: [to_dictで変更条件とベンチマークreportをまとめる]
# }
class CpuWeightSweepCandidateResult:
    label: str
    changed_weight: str | None
    baseline_value: float | None
    candidate_value: float | None
    multiplier: float | None
    report: CpuBenchmarkReport

    # {
    # 責務: [to_dict: 重み候補の条件と評価結果を辞書へ変換する]
    # 処理: [候補メタデータとreportのJSON互換表現を返す]
    # 引数: [self: 変換対象の候補結果]
    # 戻り値: 候補条件と評価結果を含む辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "changed_weight": self.changed_weight,
            "baseline_value": self.baseline_value,
            "candidate_value": self.candidate_value,
            "multiplier": self.multiplier,
            "report": self.report.to_dict(),
        }


@dataclass(frozen=True)
# {
# 責務: [CpuWeightSweepReport: 同一条件で評価した重み候補群と基準設定を保持する]
# フィールド: [level / seed_start / game_count / max_pieces / step_fraction: 共通条件, candidates: 候補別結果]
# 処理: [候補ごとのsummaryと詳細をweight-sweep形式へまとめる]
# }
class CpuWeightSweepReport:
    level: str
    seed_start: int
    game_count: int
    max_pieces: int
    step_fraction: float
    candidates: tuple[CpuWeightSweepCandidateResult, ...]

    # {
    # 責務: [to_dict: 重み候補ごとの比較結果をschema version付き辞書へ変換する]
    # 処理: [共通条件、候補数、候補別summary、候補詳細を出力する]
    # 引数: [self: 変換対象のweight sweep report]
    # 戻り値: weight-sweep形式のベンチマーク辞書
    # }
    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
            "mode": "weight-sweep",
            "level": self.level,
            "seed_start": self.seed_start,
            "game_count": self.game_count,
            "max_pieces": self.max_pieces,
            "step_fraction": self.step_fraction,
            "candidate_count": len(self.candidates),
            "summary_by_candidate": {
                candidate.label: candidate.report.summary_dict()
                for candidate in self.candidates
            },
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }
