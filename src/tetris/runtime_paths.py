"""Runtime paths that work in source and frozen distributions."""

import sys
from pathlib import Path


USER_DATA_SUBDIRECTORIES = ("Config", "Logs")


# {
#   責務: [application_root: ソース実行とfrozen配布で共通の基準ディレクトリを返す]
#   処理: [frozen実行なら実行ファイルの配置先を解決し、通常実行なら現在の作業ディレクトリを使う]
#   引数: [なし]
#   戻り値: [UserDataや配布資材の基準となる絶対Path]
# }
def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


# {
#   責務: [ensure_user_data: UserDataと必須サブディレクトリを初期化する]
#   処理: [1: 指定rootまたはapplication_rootを基準に選ぶ 2: UserData/Config/Logsを再利用可能に作成する]
#   引数: [root: UserDataの親にするディレクトリ。省略時はapplication_rootを使う]
#   戻り値: [作成または確認したUserDataディレクトリのPath]
#   副作用: [必要なディレクトリをfilesystemへ作成する]
#   エラー: [ディレクトリを作成できない場合はPath.mkdirのOSErrorを伝える]
# }
def ensure_user_data(root: Path | None = None) -> Path:
    base = root if root is not None else application_root()
    user_data = base / "UserData"
    user_data.mkdir(parents=True, exist_ok=True)
    for name in USER_DATA_SUBDIRECTORIES:
        (user_data / name).mkdir(exist_ok=True)
    return user_data
