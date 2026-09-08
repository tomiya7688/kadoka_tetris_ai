import unittest
from tetris.core import GameState
from tetris.ai import PlacementPlanner
class PlannerTests(unittest.TestCase):
 def test_returns_legal_action_sequence(self):
  state=GameState(seed=4); move=PlacementPlanner().choose(state); self.assertEqual(move.actions[-1],'hard_drop'); self.assertGreaterEqual(move.rotation,0)
if __name__=='__main__': unittest.main()
