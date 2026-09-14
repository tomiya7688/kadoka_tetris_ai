import json
import tempfile
import unittest
from pathlib import Path

from tetris.input_config import ensure_input_config, load_keyboard_bindings


class InputConfigTests(unittest.TestCase):
    def test_default_config_is_created_for_both_players(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "Config"
            bindings = load_keyboard_bindings(config_dir)

            self.assertTrue((config_dir / "input.json").is_file())
            self.assertEqual(bindings.players, (0, 1))
            self.assertEqual(bindings.action_for_key(0, "SPACE"), "hard_drop")
            self.assertEqual(bindings.action_for_key(1, "A"), "move_left")

    def test_custom_key_is_loaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "Config"
            path = ensure_input_config(config_dir)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["players"]["0"]["hard_drop"] = "x"
            path.write_text(json.dumps(data), encoding="utf-8")

            bindings = load_keyboard_bindings(config_dir)
            self.assertEqual(bindings.action_for_key(0, "x"), "hard_drop")
            self.assertIsNone(bindings.action_for_key(0, "space"))

    def test_unknown_config_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "Config"
            path = ensure_input_config(config_dir)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["unexpected"] = True
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unknown input config fields"):
                load_keyboard_bindings(config_dir)

    def test_shared_key_between_players_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "Config"
            path = ensure_input_config(config_dir)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["players"]["1"]["hard_drop"] = "space"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "shared by players"):
                load_keyboard_bindings(config_dir)


if __name__ == "__main__":
    unittest.main()
