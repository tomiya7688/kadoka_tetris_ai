# PythonのCA bundle監査

Issue #95の最初の対応として、ビルド環境とCIにpip 26.2.2、certifi 2026.10.19を固定します。pip 26.2.2はvendorのcertifiも更新する版です。[pip公式変更履歴](https://pip.pypa.io/en/stable/news/#v26-2-2)を参照してください。

プロジェクトの仮想環境で、次を実行してください。wheelのSHA-256はPyPIの[pip](https://pypi.org/pypi/pip/26.2.2/json)と[certifi](https://pypi.org/pypi/certifi/2026.10.19/json)の公式メタデータで照合しています。TLS検証を無効化するオプションは指定しないでください。

```powershell
python -m pip install --disable-pip-version-check --only-binary=:all: --require-hashes -r requirements-security.txt
python tools/audit_python_trust.py
```

監査はインストール済みの版、`certifi.where()`とpip内蔵certifiが指すPEM実ファイル、SHA-256、CA数、対象G3ルートのDER SHA-256一致をJSONで報告します。CA bundleの中身を更新・削除する処理やネットワーク通信は行いません。古い版、欠落、不正なPEM、対象CA残存、`PIP_TRUSTED_HOST`による検証回避は失敗終了になります。

`PIP_CERT`、`REQUESTS_CA_BUNDLE`、`CURL_CA_BUNDLE`、`SSL_CERT_FILE`を指定した環境では、その実ファイルも監査します。`SSL_CERT_DIR`が指定された場合は各ディレクトリ内のOpenSSL hash名ファイルを監査し、対象rootや不正なファイルを検出すると失敗します。指定値や区切り後の要素が空の場合、または存在しないディレクトリの場合も失敗します。ディレクトリが空でも実チェーンの安全性は未検証です。proxyや認証値は出力しません。未導入の依存関係を自動インストールするのは監査ではなく、上記の明示的な準備コマンドです。

設定ファイル経由の別CAやTLS検証回避を見落とさないため、pip自身の通常モードの設定ローダーも使用します。global・user・siteと`PIP_CONFIG_FILE`、環境変数をpipの読込規則で読み、各セクションの`cert`が指す実bundleを監査します。`trusted-host`が1つでも空白以外の値を持つ場合は失敗します。コマンド別設定や上書きされる設定も保守的に検査するため、特定のpip呼出しで使わない設定が失敗原因になる場合があります。[pipの設定仕様](https://pip.pypa.io/en/stable/topics/configuration/)を確認し、不要な設定は利用者が修正してください。

`PIP_CONFIG_FILE`に`os.devnull`を指定すると、pipと同様に設定ファイルを読みません。認証付きindexやproxy、trusted-hostの値は報告しません。設定読込の失敗は原文を出さず失敗終了になります。コマンドライン引数・requirements内の追加オプション、`--isolated`での別の設定読込は、この通常モード監査では検証しません。

`bundle_status: PASS`は、この範囲のCA一覧と最低版の検査成功を意味します。OSのsystem trust、失効判定、AAA Certificate Servicesへの交差署名を含む実チェーンの拒否、`SSL_CERT_DIR`、uv・sigstore、他のPython環境、配布済み成果物は保証しません。OS全体のtrust storeをこのツールで変更しません。

certifi以外の既定経路に対象CAが残る場合を検出するため、Pythonの`SSLContext.load_default_certs(SERVER_AUTH)`で読み込まれるCAも列挙します。`system_trust`にはCA数・対象fingerprint・既定のCAファイル/ディレクトリ経路を報告します。`loaded_ca_status`は列挙したCAだけの結果です。対象rootを検出した場合は`system_trust.status: FAIL`となり、bundleがPASSでもCLIは終了値1を返します。

列挙したCAに対象がなくても、`system_trust.status`は`UNVERIFIED`のままです。検出は公開ルートのDER SHA-256完全一致だけを対象とし、同じ鍵の再発行証明書や交差署名証明書までは検出しません。ディレクトリのCAは遅延読込されるため、空の列挙も安全の証明にはしません。ネイティブOSやpipのtruststoreによる実チェーン・失効検証は別の経路です。[PythonのCA列挙の仕様](https://docs.python.org/3/library/ssl.html#ssl.SSLContext.get_ca_certs)と[pipのsystem trust仕様](https://pip.pypa.io/en/stable/topics/https-certificates/)を参照してください。終了値0でもこれらの残件は未検証です。監査はTLS接続やkeylogファイルの作成を行いません。

`build.bat`は依存導入前に固定版のbootstrapと監査を行います。Pythonを使う各CIも同じ監査を実行します。Issue #95は、残るOS・他環境・生成済み成果物の検証を終えるまで完了にしません。

対象fingerprintは[公開インシデント資料のroots.json](https://emudhra.we-have-a-problem.com/roots.json)にあるemSign ECC/TLS/CSのG3ルートです。上流が復元したG1・C1・C3ルートは一括禁止しません。

対応するPEM形式は`CERTIFICATE`です。`TRUSTED CERTIFICATE`など別形式を含むファイルは、証明書を黙って監査対象から除外せず失敗終了にします。未完了・重複した証明書境界も失敗になります。
