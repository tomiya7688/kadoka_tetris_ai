import unittest
from tetris.adapters import decode_commands,encode_event
class JsonlTests(unittest.TestCase):
 def test_decode_and_encode(self):
  c=list(decode_commands(['{"player":0,"tick":1,"sequence":2,"action":"hard_drop"}']))[0]; self.assertEqual(c.tick,1); self.assertEqual(encode_event({"ok":True}),'{"ok":true}')
 def test_reports_line(self):
  with self.assertRaisesRegex(ValueError,'line 1'): list(decode_commands(['{}','bad']))
if __name__=='__main__': unittest.main()

