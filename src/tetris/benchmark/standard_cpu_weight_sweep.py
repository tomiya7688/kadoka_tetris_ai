"""Semi-automatic same-seed sweep for standard CPU evaluator weights."""

import math
from dataclasses import dataclass, fields, replace

from tetris.cpu import VisibleBoardWeights

from .result import CpuWeightSweepCandidateResult, CpuWeightSweepReport
from .standard_cpu_benchmark import StandardCpuBenchmark


@dataclass(frozen=True)
class _WeightCandidate:
    label: str
    changed_weight: str | None
    baseline_value: float | None
    candidate_value: float | None
    multiplier: float | None
    weights: VisibleBoardWeights


class StandardCpuWeightSweep:
    """Evaluate baseline and one-weight perturbations over identical games."""

    def __init__(
        self,
        level: str,
        max_pieces: int = 100,
        max_ticks_per_piece: int = 120,
        base_weights: VisibleBoardWeights | None = None,
        step_fraction: float = 0.25,
    ):
        if not isinstance(step_fraction, (int, float)) or isinstance(step_fraction, bool):
            raise ValueError("step_fraction must be a number")
        step_fraction = float(step_fraction)
        if not math.isfinite(step_fraction) or not 0.0 < step_fraction <= 1.0:
            raise ValueError("step_fraction must be finite and between 0 and 1")

        self.level = level
        self.max_pieces = max_pieces
        self.max_ticks_per_piece = max_ticks_per_piece
        self.base_weights = base_weights or VisibleBoardWeights()
        self.step_fraction = step_fraction

    def run(self, game_count: int = 1, seed: int = 0) -> CpuWeightSweepReport:
        candidates = tuple(
            CpuWeightSweepCandidateResult(
                label=candidate.label,
                changed_weight=candidate.changed_weight,
                baseline_value=candidate.baseline_value,
                candidate_value=candidate.candidate_value,
                multiplier=candidate.multiplier,
                report=StandardCpuBenchmark(
                    self.level,
                    max_pieces=self.max_pieces,
                    max_ticks_per_piece=self.max_ticks_per_piece,
                    weights=candidate.weights,
                ).run(game_count=game_count, seed=seed),
            )
            for candidate in self._candidates()
        )
        return CpuWeightSweepReport(
            level=self.level,
            seed_start=seed,
            game_count=game_count,
            max_pieces=self.max_pieces,
            step_fraction=self.step_fraction,
            candidates=candidates,
        )

    def _candidates(self) -> tuple[_WeightCandidate, ...]:
        candidates = [
            _WeightCandidate(
                label="baseline",
                changed_weight=None,
                baseline_value=None,
                candidate_value=None,
                multiplier=None,
                weights=self.base_weights,
            )
        ]
        for field in fields(VisibleBoardWeights):
            name = field.name
            baseline = float(getattr(self.base_weights, name))
            for sign, multiplier in (
                (-1.0, 1.0 - self.step_fraction),
                (1.0, 1.0 + self.step_fraction),
            ):
                if baseline == 0.0:
                    candidate_value = sign * self.step_fraction
                    effective_multiplier = None
                    label = f"{name}:{'-step' if sign < 0 else '+step'}"
                else:
                    candidate_value = baseline * multiplier
                    effective_multiplier = multiplier
                    label = f"{name}:{multiplier:g}x"
                candidates.append(
                    _WeightCandidate(
                        label=label,
                        changed_weight=name,
                        baseline_value=baseline,
                        candidate_value=candidate_value,
                        multiplier=effective_multiplier,
                        weights=replace(
                            self.base_weights,
                            **{name: candidate_value},
                        ),
                    )
                )
        return tuple(candidates)
