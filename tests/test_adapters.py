import unittest
from tetris.adapters import action_for_key
class AdapterTests(unittest.TestCase):
 def test_keyboard_mapping(self):
  self.assertEqual(action_for_key("SPACE"),"hard_drop"); self.assertIsNone(action_for_key("escape"))
if __name__=='__main__': unittest.main()
