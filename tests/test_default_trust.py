from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import audit_python_trust as audit


# {
#   責務: [DefaultTrustTests: 既定TLSの対象CA残存と列挙の限界を検証する]
#   フィールド: [なし]
#   処理: [対象root、空CA、例外、CLI終了値、監査時の書込防止を確認する]
# }
class DefaultTrustTests(unittest.TestCase):
    # {
    #   責務: [test_loaded_roots_and_scope: 列挙されたCAの検査をOS全体の保証と区別する]
    #   処理: [対象root残存・安全なCA・空の列挙に対する各statusを確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_loaded_roots_and_scope(self) -> None:
        fingerprint = hashlib.sha256(b"blocked fixture").hexdigest()
        for certificates, loaded_status, system_status in (
            ([b"blocked fixture"], "FAIL", "FAIL"),
            ([b"unaffected fixture"], "PASS", "UNVERIFIED"),
            ([], "UNVERIFIED", "UNVERIFIED"),
        ):
            with (
                self.subTest(certificates=certificates),
                patch.object(audit.ssl, "SSLContext") as context,
                patch.object(audit, "BLOCKED_ROOT_SHA256", {fingerprint}),
            ):
                context.return_value.get_ca_certs.return_value = certificates
                report = audit.audit_default_trust()
                context.assert_called_once_with(audit.ssl.PROTOCOL_TLS_CLIENT)
                context.return_value.load_default_certs.assert_called_once_with(
                    audit.ssl.Purpose.SERVER_AUTH
                )
                context.return_value.get_ca_certs.assert_called_once_with(
                    binary_form=True
                )
            self.assertEqual(report["loaded_ca_status"], loaded_status)
            self.assertEqual(report["status"], system_status)
            self.assertEqual(report["ca_count"], len(certificates))
            self.assertIn("SSL_CERT_DIR", report["reason"])

    # {
    #   責務: [test_cli_rejects_blocked_default_trust: bundle成功だけではCLIを成功にしない]
    #   処理: [既定CAのFAILとUNVERIFIEDをCLI終了値とJSONへ反映する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_cli_rejects_blocked_default_trust(self) -> None:
        for system_status, exit_code in (("FAIL", 1), ("UNVERIFIED", 0)):
            report = {
                "bundle_status": "PASS",
                "system_trust": {"status": system_status},
            }
            with (
                self.subTest(system_status=system_status),
                patch.object(audit, "audit_environment", return_value=report),
                patch("builtins.print") as output,
            ):
                self.assertEqual(audit.main(), exit_code)
                self.assertEqual(json.loads(output.call_args.args[0]), report)

    # {
    #   責務: [test_default_store_load_failure: 既定CAの読込エラーをCLI成功にしない]
    #   処理: [SSL例外を模擬し、既定CA失敗時のCLI終了を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_default_store_load_failure(self) -> None:
        with patch.object(audit.ssl, "SSLContext") as context:
            context.return_value.load_default_certs.side_effect = audit.ssl.SSLError(
                "default store unavailable"
            )
            with self.assertRaises(audit.ssl.SSLError):
                audit.audit_default_trust()
        with (
            patch.object(audit, "version", side_effect=["26.2.2", "2026.10.19"]),
            patch.object(audit, "import_module"),
            patch.object(audit, "audit_bundle", return_value={"status": "PASS"}),
            patch.object(audit, "load_pip_trust_settings", return_value=[]),
            patch.object(
                audit,
                "audit_default_trust",
                side_effect=audit.ssl.SSLError("default store unavailable"),
            ),
            patch.dict(os.environ, {}, clear=True),
            patch("builtins.print") as output,
        ):
            self.assertEqual(audit.main(), 1)
            self.assertEqual(
                json.loads(output.call_args.args[0])["bundle_status"], "FAIL"
            )

    # {
    #   責務: [test_real_context_does_not_write_keylog: 実既定CAの監査がkeylogを作成しない]
    #   処理: [SSLKEYLOGFILE指定下の実監査と未検証境界を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_real_context_does_not_write_keylog(self) -> None:
        with TemporaryDirectory() as directory:
            keylog = Path(directory) / "must-not-create.log"
            with patch.dict(os.environ, {"SSLKEYLOGFILE": str(keylog)}):
                report = audit.audit_default_trust()
            self.assertFalse(keylog.exists())
            self.assertIsInstance(report["ca_count"], int)
            self.assertNotEqual(report["status"], "PASS")
            self.assertIn("openssl_capath", report["default_verify_paths"])


if __name__ == "__main__":
    unittest.main()
