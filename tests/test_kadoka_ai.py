import unittest

from tetris.ai import KadokaAI, KadokaEvaluator, KadokaPreferenceEvaluator
from tetris.core import Board, GameState, PieceType, Tetromino


class KadokaAITests(unittest.TestCase):
    def test_default_speed_multiplier_is_slow(self):
        self.assertEqual(KadokaAI().speed_multiplier, 0.4)

    def test_invalid_speed_multiplier_is_rejected(self):
        with self.assertRaises(ValueError):
            KadokaAI(speed_multiplier=0)

    def test_same_seed_and_board_have_stable_variation(self):
        board = Board()
        evaluator = KadokaEvaluator(seed=17)
        first = evaluator.score(board)
        second = evaluator.score(board)
        self.assertEqual(first, second)

    def test_flat_surface_is_preferred_over_equally_tall_bumpy_surface(self):
        flat = Board()
        bumpy = Board()
        block = Tetromino(PieceType.O, ((0, 0),))

        for x in range(flat.width):
            flat.lock(block, (x, flat.height - 1))

        for x in range(0, bumpy.width, 2):
            bumpy.lock(block, (x, bumpy.height - 1))
            bumpy.lock(block, (x, bumpy.height - 2))

        evaluator = KadokaPreferenceEvaluator()
        self.assertGreater(evaluator.score(flat), evaluator.score(bumpy))

    def test_choose_uses_existing_planner_contract(self):
        state = GameState(seed=4)
        move = KadokaAI(seed=11).choose(state)
        self.assertEqual(move.actions[-1], "hard_drop")


if __name__ == "__main__":
    unittest.main()
