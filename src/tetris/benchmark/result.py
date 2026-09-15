"""Serializable benchmark result models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CpuBenchmarkGameResult:
    level: str
    seed: int
    placements: int
    lines: int
    ticks: int
    game_over: bool
    reached_piece_limit: bool
    tick_limit_reached: bool
    final_stack_height: int
    final_holes: int
    peak_stack_height: int
    peak_holes: int
    average_stack_height: float
    average_holes: float
    decision_calls: int
    decision_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "seed": self.seed,
            "placements": self.placements,
            "lines": self.lines,
            "ticks": self.ticks,
            "game_over": self.game_over,
            "reached_piece_limit": self.reached_piece_limit,
            "tick_limit_reached": self.tick_limit_reached,
            "final_stack_height": self.final_stack_height,
            "final_holes": self.final_holes,
            "peak_stack_height": self.peak_stack_height,
            "peak_holes": self.peak_holes,
            "average_stack_height": round(self.average_stack_height, 4),
            "average_holes": round(self.average_holes, 4),
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
    games: tuple[CpuBenchmarkGameResult, ...]

    def to_dict(self) -> dict[str, object]:
        count = len(self.games)
        total_placements = sum(game.placements for game in self.games)
        total_lines = sum(game.lines for game in self.games)
        total_ticks = sum(game.ticks for game in self.games)
        total_decision_seconds = sum(game.decision_seconds for game in self.games)
        total_game_overs = sum(1 for game in self.games if game.game_over)

        return {
            "level": self.level,
            "game_count": count,
            "max_pieces": self.max_pieces,
            "summary": {
                "total_placements": total_placements,
                "total_lines": total_lines,
                "game_overs": total_game_overs,
                "average_placements": round(total_placements / max(1, count), 4),
                "average_lines": round(total_lines / max(1, count), 4),
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
            },
            "games": [game.to_dict() for game in self.games],
        }
