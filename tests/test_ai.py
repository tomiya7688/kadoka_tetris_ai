import unittest
from tetris.core import Board
from tetris.ai import HeuristicEvaluator
class AITests(unittest.TestCase):
 def test_empty_board_scores_zero(self): self.assertEqual(HeuristicEvaluator().score(Board()),0)
 def test_lines_are_rewarded(self): self.assertGreater(HeuristicEvaluator().score(Board(),1),HeuristicEvaluator().score(Board(),0))
if __name__=='__main__': unittest.main()
