import tempfile
import unittest
from pathlib import Path

from tetris.main import main
from tetris.runtime_paths import ensure_user_data


class RuntimePathsTests(unittest.TestCase):
    def test_ensure_user_data_creates_expected_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            user_data = ensure_user_data(root)
            self.assertTrue((user_data / "Config").is_dir())
            self.assertTrue((user_data / "Logs").is_dir())

    def test_smoke_mode_initializes_and_exits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = main(["--smoke-test", "--data-root", str(root)])
            self.assertEqual(result, 0)
            self.assertTrue((root / "UserData" / "Config").is_dir())
            self.assertTrue((root / "UserData" / "Logs").is_dir())
            self.assertTrue((root / "UserData" / "Config" / "input.json").is_file())


if __name__ == "__main__":
    unittest.main()
