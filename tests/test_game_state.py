import unittest
from tetris.core import GameState
class GameStateTests(unittest.TestCase):
 def test_move_rotate_drop_locks(self):
  g=GameState(seed=1); start=g.active.kind; g.move(1); g.rotate(); g.hard_drop(); self.assertNotEqual(list(g.board.cells()),[]); self.assertNotEqual(g.active.kind,start)
 def test_hold_once_per_piece(self):
  g=GameState(seed=1); self.assertTrue(g.hold_piece()); self.assertFalse(g.hold_piece()); g.hard_drop(); self.assertTrue(g.hold_piece())
if __name__=='__main__': unittest.main()
