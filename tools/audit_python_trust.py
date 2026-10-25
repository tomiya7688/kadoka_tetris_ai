from __future__ import annotations

import hashlib
from importlib import import_module
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import ssl
import sys

MINIMUM_VERSIONS = {"pip": (26, 2, 2), "certifi": (2026, 10, 19)}
# 公開資料roots.jsonのemSign G3 root DER SHA-256。AAA交差署名経路は別検証。
BLOCKED_ROOT_SHA256 = {
    "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",
    "7dd78d5f4f13459a83dff9abbba62edbaf6f2d102bf257fd712f4d9f2746ed8d",
    "f2edaaff3d9b701fb4d14c9f285f8c0bad90fc3bcc1fa07d47f4718edaba34a5",
}


# {
#   責務: [blocked_roots: 列挙されたCAのDERから対象rootを検出する]
#   処理: [各証明書のSHA-256を公開資料のfingerprintと照合する]
#   引数: [certificates: SSLContextが返すCAのDER一覧]
#   戻り値: [検出した対象rootのSHA-256一覧]
# }
def blocked_roots(certificates: list[bytes]) -> list[str]:
    fingerprints = {
        hashlib.sha256(certificate).hexdigest() for certificate in certificates
    }
    return sorted(fingerprints & BLOCKED_ROOT_SHA256)


# {
#   責務: [audit_bundle: 実ファイルのCA bundleを読取専用で監査する]
#   処理: [1: 明示したbundleだけをSSLContextへ読み込む 2: CAとhashを報告する]
#   引数: [path: PEM bundleの実ファイル]
#   戻り値: [path、SHA256、CA数、対象CA、PASSまたはFAILを持つ辞書]
# }
def audit_bundle(path: Path) -> dict:
    # system storeを暗黙に混ぜず、このbundleの収録内容だけを検査する。
    bundle = path.read_bytes()
    # PEM外のUTF-8コメントを除き、証明書ブロック自体はASCIIとして厳密に読む。
    labels = re.findall(rb"-----(?:BEGIN|END) ([^\r\n-]+)-----", bundle)
    if any(label != b"CERTIFICATE" for label in labels):
        raise ValueError("Unsupported PEM block type in CA bundle")
    certificates_pem = re.findall(
        rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", bundle, re.DOTALL
    )
    if not certificates_pem:
        raise ValueError("No PEM certificates in CA bundle")
    if any(
        bundle.count(marker) != len(certificates_pem)
        for marker in (b"-----BEGIN CERTIFICATE-----", b"-----END CERTIFICATE-----")
    ):
        raise ValueError("Unbalanced PEM certificate delimiters")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(
        cadata=(b"\n".join(certificates_pem) + b"\n").decode("ascii")
    )
    certificates = context.get_ca_certs(binary_form=True)
    blocked = blocked_roots(certificates)
    return {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "ca_count": len(certificates),
        "blocked_roots": blocked,
        "status": "PASS" if certificates and not blocked else "FAIL",
    }


# {
#   責務: [audit_environment: 現在のPythonが参照するbundleとtool版を監査する]
#   処理: [1: package版を検査する 2: vendorと明示的overrideのbundleを検査する]
#   引数: [なし]
#   戻り値: [bundle監査結果とOS検証の未確認境界を持つ辞書]
# }
def audit_environment() -> dict:
    report = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "packages": {},
        "bundles": {},
    }
    for package, minimum in MINIMUM_VERSIONS.items():
        installed = version(package)
        # pre/dev/local版を最低版クリアと誤判定しない。
        actual = tuple(int(part) for part in installed.split("."))
        report["packages"][package] = {
            "version": installed,
            "status": "PASS" if actual >= minimum else "FAIL",
        }
    for name, module_name in (
        ("certifi", "certifi"),
        ("pip-vendored-certifi", "pip._vendor.certifi"),
    ):
        module = import_module(module_name)
        report["bundles"][name] = audit_bundle(Path(module.where()))
    for setting in (
        "PIP_CERT",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "SSL_CERT_FILE",
    ):
        if os.environ.get(setting):
            report["bundles"][setting] = audit_bundle(Path(os.environ[setting]))
    # OSやSSL_CERT_DIRはbundle監査と同じ保証にはせず、残件として明示する。
    report["system_trust"] = {
        "status": "UNVERIFIED",
        "reason": "OS chain validation/revocation and SSL_CERT_DIR are outside this bundle audit; pip may also use OS trust.",
    }
    report["tls_verification_bypass"] = (
        "FAIL" if os.environ.get("PIP_TRUSTED_HOST") else "PASS"
    )
    checks = [
        entry["status"]
        for category in ("packages", "bundles")
        for entry in report[category].values()
    ]
    report["bundle_status"] = (
        "PASS"
        if all(status == "PASS" for status in checks)
        and report["tls_verification_bypass"] == "PASS"
        else "FAIL"
    )
    return report


# {
#   責務: [main: ネットワークやtrust storeの変更なしで監査結果をJSON出力する]
#   処理: [監査を実行し、不足・異常・対象CA残存を失敗終了として返す]
#   引数: [なし]
#   戻り値: [bundle監査成功時0、失敗時1。OS検証の完了を意味しない]
# }
def main() -> int:
    try:
        report = audit_environment()
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report["bundle_status"] == "PASS" else 1
    except (ImportError, OSError, ValueError, ssl.SSLError) as error:
        print(
            json.dumps(
                {"bundle_status": "FAIL", "reason": str(error)}, ensure_ascii=True
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
