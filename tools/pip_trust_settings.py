from __future__ import annotations


# {
#   責務: [load_pip_trust_settings: pip自身の設定読込経路からtrust設定だけを取り出す]
#   処理: [通常モードの設定を読み、certとtrusted-hostだけを返す]
#   引数: [なし]
#   戻り値: [設定名と値の組の一覧。読込失敗時はValueError]
# }
def load_pip_trust_settings() -> list[tuple[str, str]]:
    # indexやproxyの認証情報は返さず、エラーの原文も出力しない。
    try:
        from pip._internal.configuration import Configuration

        configuration = Configuration(isolated=False)
        configuration.load()
        # pip 26.2.2はファイル別辞書を返す。同名設定も消さずに残す。
        trust_settings = []
        for _, source_settings in configuration.items():
            if not isinstance(source_settings, dict):
                raise ValueError("Unexpected pip configuration structure")
            for name, setting in source_settings.items():
                if name.rsplit(".", 1)[-1] in {"cert", "trusted-host"}:
                    if not isinstance(setting, str):
                        raise ValueError("Unexpected pip trust value")
                    trust_settings.append((name, setting))
        return trust_settings
    except Exception:
        # pip内部APIの変更や設定の構文エラーでも監査を成功扱いにしない。
        raise ValueError("Unable to read pip trust configuration") from None
