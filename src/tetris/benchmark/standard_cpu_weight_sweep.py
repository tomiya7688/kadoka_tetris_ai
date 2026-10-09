"""Semi-automatic same-seed sweep for standard CPU evaluator weights."""

import math
from dataclasses import dataclass, fields, replace

from tetris.cpu import VisibleBoardWeights

from .result import CpuWeightSweepCandidateResult, CpuWeightSweepReport
from .standard_cpu_benchmark import StandardCpuBenchmark


# {
# 責務: [_WeightCandidate: 重みスイープの1候補と、基準からの変更内容を保持する]
# フィールド: [label: 出力用候補名, changed_weight: 変更した評価項目, baseline_value / candidate_value: 変更前後の値, multiplier: 基準値に対する倍率, weights: 候補を実行する評価重み一式]
# }
@dataclass(frozen=True)
class _WeightCandidate:
    label: str
    changed_weight: str | None
    baseline_value: float | None
    candidate_value: float | None
    multiplier: float | None
    weights: VisibleBoardWeights


# {
# 責務: [StandardCpuWeightSweep: 基準重みと一項目ずつ変えた重みを同条件で評価する]
# フィールド: [level: CPU難易度, max_pieces / max_ticks_per_piece: 各ゲームの上限, base_weights: 比較基準の重み, step_fraction: 候補を変化させる割合]
# 処理: [候補ごとに標準CPUベンチマークを実行し、同じseed範囲の比較reportを作る]
# }
class StandardCpuWeightSweep:
    """Evaluate baseline and one-weight perturbations over identical games."""

    # {
    # 責務: [__init__: 重みスイープの難易度、実行上限、基準重み、変化幅を設定する]
    # 処理: [step_fractionを数値かつ有限な0より大きく1以下の範囲に検証し、条件を保持する]
    # 引数: [self: 初期化するsweep, level: CPU難易度, max_pieces: 最大配置数, max_ticks_per_piece: 配置ごとのtick上限, base_weights: 比較基準の評価重み, step_fraction: 基準値に対する変化割合]
    # 戻り値: なし
    # エラー: step_fractionが数値でない、有限でない、または0より大きく1以下でない場合にValueErrorを送出する
    # }
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

    # {
    # 責務: [run: 全重み候補を同じseedと上限で評価してreportへまとめる]
    # 処理: [_candidatesの各重みでStandardCpuBenchmarkを実行し、候補情報と評価結果を集約する]
    # 引数: [self: sweep条件, game_count: 各候補で実行するゲーム数, seed: すべての候補で共有する開始seed]
    # 戻り値: 基準条件、変化幅、候補別詳細reportを持つCpuWeightSweepReport
    # }
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

    # {
    # 責務: [_candidates: 基準候補と評価重みごとの上下候補を作る]
    # 処理: [各重みを一つずつ変化させ、非ゼロ値は倍率、ゼロ値は絶対幅で候補を生成する]
    # 引数: [self: 基準重みと変化幅を保持するsweep]
    # 戻り値: baselineと全評価重みの増減候補を含む不変な候補tuple
    # }
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
                    # 0に倍率を掛けても変化しないため、step_fractionを絶対値の幅として適用する。
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
