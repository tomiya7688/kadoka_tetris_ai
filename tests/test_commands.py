import unittest
from tetris.core import GameState
from tetris.application import Command,TickEngine
class CommandTests(unittest.TestCase):
 def test_validation_and_tick(self):
  e=TickEngine({0:GameState(1),1:GameState(2)}); e.submit(Command.from_dict({"player":0,"tick":0,"sequence":0,"action":"move_right"})); e.advance(); self.assertEqual(e.tick,1)
  with self.assertRaises(ValueError): e.submit(Command.from_dict({"player":0,"tick":0,"sequence":0,"action":"move_right"}))
 def test_bad_action(self):
  with self.assertRaises(ValueError): Command.from_dict({"player":0,"tick":0,"sequence":0,"action":"teleport"})
if __name__=='__main__': unittest.main()
