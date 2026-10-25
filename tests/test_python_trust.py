from __future__ import annotations

import json
import hashlib
from pathlib import Path
import ssl
import unittest
from unittest.mock import patch

from tools import audit_python_trust as audit


# {
#   責務: [PythonTrustTests: bundle監査の対象CA検出と失敗終了を検証する]
#   フィールド: [なし]
#   処理: [対象名、欠落・不正版、失敗終了、OS未検証表示を確認する]
# }
class PythonTrustTests(unittest.TestCase):
    # {
    #   責務: [test_blocked_roots: 表示名に依存せず対象DERだけを検出する]
    #   処理: [対象と対象外のDERをfingerprintで照合する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_blocked_roots(self) -> None:
        fingerprint = hashlib.sha256(b"compromised DER fixture").hexdigest()
        with patch.object(audit, "BLOCKED_ROOT_SHA256", {fingerprint}):
            self.assertEqual(
                audit.blocked_roots(
                    [b"compromised DER fixture", b"unaffected emSign G1 DER"]
                ),
                [fingerprint],
            )
            self.assertEqual(audit.blocked_roots([b"unaffected emSign G1 DER"]), [])
            self.assertEqual(audit.blocked_roots([]), [])

    # {
    #   責務: [test_bundle_requires_real_nonempty_ca_data: 欠落や空CAを成功扱いにしない]
    #   処理: [実ファイル欠落とSSLContextがCAを返さない条件を検証する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_bundle_requires_real_nonempty_ca_data(self) -> None:
        with self.assertRaises(OSError):
            audit.audit_bundle(Path(__file__).with_name("missing-bundle.pem"))
        with (
            patch.object(ssl, "SSLContext") as context,
            patch.object(
                Path,
                "read_bytes",
                return_value=b"-----BEGIN CERTIFICATE-----\nZmFrZQ==\n-----END CERTIFICATE-----",
            ),
        ):
            context.return_value.get_ca_certs.return_value = []
            self.assertEqual(audit.audit_bundle(Path(__file__))["status"], "FAIL")
            context.return_value.get_ca_certs.return_value = [b"compromised fixture"]
            with patch.object(
                audit,
                "BLOCKED_ROOT_SHA256",
                {hashlib.sha256(b"compromised fixture").hexdigest()},
            ):
                self.assertEqual(audit.audit_bundle(Path(__file__))["status"], "FAIL")

    # {
    #   責務: [test_environment_records_scope: 版不足とOS未検証を正しく区別する]
    #   処理: [監査依存を模擬して版不足と安全なbundleの結果を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_environment_records_scope(self) -> None:
        with (
            patch.object(audit, "version", side_effect=["26.2.1", "2026.10.19"]),
            patch.object(audit, "import_module"),
            patch.object(audit, "load_pip_trust_settings", return_value=[]),
            patch.object(audit, "audit_bundle", return_value={"status": "PASS"}),
            patch.dict(audit.os.environ, {}, clear=True),
        ):
            report = audit.audit_environment()
        self.assertEqual(report["bundle_status"], "FAIL")
        self.assertEqual(report["packages"]["pip"]["status"], "FAIL")
        self.assertEqual(report["system_trust"]["status"], "UNVERIFIED")

    # {
    #   責務: [test_cli_fails_closed: 依存不足や不正bundleを失敗終了として報告する]
    #   処理: [監査例外と不合格結果に対する終了値・JSONを確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_cli_fails_closed(self) -> None:
        for error in (
            ImportError("missing"),
            ValueError("bad version"),
            ssl.SSLError("bad PEM"),
        ):
            with (
                self.subTest(error=error),
                patch.object(audit, "audit_environment", side_effect=error),
                patch("builtins.print") as output,
            ):
                self.assertEqual(audit.main(), 1)
                self.assertEqual(
                    json.loads(output.call_args.args[0])["bundle_status"], "FAIL"
                )
        with (
            patch.object(
                audit, "audit_environment", return_value={"bundle_status": "FAIL"}
            ),
            patch("builtins.print"),
        ):
            self.assertEqual(audit.main(), 1)

    # {
    #   責務: [test_explicit_overrides_and_bypass: 明示された別bundleと検証回避を見落とさない]
    #   処理: [overrideの参照とPIP_TRUSTED_HOSTによる失敗を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_explicit_overrides_and_bypass(self) -> None:
        with (
            patch.object(
                audit,
                "version",
                side_effect=lambda name: {"pip": "26.2.2", "certifi": "2026.10.19"}[
                    name
                ],
            ),
            patch.object(audit, "import_module"),
            patch.object(audit, "load_pip_trust_settings", return_value=[]),
            patch.object(
                audit, "audit_bundle", return_value={"status": "PASS"}
            ) as bundle,
            patch.dict(
                audit.os.environ,
                {"PIP_CERT": "custom.pem", "PIP_TRUSTED_HOST": "example.invalid"},
                clear=True,
            ),
        ):
            report = audit.audit_environment()
        self.assertIn("PIP_CERT", report["bundles"])
        bundle.assert_any_call(Path("custom.pem"))
        self.assertEqual(report["bundle_status"], "FAIL")

    # {
    #   責務: [test_unicode_comments: 証明書外の日本語コメントで有効bundleを拒否しない]
    #   処理: [実certifi bundleにUTF-8コメントを加え、CAとhashを確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_unicode_comments(self) -> None:
        try:
            import certifi
        except ImportError:
            self.skipTest("Install requirements-security.txt for real PEM integration")
        bundle = "# 日本語のCA管理メモ\n".encode() + Path(certifi.where()).read_bytes()
        with patch.object(Path, "read_bytes", return_value=bundle):
            report = audit.audit_bundle(Path(__file__))
        self.assertEqual(report["status"], "PASS")
        self.assertGreater(report["ca_count"], 0)
        self.assertEqual(report["sha256"], hashlib.sha256(bundle).hexdigest())
        # cafileが扱う別形式を黙って除外し、安全な証明書だけでPASSにしない。
        for label in (b"TRUSTED CERTIFICATE", b"X509 CERTIFICATE", b"X509 CRL"):
            unsupported = (
                b"-----BEGIN "
                + label
                + b"-----\nZmFrZQ==\n-----END "
                + label
                + b"-----\n"
            )
            with (
                self.subTest(label=label),
                patch.object(Path, "read_bytes", return_value=bundle + unsupported),
            ):
                with self.assertRaises(ValueError):
                    audit.audit_bundle(Path(__file__))
        # 有効な証明書の後に壊れたブロックがあっても無視してPASSにしない。
        with patch.object(
            Path,
            "read_bytes",
            return_value=bundle + b"\n-----BEGIN CERTIFICATE-----\ntruncated",
        ):
            with self.assertRaises(ValueError):
                audit.audit_bundle(Path(__file__))


if __name__ == "__main__":
    unittest.main()
