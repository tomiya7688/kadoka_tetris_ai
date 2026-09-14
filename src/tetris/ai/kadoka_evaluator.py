"""Composite scoring for the Kadoka character AI."""

import random
import zlib

from tetris.core import Board

from .heuristic import HeuristicEvaluator
from .kadoka_preference import KadokaPreferenceEvaluator


class KadokaEvaluator:
    """Combine minimum sensible play with Kadoka-specific preferences."""

    def __init__(
        self,
        basic_evaluator: HeuristicEvaluator | None = None,
        preference_evaluator: KadokaPreferenceEvaluator | None = None,
        basic_weight: float = 0.35,
        variation: float = 0.20,
        seed: int = 0,
    ):
        if basic_weight < 0:
            raise ValueError("basic_weight must be non-negative")
        if variation < 0:
            raise ValueError("variation must be non-negative")

        self.basic_evaluator = basic_evaluator or HeuristicEvaluator()
        self.preference_evaluator = preference_evaluator or KadokaPreferenceEvaluator()
        self.basic_weight = basic_weight
        self.variation = variation
        self.seed = seed

    def score(self, board: Board, cleared_lines: int = 0) -> float:
        basic_score = self.basic_evaluator.score(board, cleared_lines)
        preference_score = self.preference_evaluator.score(board, cleared_lines)
        variation_score = self._variation_score(board, cleared_lines)
        return self.basic_weight * basic_score + preference_score + variation_score

    def _variation_score(self, board: Board, cleared_lines: int) -> float:
        if self.variation == 0:
            return 0.0
        randomizer = random.Random(self._board_seed(board, cleared_lines))
        return randomizer.uniform(-self.variation, self.variation)

    def _board_seed(self, board: Board, cleared_lines: int) -> int:
        data = bytearray()
        for y in range(board.height):
            for x in range(board.width):
                data.append(1 if board.occupied(x, y) else 0)
        data.extend(cleared_lines.to_bytes(2, "little", signed=False))
        return zlib.crc32(data, self.seed & 0xFFFFFFFF)
