from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tetris.adapters import decode_input_action, encode_event
from tetris.adapters.keyboard_bindings import KeyboardBindings
from tetris.application import AIBackendKind, Command, FunctionAIBackend
from tetris.observation.board_observation import BoardObservation
from tetris.observation.player_observation import PlayerObservation


# {
#   責務: [PythonReachabilityTests: 到達不能検査と入力境界の防御を確認する]
#   フィールド: [なし]
#   処理: [検査の検出能力と型注釈外の不正入力に対する防御を検証する]
# }
class PythonReachabilityTests(unittest.TestCase):
    # {
    #   責務: [test_input_guards_remain_reachable: 入力境界の防御が動作することを確認する]
    #   処理: [型注釈と異なる入力に対し各公開入口がValueErrorを返す]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_input_guards_remain_reachable(self) -> None:
        bindings = KeyboardBindings.default()
        board = BoardObservation(10, 20, frozenset(), frozenset())
        cases = (
            ("input", lambda: decode_input_action(None), "input action must be text"),
            ("event", lambda: encode_event(None), "event must be an object"),
            (
                "key",
                lambda: bindings.action_for_key(0, None),
                "key names must be strings",
            ),
            (
                "backend",
                lambda: FunctionAIBackend(AIBackendKind.NATIVE, "test", None),
                "decide must be callable",
            ),
            ("command", lambda: Command.from_dict(None), "command must be an object"),
            (
                "piece",
                lambda: PlayerObservation(board, "invalid", None, ()),
                "current_piece must be PieceType or None",
            ),
        )
        for name, call, message in cases:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, message):
                call()

    # {
    #   責務: [test_checker_rejects_unreachable_statement: 検査が到達不能コードを検出する]
    #   処理: [一時プロジェクトに到達不能なreturnを作り診断と失敗終了を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    @unittest.skipUnless(
        importlib.util.find_spec("pyright"), "pyright is not installed"
    )
    def test_checker_rejects_unreachable_statement(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project_config = Path(__file__).resolve().parents[1] / "pyproject.toml"
            shutil.copyfile(project_config, root / "pyproject.toml")
            for directory_name in ("src", "tests", "tools"):
                source_directory = root / directory_name
                source_directory.mkdir()
                (source_directory / "probe.py").write_text(
                    "def probe():\n    return 1\n    return 2\n", encoding="utf-8"
                )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pyright",
                    "--project",
                    str(root),
                    "--outputjson",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            diagnostic_files = {
                Path(item["file"]).parent.name
                for item in report["generalDiagnostics"]
                if item.get("rule") == "reportUnreachable"
            }
            self.assertEqual(diagnostic_files, {"src", "tests", "tools"})
