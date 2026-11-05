from __future__ import annotations

import hashlib
import json
import os
import re
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
    #   責務: [test_configured_ca_directories: hash名のCAと無効な経路を検査する]
    #   処理: [複数ディレクトリの対象ファイルと不正指定を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_configured_ca_directories(self) -> None:
        with TemporaryDirectory() as root:
            first = Path(root) / "first"
            second = Path(root) / "second"
            first.mkdir()
            second.mkdir()
            blocked = first / "abcdef01.0"
            clean = second / "12345678.1"
            ignored = second / "other.pem"
            for path in (blocked, clean, ignored):
                path.write_text("fixture", encoding="ascii")
            with patch.object(audit, "audit_bundle") as inspect:
                inspect.side_effect = lambda path, content: {
                    "path": str(path),
                    "status": "FAIL" if path == blocked else "PASS",
                }
                report = audit.audit_configured_ca_directories(
                    os.pathsep.join((str(first), str(second)))
                )
            self.assertEqual([item["status"] for item in report], ["FAIL", "PASS"])
            self.assertEqual(inspect.call_count, 2)
            for value in (str(first) + os.pathsep, str(first / "missing")):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    audit.audit_configured_ca_directories(value)

    # {
    #   責務: [test_hashed_file_rejects_unsafe_entries: 特殊ファイルと巨大ファイルを拒否する]
    #   処理: [上限を超えるファイルと非通常ファイルを検査する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_hashed_file_rejects_unsafe_entries(self) -> None:
        with TemporaryDirectory() as root:
            oversized = Path(root) / "abcdef01.0"
            with oversized.open("wb") as target:
                target.truncate(4 * 1024 * 1024 + 1)
            with self.assertRaises(ValueError):
                audit.read_hashed_ca_file(oversized)
            if hasattr(os, "mkfifo"):
                fifo = Path(root) / "abcdef02.0"
                os.mkfifo(fifo)
                with self.assertRaises(ValueError):
                    audit.read_hashed_ca_file(fifo)

    # {
    #   責務: [test_windows_hung_reader_is_terminated: 開く処理の停止を打ち切る]
    #   処理: [停止する子プロセスを起動し、監査が失敗することを確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    @unittest.skipUnless(os.name == "nt", "Windows subprocess path")
    def test_windows_hung_reader_is_terminated(self) -> None:
        with TemporaryDirectory() as root:
            script = Path(root) / "slow_reader.py"
            started = Path(root) / "started"
            script.write_text(
                "import pathlib, sys, time\n"
                "pathlib.Path(sys.argv[2]).write_text('started')\n"
                "time.sleep(120)\n",
                encoding="utf-8",
            )
            with (
                patch.object(audit, "__file__", str(script)),
                patch.object(audit, "HASHED_CA_READ_TIMEOUT_SECONDS", 45),
            ):
                with self.assertRaisesRegex(ValueError, "Timed out"):
                    audit.read_hashed_ca_file(started)
            self.assertEqual(started.read_text(), "started")

    # {
    #   責務: [test_windows_inherited_pipe_timeout: 孫がパイプを保持しても監査が戻る]
    #   処理: [子孫を作り、タイムアウトと経過時間を検査し、子孫を片付ける]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    @unittest.skipUnless(os.name == "nt", "Windows subprocess path")
    def test_windows_inherited_pipe_timeout(self) -> None:
        import ctypes
        import time
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        with TemporaryDirectory() as root:
            script = Path(root) / "reader_with_child.py"
            handle_file = Path(root) / "handle"
            script.write_text(
                "import ctypes, pathlib, subprocess, sys, time\n"
                "from ctypes import wintypes as w\n"
                "k=ctypes.WinDLL('kernel32',use_last_error=True)\n"
                "k.GetCurrentProcess.restype=w.HANDLE\n"
                "k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]; k.OpenProcess.restype=w.HANDLE\n"
                "k.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,ctypes.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD]; k.DuplicateHandle.restype=w.BOOL\n"
                "k.CloseHandle.argtypes=[w.HANDLE]\n"
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'])\n"
                f"parent=k.OpenProcess(0x40,False,{os.getpid()})\n"
                "assert parent, ctypes.get_last_error()\n"
                "handle=w.HANDLE()\n"
                "assert k.DuplicateHandle(k.GetCurrentProcess(),int(p._handle),parent,ctypes.byref(handle),0x00100001,False,0), ctypes.get_last_error()\n"
                "k.CloseHandle(parent)\n"
                "pathlib.Path(sys.argv[2]).write_text(str(handle.value))\n"
                "time.sleep(120)\n",
                encoding="utf-8",
            )
            handle = None
            started = time.monotonic()
            try:
                with (
                    patch.object(audit, "__file__", str(script)),
                    patch.object(audit, "HASHED_CA_READ_TIMEOUT_SECONDS", 45),
                    self.assertRaisesRegex(ValueError, "Timed out"),
                ):
                    audit.read_hashed_ca_file(handle_file)
                self.assertTrue(
                    handle_file.exists(), "grandchild handle was not received"
                )
                handle = int(handle_file.read_text())
                self.assertLess(time.monotonic() - started, 70)
                self.assertEqual(kernel.WaitForSingleObject(handle, 10000), 0)
            finally:
                if handle is None and handle_file.exists():
                    handle = int(handle_file.read_text())
                if handle:
                    if kernel.WaitForSingleObject(handle, 0) != 0:
                        kernel.TerminateProcess(handle, 1)
                        kernel.WaitForSingleObject(handle, 10000)
                    kernel.CloseHandle(handle)

    # {
    #   責務: [test_windows_job_closes_on_parent_exit: 親終了時に孫を終了する]
    #   処理: [Jobを持つ親を終了し、孫プロセスの終了を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    @unittest.skipUnless(os.name == "nt", "Windows Job Object path")
    def test_windows_job_closes_on_parent_exit(self) -> None:
        import ctypes
        import subprocess
        import sys
        import time
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        worker = (
            "import ctypes,pathlib,subprocess,sys,time; from ctypes import wintypes as w; "
            "sys.stdin.buffer.read(1); k=ctypes.WinDLL('kernel32',use_last_error=True); "
            "k.GetCurrentProcess.restype=w.HANDLE; "
            "k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]; k.OpenProcess.restype=w.HANDLE; "
            "k.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,ctypes.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD]; "
            "k.DuplicateHandle.restype=w.BOOL; k.CloseHandle.argtypes=[w.HANDLE]; "
            "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)']); "
            f"parent=k.OpenProcess(0x40,False,{os.getpid()}); "
            "assert parent,ctypes.get_last_error(); h=w.HANDLE(); "
            "assert k.DuplicateHandle(k.GetCurrentProcess(),int(p._handle),parent,ctypes.byref(h),0x00100001,False,0),ctypes.get_last_error(); "
            "k.CloseHandle(parent); pathlib.Path(sys.argv[1]).write_text(str(h.value)); time.sleep(120)"
        )
        parent = (
            "import sys; from tools.windows_job import run_in_job; "
            "run_in_job([sys.executable,'-I','-S','-c',sys.argv[1],sys.argv[2]],120)"
        )
        with TemporaryDirectory() as root:
            pid_file = Path(root) / "pid"
            process = subprocess.Popen(
                [sys._base_executable, "-c", parent, worker, str(pid_file)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            descendant = None
            try:
                deadline = time.monotonic() + 60
                while (
                    not pid_file.exists()
                    and process.poll() is None
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.1)
                self.assertTrue(pid_file.exists(), "worker failed to start")
                self.assertIsNone(process.poll(), "parent exited before termination")
                descendant = int(pid_file.read_text())
                self.assertTrue(descendant, "grandchild handle not received")
                process.kill()
                process.wait(timeout=10)
                self.assertEqual(kernel.WaitForSingleObject(descendant, 10000), 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                if descendant:
                    if kernel.WaitForSingleObject(descendant, 0) != 0:
                        kernel.TerminateProcess(descendant, 1)
                    kernel.CloseHandle(descendant)

    # {
    #   責務: [test_real_certificate_in_directory: 実PEMから対象証明書を検出する]
    #   処理: [certifi内の証明書を一時ディレクトリへ置きDER fingerprintを照合する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_real_certificate_in_directory(self) -> None:
        import certifi

        bundle = Path(certifi.where()).read_bytes()
        match = re.search(
            rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
            bundle,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        pem = match.group(0)
        der = audit.ssl.PEM_cert_to_DER_cert(pem.decode("ascii"))
        fingerprint = hashlib.sha256(der).hexdigest()
        with TemporaryDirectory() as root:
            (Path(root) / "abcdef01.0").write_bytes(pem)
            with patch.object(audit, "BLOCKED_ROOT_SHA256", {fingerprint}):
                report = audit.audit_configured_ca_directories(root)
            self.assertEqual(report[0]["status"], "FAIL")
            self.assertEqual(report[0]["blocked_roots"], [fingerprint])

    # {
    #   責務: [test_configured_ca_directory_failure: 対象CAの検出で監査を失敗させる]
    #   処理: [bundleが成功でも明示ディレクトリのFAILを終了値に反映する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_configured_ca_directory_failure(self) -> None:
        with (
            patch.object(audit, "version", side_effect=["26.2.2", "2026.10.19"]),
            patch.object(audit, "import_module"),
            patch.object(audit, "audit_bundle", return_value={"status": "PASS"}),
            patch.object(audit, "load_pip_trust_settings", return_value=[]),
            patch.object(
                audit, "audit_default_trust", return_value={"status": "UNVERIFIED"}
            ),
            patch.object(
                audit,
                "audit_configured_ca_directories",
                return_value=[{"status": "FAIL"}],
            ),
            patch.dict(os.environ, {"SSL_CERT_DIR": "configured"}, clear=True),
            patch("builtins.print"),
        ):
            self.assertEqual(audit.main(), 1)

    # {
    #   責務: [test_invalid_configured_directory: 無効な指定をCLIで失敗させる]
    #   処理: [空文字と存在しないディレクトリのJSONと終了値を確認する]
    #   引数: [self: テストインスタンス]
    #   戻り値: [なし]
    # }
    def test_invalid_configured_directory(self) -> None:
        with TemporaryDirectory() as root:
            for directory in ("", str(Path(root) / "missing")):
                with (
                    self.subTest(directory=directory),
                    patch.object(
                        audit, "version", side_effect=["26.2.2", "2026.10.19"]
                    ),
                    patch.object(audit, "import_module"),
                    patch.object(
                        audit, "audit_bundle", return_value={"status": "PASS"}
                    ),
                    patch.object(audit, "load_pip_trust_settings", return_value=[]),
                    patch.dict(os.environ, {"SSL_CERT_DIR": directory}, clear=True),
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
