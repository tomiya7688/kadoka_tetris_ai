import unittest

from tetris.adapters import decode_commands, decode_input_action, encode_event


class JsonlTests(unittest.TestCase):
    def test_decode_and_encode_command(self):
        command = list(
            decode_commands(
                ['{"player":0,"tick":1,"sequence":2,"action":"hard_drop"}']
            )
        )[0]
        self.assertEqual(command.tick, 1)
        self.assertEqual(encode_event({"ok": True}), '{"ok":true}')

    def test_reports_command_line(self):
        with self.assertRaisesRegex(ValueError, "line 1"):
            list(decode_commands(["{}", "bad"]))

    def test_decodes_semantic_input_action(self):
        action = decode_input_action('{"player":1,"action":"hold"}')
        self.assertEqual(action.player, 1)
        self.assertEqual(action.action, "hold")

    def test_rejects_internal_or_scheduling_fields_from_input_api(self):
        with self.assertRaisesRegex(ValueError, "unknown input action fields"):
            decode_input_action(
                '{"player":0,"action":"move_left","tick":99,"sequence":5}'
            )


if __name__ == "__main__":
    unittest.main()
