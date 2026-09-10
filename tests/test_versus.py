import unittest
from tetris.core import GameState
from tetris.application import VersusSession
class VersusTests(unittest.TestCase):
 def test_two_players_and_attack(self):
  s=VersusSession({0:GameState(1),1:GameState(2)}); s.queue_attack(0,3); s.queue_attack(1,1); s.advance(); self.assertEqual(s.results[1].incoming_garbage,2); self.assertEqual(s.results[0].incoming_garbage,0)
 def test_requires_two(self):
  with self.assertRaises(ValueError): VersusSession({0:GameState(1)})
if __name__=='__main__': unittest.main()
