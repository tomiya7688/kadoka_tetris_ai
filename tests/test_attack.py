import unittest
from tetris.application import attack_for_clear,cancel_attack
class AttackTests(unittest.TestCase):
 def test_clear_table_and_combo(self): self.assertEqual(attack_for_clear(4),4); self.assertEqual(attack_for_clear(2,3),3)
 def test_cancel(self): self.assertEqual(cancel_attack(3,1),(2,0)); self.assertEqual(cancel_attack(1,3),(0,2))
if __name__=='__main__': unittest.main()
