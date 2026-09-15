import json
import tempfile
import unittest
from pathlib import Path

from tetris.cpu import (
    STANDARD_CPU_CONFIG_FILENAME,
    VisibleBoardWeights,
    ensure_standard_cpu_config,
    load_standard_cpu_config,
)


class StandardCpuConfigTests(unittest.TestCase):
    def test_default_config_is_created_with_current_weights(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            path = ensure_standard_cpu_config(config_dir)
            config = load_standard_cpu_config(config_dir)

            self.assertEqual(path.name, STANDARD_CPU_CONFIG_FILENAME)
            self.assertEqual(config.weights, VisibleBoardWeights())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], 1)
            self.assertEqual(payload["weights"]["holes"], -7.0)

    def test_custom_weights_are_loaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            path = ensure_standard_cpu_config(config_dir)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["weights"]["holes"] = -12.5
            payload["weights"]["bumpiness"] = -0.1
            path.write_text(json.dumps(payload), encoding="utf-8")

            config = load_standard_cpu_config(config_dir)

            self.assertEqual(config.weights.holes, -12.5)
            self.assertEqual(config.weights.bumpiness, -0.1)

    def test_unknown_weight_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            path = ensure_standard_cpu_config(config_dir)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["weights"]["mystery"] = 1.0
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unknown standard CPU weights fields"):
                load_standard_cpu_config(config_dir)

    def test_missing_weight_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            path = ensure_standard_cpu_config(config_dir)
            payload = json.loads(path.read_text(encoding="utf-8"))
            del payload["weights"]["holes"]
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing standard CPU weights fields"):
                load_standard_cpu_config(config_dir)

    def test_non_finite_weight_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            path = ensure_standard_cpu_config(config_dir)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["weights"]["holes"] = float("nan")
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "holes must be finite"):
                load_standard_cpu_config(config_dir)


if __name__ == "__main__":
    unittest.main()
