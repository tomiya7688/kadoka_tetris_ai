from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import format_code


# {
#   責務: [has_formatters: 開発用formatterを使う統合検証の実行可否を判定する]
#   処理: [固定版二つの導入状態を確認する]
#   引数: [なし]
#   戻り値: [両方の固定版が導入済みならTrue]
# }
def has_formatters() -> bool:
    try:
        return version("ruff") == "0.16.7" and version("clang-format") == "21.1.8"
    except PackageNotFoundError:
        return False


# {
#   責務: [FormatCodeTests: 整形対象の境界と書換えなし検査を検証する]
#   フィールド: [なし]
#   処理: [path選別、commit差分取得、実formatterの整形と検査を検証する]
# }
class FormatCodeTests(unittest.TestCase):
    # {
    #   責務: [test_source_selection: 生成物や対象外を除き指定sourceだけを選ぶ]
    #   処理: [一時rootへ必要なsourceを用意し選別結果を比較する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_source_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("answer = 42\n", encoding="utf-8")
            # 短縮pathと同様に、rootの表記だけが正規形と異なる場合も許可する。
            with patch.object(format_code, "ROOT", root / "tools" / ".."):
                self.assertEqual(
                    format_code.source_paths(
                        [
                            "tools/example.py",
                            "tools/example.py",
                            "dist/generated.py",
                            "tools/vendor/example.py",
                            "tools/.cache/example.py",
                            "tools/generated/example.cpp",
                            "tools/__pycache__/example.py",
                            "README.md",
                            "tools/settings.json",
                        ]
                    ),
                    ["tools/example.py"],
                )
                for invalid in [
                    "../outside.py",
                    str(root / "tools/example.py"),
                    "tools/missing.py",
                ]:
                    with self.subTest(path=invalid), self.assertRaises(ValueError):
                        format_code.source_paths([invalid])

    # {
    #   責務: [test_changed_names: 空白と非ASCIIを含むファイル名を維持する]
    #   処理: [NUL区切りのGit応答を模擬し取得結果と安全な引数を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_changed_names(self) -> None:
        with patch.object(
            subprocess,
            "check_output",
            side_effect=[
                b"a" * 40 + b"\n",
                b"b" * 40 + b"\n",
                "tools/space name.py\0core/日本語.cpp\0".encode(),
            ],
        ) as git:
            self.assertEqual(
                format_code.changed_paths("main", "HEAD"),
                [
                    "tools/space name.py",
                    "core/日本語.cpp",
                ],
            )
            self.assertIn("--end-of-options", git.call_args_list[0].args[0])
            self.assertEqual(git.call_args_list[-1].args[0][-1], "--")

    # {
    #   責務: [test_format_and_check: 検査の非書換え、整形成功、対象外保護を実toolで確認する]
    #   処理: [未整形fixtureの失敗を確認し、整形後に両言語の検査成功を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    @unittest.skipUnless(
        has_formatters(), "Install requirements-ci.txt for formatter integration"
    )
    def test_format_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            for config in ["requirements-ci.txt", "pyproject.toml", ".clang-format"]:
                shutil.copyfile(format_code.ROOT / config, root / config)
            originals = {
                "tools/example.py": b"answer=  42\n",
                "tools/example.cpp": b"int main(){return 0;}\n",
            }
            for name, content in originals.items():
                (root / name).write_bytes(content)
            untouched = root / "tools/untouched.py"
            untouched.write_bytes(b"unchanged=  1\n")
            with patch.object(format_code, "ROOT", root):
                for name, content in originals.items():
                    with (
                        self.subTest(path=name),
                        self.assertRaises(subprocess.CalledProcessError),
                    ):
                        format_code.format_sources([name], check=True)
                    self.assertEqual((root / name).read_bytes(), content)
                format_code.format_sources(list(originals), check=False)
                format_code.format_sources(list(originals), check=True)
            self.assertEqual(untouched.read_bytes(), b"unchanged=  1\n")


if __name__ == "__main__":
    unittest.main()
