from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pip._internal.configuration import kinds

from tools import audit_python_trust as audit
from tools import pip_trust_settings as settings


# {
#   責務: [PipTrustSettingsTests: pip設定由来のCAと検証回避の見落としを防ぐ]
#   フィールド: [なし]
#   処理: [実INI読込、設定の監査反映、秘密情報を含むエラーの非表示を検証する]
# }
class PipTrustSettingsTests(unittest.TestCase):
    # {
    #   責務: [test_real_config_loading: pip自身の設定読込と無効化を確認する]
    #   処理: [隔離した実INIのコマンド別設定とPIP_CONFIG_FILEを検証する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_real_config_loading(self) -> None:
        with (
            TemporaryDirectory() as directory,
            patch(
                "pip._internal.configuration.get_configuration_files",
                return_value={kinds.GLOBAL: [], kinds.USER: [], kinds.SITE: []},
            ),
            patch.dict(os.environ, {}, clear=True),
        ):
            config = Path(directory) / "pip.ini"
            config.write_text(
                "[global]\ncert = first.pem\nindex-url = https://private.invalid\n"
                "[install]\ncert = install.pem\ntrusted_host = mirror.invalid\n",
                encoding="utf-8",
            )
            os.environ["PIP_CONFIG_FILE"] = str(config)
            self.assertEqual(
                settings.load_pip_trust_settings(),
                [
                    ("global.cert", "first.pem"),
                    ("install.cert", "install.pem"),
                    ("install.trusted-host", "mirror.invalid"),
                ],
            )
            os.environ["PIP_CERT"] = "environment.pem"
            self.assertEqual(
                settings.load_pip_trust_settings()[-1],
                (":env:.cert", "environment.pem"),
            )
            os.environ["PIP_CONFIG_FILE"] = os.devnull
            self.assertEqual(
                settings.load_pip_trust_settings(), [(":env:.cert", "environment.pem")]
            )
            # 不正な実INIの内容をエラーメッセージへ漏らさない。
            config.write_text("sensitive-setting-value\n", encoding="utf-8")
            os.environ["PIP_CONFIG_FILE"] = str(config)
            with self.assertRaisesRegex(
                ValueError, "^Unable to read pip trust configuration$"
            ):
                settings.load_pip_trust_settings()

    # {
    #   責務: [test_configured_trust_is_audited: 設定由来のCAと検証回避を集計する]
    #   処理: [コマンド別bundleの監査失敗とtrusted-hostの拒否を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_configured_trust_is_audited(self) -> None:
        for certificate_status, hosts, expected in (
            ("PASS", "", "PASS"),
            ("FAIL", "", "FAIL"),
            ("PASS", "private-mirror.invalid", "FAIL"),
        ):
            with (
                self.subTest(certificate_status=certificate_status, hosts=hosts),
                patch.object(audit, "version", side_effect=["26.2.2", "2026.10.19"]),
                patch.object(audit, "import_module"),
                patch.object(
                    audit, "audit_default_trust", return_value={"status": "UNVERIFIED"}
                ),
                patch.object(
                    audit,
                    "load_pip_trust_settings",
                    return_value=[
                        ("install.cert", "config.pem"),
                        ("global.trusted-host", hosts),
                    ],
                ),
                patch.object(
                    audit,
                    "audit_bundle",
                    side_effect=[
                        {"status": "PASS"},
                        {"status": "PASS"},
                        {"status": certificate_status},
                    ],
                ) as bundle,
                patch.dict(os.environ, {}, clear=True),
            ):
                report = audit.audit_environment()
            bundle.assert_any_call(Path("config.pem"))
            self.assertEqual(report["bundle_status"], expected)
            self.assertIn("pip-config:0:install.cert", report["bundles"])
            self.assertNotIn("private-mirror.invalid", json.dumps(report))

    # {
    #   責務: [test_configuration_failure_is_sanitized: 設定読込失敗を安全に報告する]
    #   処理: [認証情報を含む内部例外を固定メッセージへ変換する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_configuration_failure_is_sanitized(self) -> None:
        with patch("pip._internal.configuration.Configuration") as configuration:
            configuration.return_value.load.side_effect = ValueError(
                "sensitive-setting-value"
            )
            with self.assertRaisesRegex(
                ValueError, "^Unable to read pip trust configuration$"
            ):
                settings.load_pip_trust_settings()

    # {
    #   責務: [test_duplicate_settings_and_unknown_schema: 設定の取りこぼしと誤成功を防ぐ]
    #   処理: [別ファイルの同名設定を残し、内部API形状の変化を失敗にする]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_duplicate_settings_and_unknown_schema(self) -> None:
        with patch("pip._internal.configuration.Configuration") as configuration:
            configuration.return_value.items.return_value = [
                ("global.ini", {"global.cert": "first.pem"}),
                ("site.ini", {"global.cert": "second.pem"}),
            ]
            self.assertEqual(
                settings.load_pip_trust_settings(),
                [("global.cert", "first.pem"), ("global.cert", "second.pem")],
            )
            for items in (
                [("global.cert", "unexpected-flat-api")],
                [("config.ini", {"global.cert": None})],
            ):
                configuration.return_value.items.return_value = items
                with self.assertRaises(ValueError):
                    settings.load_pip_trust_settings()


if __name__ == "__main__":
    unittest.main()
