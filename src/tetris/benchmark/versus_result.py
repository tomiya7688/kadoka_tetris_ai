"""Serializable result models for mirrored CPU-versus-CPU benchmarks."""

from dataclasses import dataclass


VERSUS_BENCHMARK_SCHEMA_VERSION = 1


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


@dataclass(frozen=True)
class StandardCpuVersusBenchmarkReport:
    level_a: str
    level_b: str
    seed_start: int
    seed_count: int
    max_pieces_per_player: int
    legs: tuple[VersusBenchmarkLegResult, ...]

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
