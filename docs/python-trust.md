# PythonのCA bundle監査

Issue #95の最初の対応として、ビルド環境とCIにpip 26.2.2、certifi 2026.10.19を固定します。pip 26.2.2はvendorのcertifiも更新する版です。[pip公式変更履歴](https://pip.pypa.io/en/stable/news/#v26-2-2)を参照してください。

プロジェクトの仮想環境で、次を実行してください。wheelのSHA-256はPyPIの[pip](https://pypi.org/pypi/pip/26.2.2/json)と[certifi](https://pypi.org/pypi/certifi/2026.10.19/json)の公式メタデータで照合しています。TLS検証を無効化するオプションは指定しないでください。

```powershell
python -m pip install --disable-pip-version-check --only-binary=:all: --require-hashes -r requirements-security.txt
python tools/audit_python_trust.py
```

監査はインストール済みの版、`certifi.where()`とpip内蔵certifiが指すPEM実ファイル、SHA-256、CA数、対象G3ルートのDER SHA-256一致をJSONで報告します。CA bundleの中身を更新・削除する処理やネットワーク通信は行いません。古い版、欠落、不正なPEM、対象CA残存、`PIP_TRUSTED_HOST`による検証回避は失敗終了になります。

`PIP_CERT`、`REQUESTS_CA_BUNDLE`、`CURL_CA_BUNDLE`、`SSL_CERT_FILE`を指定した環境では、その実ファイルも監査します。proxyや認証値は出力しません。未導入の依存関係を自動インストールするのは監査ではなく、上記の明示的な準備コマンドです。

`bundle_status: PASS`は、この範囲のCA一覧と最低版の検査成功を意味します。OSのsystem trust、失効判定、AAA Certificate Servicesへの交差署名を含む実チェーンの拒否、`SSL_CERT_DIR`、uv・sigstore、他のPython環境、配布済み成果物は保証しません。pipはOSのtrust storeも利用するため、`system_trust`を`UNVERIFIED`として必ず報告します。OS全体のtrust storeをこのツールで変更しません。

`build.bat`は依存導入前に固定版のbootstrapと監査を行います。Pythonを使う各CIも同じ監査を実行します。Issue #95は、残るOS・他環境・生成済み成果物の検証を終えるまで完了にしません。

対象fingerprintは[公開インシデント資料のroots.json](https://emudhra.we-have-a-problem.com/roots.json)にあるemSign ECC/TLS/CSのG3ルートです。上流が復元したG1・C1・C3ルートは一括禁止しません。

対応するPEM形式は`CERTIFICATE`です。`TRUSTED CERTIFICATE`など別形式を含むファイルは、証明書を黙って監査対象から除外せず失敗終了にします。未完了・重複した証明書境界も失敗になります。
