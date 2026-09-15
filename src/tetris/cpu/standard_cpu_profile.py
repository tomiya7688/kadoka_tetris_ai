"""Difficulty profiles for the built-in visible-only standard CPU."""

from dataclasses import dataclass


STANDARD_CPU_IMPLEMENTATION_ID = "standard-visible-v1"


@dataclass(frozen=True)
class StandardCpuProfile:
    name: str
    search_depth: int
    action_interval_ticks: int
    lookahead_discount: float = 0.35

    def __post_init__(self) -> None:
        if self.search_depth < 1:
            raise ValueError("search_depth must be at least 1")
        if self.action_interval_ticks < 1:
            raise ValueError("action_interval_ticks must be at least 1")
        if not 0.0 <= self.lookahead_discount <= 1.0:
            raise ValueError("lookahead_discount must be between 0 and 1")


STANDARD_CPU_PROFILES = {
    "easy": StandardCpuProfile(
        name="easy",
        search_depth=1,
        action_interval_ticks=6,
    ),
    "normal": StandardCpuProfile(
        name="normal",
        search_depth=2,
        action_interval_ticks=3,
    ),
    "hard": StandardCpuProfile(
        name="hard",
        search_depth=3,
        action_interval_ticks=1,
    ),
}


def standard_cpu_profile(name: str) -> StandardCpuProfile:
    try:
        return STANDARD_CPU_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"unknown standard CPU level: {name}") from exc
