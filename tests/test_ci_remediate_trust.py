from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import ci_remediate_trust as remediation


# {
#   責務: [CiRemediateTrustTests: CI用対象CA除外の境界と失敗処理を確認する]
#   フィールド: [なし]
#   処理: [一時fixture、runner制限、CA設定、遅延読込経路を検証する]
# }
class CiRemediateTrustTests(unittest.TestCase):
    # {
    #   責務: [test_exact_certificate_detection: 対象DERだけを検出する]
    #   処理: [別のDERと不正なPEMを使って対象検出と失敗処理を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_exact_certificate_detection(self) -> None:
        fingerprint = hashlib.sha256(b"blocked fixture").hexdigest()
        blocked = (
            b"-----BEGIN CERTIFICATE-----\n"
            + base64.b64encode(b"blocked fixture")
            + b"\n-----END CERTIFICATE-----\n"
        )
        safe = (
            b"-----BEGIN CERTIFICATE-----\n"
            + base64.b64encode(b"safe fixture")
            + b"\n-----END CERTIFICATE-----\n"
        )
        with patch.object(remediation, "BLOCKED_ROOT_SHA256", {fingerprint}):
            self.assertEqual(
                remediation.blocked_pem_certificates(blocked), (1, {fingerprint})
            )
            self.assertEqual(remediation.blocked_pem_certificates(safe), (1, set()))
            for contents in (
                b"",
                safe + b"-----BEGIN CERTIFICATE-----\ntruncated",
                safe + b"-----BEGIN TRUSTED CERTIFICATE-----\n",
            ):
                with self.subTest(contents=contents), self.assertRaises(ValueError):
                    remediation.blocked_pem_certificates(contents)

    # {
    #   責務: [test_deselect_only_exact_matches: Ubuntu設定の対象行だけを無効化する]
    #   処理: [仮の設定で非対象の保持、既に無効な行、欠落時の失敗を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_deselect_only_exact_matches(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "ca"
            root.mkdir()
            target = root / "target.crt"
            config = Path(directory) / "ca-certificates.conf"
            config.write_text("target.crt\nsafe.crt\n", encoding="utf-8")
            self.assertTrue(
                remediation.deselect_ubuntu_ca_sources(config, root, [target])
            )
            self.assertEqual(
                config.read_text(encoding="utf-8"), "!target.crt\nsafe.crt\n"
            )
            self.assertFalse(
                remediation.deselect_ubuntu_ca_sources(config, root, [target])
            )
            with self.assertRaises(ValueError):
                remediation.deselect_ubuntu_ca_sources(
                    config, root, [root / "missing.crt"]
                )
            self.assertEqual(
                config.read_text(encoding="utf-8"), "!target.crt\nsafe.crt\n"
            )

    # {
    #   責務: [test_find_blocked_source: 別証明書を誤って除外しない]
    #   処理: [実ファイルfixtureで対象だけを返し、混在ファイルを拒否する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_find_blocked_source(self) -> None:
        fingerprint = hashlib.sha256(b"blocked fixture").hexdigest()
        blocked = (
            b"-----BEGIN CERTIFICATE-----\n"
            + base64.b64encode(b"blocked fixture")
            + b"\n-----END CERTIFICATE-----\n"
        )
        safe = (
            b"-----BEGIN CERTIFICATE-----\n"
            + base64.b64encode(b"safe fixture")
            + b"\n-----END CERTIFICATE-----\n"
        )
        with (
            TemporaryDirectory() as directory,
            patch.object(remediation, "BLOCKED_ROOT_SHA256", {fingerprint}),
        ):
            root = Path(directory)
            target = root / "target.crt"
            target.write_bytes(blocked)
            (root / "safe.crt").write_bytes(safe)
            self.assertEqual(remediation.find_blocked_sources(root), [target])
            target.write_bytes(blocked + safe)
            with self.assertRaisesRegex(ValueError, "shares a source file"):
                remediation.find_blocked_sources(root)

    # {
    #   責務: [test_source_directory_symlink_is_rejected: sourceのリンクをたどらない]
    #   処理: [CA source rootのシンボリックリンク判定を模擬して拒否を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_source_directory_symlink_is_rejected(self) -> None:
        with (
            TemporaryDirectory() as directory,
            patch.object(Path, "is_symlink", return_value=True),
        ):
            with self.assertRaisesRegex(ValueError, "Symlink in managed CA"):
                remediation.find_blocked_sources(Path(directory))

    # {
    #   責務: [test_hosted_runner_verifies_after_remediation: 是正後の検査を省略しない]
    #   処理: [GitHub-hosted環境で除外と再検査を順に呼ぶことを確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_hosted_runner_verifies_after_remediation(self) -> None:
        calls = []
        with (
            patch.dict(
                os.environ,
                {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted"},
                clear=True,
            ),
            patch.object(remediation.sys, "platform", "linux"),
            patch.object(
                remediation,
                "remediate_ubuntu_trust",
                side_effect=lambda: calls.append("remediate"),
            ),
            patch.object(
                remediation,
                "verify_remediated_trust",
                side_effect=lambda: calls.append("verify"),
            ),
        ):
            self.assertEqual(remediation.main(), 0)
        self.assertEqual(calls, ["remediate", "verify"])

    # {
    #   責務: [test_hashed_directory_rejects_blocked_ca: 遅延読込先の対象CAを見落とさない]
    #   処理: [hash名fixtureの対象と対象外を照合する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_hashed_directory_rejects_blocked_ca(self) -> None:
        fingerprint = hashlib.sha256(b"blocked fixture").hexdigest()
        blocked = (
            b"-----BEGIN CERTIFICATE-----\n"
            + base64.b64encode(b"blocked fixture")
            + b"\n-----END CERTIFICATE-----\n"
        )
        with (
            TemporaryDirectory() as directory,
            patch.object(remediation, "BLOCKED_ROOT_SHA256", {fingerprint}),
        ):
            root = Path(directory)
            (root / "1234abcd.0").write_bytes(blocked)
            with self.assertRaisesRegex(ValueError, "Blocked CA remains"):
                remediation.verify_default_ca_directory(root)
            (root / "1234abcd.0").write_bytes(
                b"-----BEGIN CERTIFICATE-----\nc2FmZQ==\n-----END CERTIFICATE-----\n"
            )
            remediation.verify_default_ca_directory(root)
            safe = (root / "1234abcd.0").read_bytes()
            (root / "1234abcd.0").write_bytes(safe + safe)
            with self.assertRaisesRegex(ValueError, "Multiple certificates"):
                remediation.verify_default_ca_directory(root)

    # {
    #   責務: [test_hosted_runner_guard: 通常PCやself-hosted runnerのストア変更を防ぐ]
    #   処理: [対象外環境ではOS別更新関数を呼ばず失敗することを確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_hosted_runner_guard(self) -> None:
        for environment in (
            {},
            {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "self-hosted"},
        ):
            with (
                self.subTest(environment=environment),
                patch.dict(os.environ, environment, clear=True),
                patch.object(remediation, "remediate_windows_trust") as windows,
                patch.object(remediation, "remediate_ubuntu_trust") as linux,
            ):
                with self.assertRaises(RuntimeError):
                    remediation.main()
                windows.assert_not_called()
                linux.assert_not_called()

    # {
    #   責務: [test_custom_ca_paths_stop_before_mutation: 独自CA経路を黙って無視しない]
    #   処理: [hosted runnerでもSSL_CERT_FILEとSSL_CERT_DIR指定時に停止する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_custom_ca_paths_stop_before_mutation(self) -> None:
        for setting in ("SSL_CERT_FILE", "SSL_CERT_DIR"):
            with (
                self.subTest(setting=setting),
                patch.dict(
                    os.environ,
                    {
                        "GITHUB_ACTIONS": "true",
                        "RUNNER_ENVIRONMENT": "github-hosted",
                        setting: "custom",
                    },
                    clear=True,
                ),
                patch.object(remediation, "remediate_windows_trust") as windows,
                patch.object(remediation, "remediate_ubuntu_trust") as linux,
            ):
                with self.assertRaisesRegex(RuntimeError, "Custom OpenSSL CA paths"):
                    remediation.main()
                windows.assert_not_called()
                linux.assert_not_called()

    # {
    #   責務: [test_post_remediation_failure_stops_ci: 是正後の対象残存を失敗にする]
    #   処理: [既定CAの失敗・空列挙を拒否する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_post_remediation_failure_stops_ci(self) -> None:
        for status in ("FAIL", "UNVERIFIED"):
            with patch.object(
                remediation,
                "audit_default_trust",
                return_value={"loaded_ca_status": status},
            ):
                with self.assertRaises(ValueError):
                    remediation.verify_remediated_trust()


if __name__ == "__main__":
    unittest.main()
