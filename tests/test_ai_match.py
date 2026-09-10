import unittest
from tetris.application import AIMatchRunner
class AIMatchTests(unittest.TestCase):
 def test_runs_deterministically(self):
  a=AIMatchRunner(3,4).run(3); b=AIMatchRunner(3,4).run(3); self.assertEqual([x.defeated for x in a.values()],[x.defeated for x in b.values()])
if __name__=='__main__': unittest.main()
