import unittest
from tetris.core import Board,PieceType,SevenBag,make_tetromino
class CoreTests(unittest.TestCase):
 def test_bag(self):
  a=SevenBag(12); b=SevenBag(12); self.assertEqual([next(a) for _ in range(7)],[next(b) for _ in range(7)])
 def test_clear(self):
  b=Board(4,1,0); b._cells[0]=[True]*4; self.assertEqual(b.clear_full_rows(),1)
if __name__=='__main__': unittest.main()
