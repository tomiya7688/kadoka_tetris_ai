from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys

if __package__:
    from .audit_python_trust import BLOCKED_ROOT_SHA256, audit_default_trust
else:
    from audit_python_trust import BLOCKED_ROOT_SHA256, audit_default_trust


# {
#   責務: [blocked_pem_certificates: PEM内の対象証明書をDER fingerprintで判別する]
#   処理: [証明書を個別に復号し、対象SHA-256の一覧を返す]
#   引数: [contents: PEMファイルの内容]
#   戻り値: [全証明書数と対象fingerprintの組]
# }
def blocked_pem_certificates(contents: bytes) -> tuple[int, set[str]]:
    blocks = re.findall(
        rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", contents, re.DOTALL
    )
    labels = re.findall(rb"-----(?:BEGIN|END) ([^\r\n-]+)-----", contents)
    if (
        not blocks
        or any(label != b"CERTIFICATE" for label in labels)
        or any(
            contents.count(marker) != len(blocks)
            for marker in (b"-----BEGIN CERTIFICATE-----", b"-----END CERTIFICATE-----")
        )
    ):
        raise ValueError("Unsupported or empty CA certificate file")
    blocked = set()
    for block in blocks:
        der = ssl.PEM_cert_to_DER_cert(block.decode("ascii"))
        fingerprint = hashlib.sha256(der).hexdigest()
        if fingerprint in BLOCKED_ROOT_SHA256:
            blocked.add(fingerprint)
    return len(blocks), blocked


# {
#   責務: [find_blocked_sources: Ubuntu管理下の対象CAファイルを特定する]
#   処理: [crtだけを読み、対象と完全一致する単一証明書ファイルを返す]
#   引数: [directory: CA source directory]
#   戻り値: [対象CAのパス一覧]
# }
def find_blocked_sources(directory: Path) -> list[Path]:
    if directory.is_symlink():
        raise ValueError("Symlink in managed CA source directory")
    if not directory.exists():
        return []
    matches = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlink in managed CA source directory")
        if not path.is_file() or path.suffix != ".crt":
            continue
        count, blocked = blocked_pem_certificates(path.read_bytes())
        if blocked:
            if count != 1:
                raise ValueError(
                    "Blocked CA shares a source file with other certificates"
                )
            matches.append(path)
    return matches


# {
#   責務: [deselect_ubuntu_ca_sources: 対象CAだけをUbuntuの設定から無効化する]
#   処理: [対象の相対パスを照合し、設定内の対象行だけに!を付ける]
#   引数: [config: ca-certificates.conf、root: 管理済みCAルート、paths: 対象パス]
#   戻り値: [設定を変更した場合True。対象が設定にない場合は失敗]
# }
def deselect_ubuntu_ca_sources(config: Path, root: Path, paths: list[Path]) -> bool:
    selected = {path.relative_to(root).as_posix() for path in paths}
    lines = config.read_text(encoding="utf-8").splitlines(keepends=True)
    found = set()
    changed = False
    for index, line in enumerate(lines):
        entry = line.strip()
        name = entry.removeprefix("!")
        if name in selected:
            found.add(name)
            if not entry.startswith("!"):
                lines[index] = "!" + line
                changed = True
    if found != selected:
        raise ValueError("Blocked CA source is not listed in ca-certificates.conf")
    if changed:
        config.write_text("".join(lines), encoding="utf-8")
    return changed


# {
#   責務: [remediate_ubuntu_trust: 使い捨てUbuntu runnerの対象CAを除外する]
#   処理: [対象を特定し、管理設定を更新してCA bundleとhash linkを再生成する]
#   引数: [なし]
#   戻り値: [なし。非管理の対象CAや更新失敗は例外]
# }
def remediate_ubuntu_trust() -> None:
    root = Path("/usr/share/ca-certificates")
    local_root = Path("/usr/local/share/ca-certificates")
    if find_blocked_sources(local_root):
        raise ValueError(
            "Blocked CA in local custom source requires manual remediation"
        )
    matches = find_blocked_sources(root)
    changed = deselect_ubuntu_ca_sources(
        Path("/etc/ca-certificates.conf"), root, matches
    )
    if changed:
        subprocess.run(["update-ca-certificates", "--fresh"], check=True)


WINDOWS_REMEDIATION = r"""
$ErrorActionPreference = 'Stop'
$blocked = $env:KADOKA_BLOCKED_ROOTS -split ','
foreach ($location in @('CurrentUser', 'LocalMachine')) {
  foreach ($name in @('Root', 'CA')) {
    $store = [System.Security.Cryptography.X509Certificates.X509Store]::new($name, $location)
    try {
      $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
      foreach ($certificate in @($store.Certificates)) {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { $fingerprint = ([BitConverter]::ToString($sha.ComputeHash($certificate.RawData))).Replace('-', '').ToLowerInvariant() }
        finally { $sha.Dispose() }
        if ($blocked -contains $fingerprint) {
          $denied = [System.Security.Cryptography.X509Certificates.X509Store]::new('Disallowed', $location)
          try {
            $denied.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
            $denied.Add($certificate)
          } finally { $denied.Close() }
          $store.Remove($certificate)
          Write-Output "Removed and disallowed SHA-256 $fingerprint from $location/$name"
        }
      }
    } finally { $store.Close() }
  }
}
"""


# {
#   責務: [remediate_windows_trust: 使い捨てWindows runnerの対象CAを信頼対象から除外する]
#   処理: [SHA-256完全一致のCAをDisallowedへ追加して元ストアから取り除く]
#   引数: [なし]
#   戻り値: [なし。ストア更新失敗は例外]
# }
def remediate_windows_trust() -> None:
    environment = os.environ.copy()
    environment["KADOKA_BLOCKED_ROOTS"] = ",".join(sorted(BLOCKED_ROOT_SHA256))
    subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_REMEDIATION],
        env=environment,
        check=True,
    )


# {
#   責務: [verify_default_ca_directory: 遅延ロードされる対象CAの残存を検出する]
#   処理: [OpenSSLのhash名ファイルを読み、対象fingerprintがあれば失敗する]
#   引数: [directory: OpenSSL CA directory]
#   戻り値: [なし。読込不能や対象CA残存は例外]
# }
def verify_default_ca_directory(directory: Path) -> None:
    if not directory.is_dir():
        raise ValueError("Configured CA directory does not exist")
    for path in directory.iterdir():
        if re.fullmatch(r"[0-9a-fA-F]{8}\.\d+", path.name):
            count, blocked = blocked_pem_certificates(path.read_bytes())
            if count != 1:
                raise ValueError("Multiple certificates in hashed CA file")
            if blocked:
                raise ValueError("Blocked CA remains in OpenSSL certificate directory")


# {
#   責務: [verify_remediated_trust: 是正後の既定CAと遅延読込経路を再検査する]
#   処理: [既定CAに対象がないこととLinux hash directoryの対象不在を確認する]
#   引数: [なし]
#   戻り値: [なし。対象残存または列挙不可なら例外]
# }
def verify_remediated_trust() -> None:
    report = audit_default_trust()
    if report["loaded_ca_status"] != "PASS":
        raise ValueError("Default CA audit did not pass after remediation")
    if sys.platform.startswith("linux"):
        paths = ssl.get_default_verify_paths()
        configured = os.environ.get("SSL_CERT_DIR")
        directories = (
            configured.split(os.pathsep) if configured else [paths.openssl_capath]
        )
        for directory in directories:
            if directory and (configured or Path(directory).exists()):
                verify_default_ca_directory(Path(directory))


# {
#   責務: [main: GitHub-hosted使い捨てrunnerだけで対象CAを是正する]
#   処理: [環境を検査しOS別処理を実行後、同じ既定CA監査で再確認する]
#   引数: [なし]
#   戻り値: [成功0、対象外環境・更新失敗・対象残存時は失敗終了]
# }
def main() -> int:
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
    ):
        raise RuntimeError("Trust remediation is restricted to GitHub-hosted runners")
    # 独自経路はsudoで環境変数が消えることもあるため、自動是正の対象外にする。
    if os.environ.get("SSL_CERT_DIR") or os.environ.get("SSL_CERT_FILE"):
        raise RuntimeError("Custom OpenSSL CA paths require manual review")
    if sys.platform.startswith("linux"):
        remediate_ubuntu_trust()
    elif sys.platform == "win32":
        remediate_windows_trust()
    else:
        raise RuntimeError("Unsupported hosted runner OS")
    verify_remediated_trust()
    print("Targeted root remediation verified; OS chain/revocation remains unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
