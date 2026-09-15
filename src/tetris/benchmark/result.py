"""Serializable benchmark result models."""

from dataclasses import dataclass


BENCHMARK_SCHEMA_VERSION = 3


@dataclass(frozen=True)
class CpuProfileSnapshot:
    implementation_id: str
    name: str
    search_depth: int
    action_interval_ticks: int
    lookahead_discount: float

    def to_dict(self) -> dict[str, object]:
        return {
            "implementation_id": self.implementation_id,
            "name": self.name,
            "search_depth": self.search_depth,
            "action_interval_ticks": self.action_interval_ticks,
            "lookahead_discount": self.lookahead_discount,
        }


@dataclass(frozen=True)
class CpuEvaluatorSnapshot:
    evaluator_id: str
    cleared_lines: float
    aggregate_height: float
    max_height: float
    holes: float
    covered_hole_cells: float
    bumpiness: float

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
class CpuBenchmarkReport:
    level: str
    max_pieces: int
    profile: CpuProfileSnapshot
    evaluator: CpuEvaluatorSnapshot
    games: tuple[CpuBenchmarkGameResult, ...]

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
class CpuBenchmarkComparisonReport:
    seed_start: int
    game_count: int
    max_pieces: int
    reports: tuple[CpuBenchmarkReport, ...]

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
class CpuWeightSweepCandidateResult:
    label: str
    changed_weight: str | None
    baseline_value: float | None
    candidate_value: float | None
    multiplier: float | None
    report: CpuBenchmarkReport

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
class CpuWeightSweepReport:
    level: str
    seed_start: int
    game_count: int
    max_pieces: int
    step_fraction: float
    candidates: tuple[CpuWeightSweepCandidateResult, ...]

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
