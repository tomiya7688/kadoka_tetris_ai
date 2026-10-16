"""Persistent keyboard input configuration stored under UserData/Config."""

import json
from pathlib import Path

from tetris.adapters.keyboard_bindings import DEFAULT_ACTION_KEYS, KeyboardBindings


INPUT_CONFIG_FILENAME = "input.json"
INPUT_CONFIG_VERSION = 1
REQUIRED_PLAYERS = frozenset({0, 1})


# {
#   責務: [load_keyboard_bindings: UserDataの入力設定を読み込み検証済みbindingへ変換する]
#   処理: [1: 設定ファイルを用意する 2: JSONを読む 3: player別bindingと設定versionを検証する]
#   引数: [config_dir: input.jsonを置くConfigディレクトリ]
#   戻り値: [player 0/1の入力割当を持つKeyboardBindings]
#   エラー: [設定の読み書きまたは形式が不正な場合はValueErrorを伝える]
# }
def load_keyboard_bindings(config_dir: Path) -> KeyboardBindings:
    path = ensure_input_config(config_dir)
    data = _read_json(path)
    return _parse_bindings(data)


# {
#   責務: [ensure_input_config: Configディレクトリと初期input.jsonを用意する]
#   処理: [1: Configディレクトリを再利用可能に作る 2: input.jsonがなければ標準割当で新規作成する]
#   引数: [config_dir: input.jsonの保存先ディレクトリ]
#   戻り値: [読み込みまたは初期化するinput.jsonのPath]
#   副作用: [必要なディレクトリと初期設定ファイルをfilesystemへ作成する]
#   エラー: [ディレクトリ作成時のOSErrorを伝える]
# }
def ensure_input_config(config_dir: Path) -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / INPUT_CONFIG_FILENAME
    if not path.exists():
        _write_default_config(path)
    return path


# {
#   責務: [_read_json: UTF-8の設定ファイルをJSON値として読み込む]
#   処理: [ファイル内容をUTF-8で読み、JSON decoderでPython値へ変換する]
#   引数: [path: 読み込むinput.jsonのPath]
#   戻り値: [JSON documentのroot value]
#   エラー: [JSON形式不正または読み込み失敗を原因付きValueErrorとして伝える]
# }
def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input config JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"failed to read input config: {exc}") from exc


# {
#   責務: [_parse_bindings: JSON値のschemaとplayer別key割当を検証する]
#   処理: [1: rootとfield集合を検証する 2: versionを確認する 3: player idとbinding objectを解析する 4: player 0/1を持つKeyboardBindingsを作る]
#   引数: [data: _read_jsonが返した未検証JSON値]
#   戻り値: [検証済みplayer別割当を持つKeyboardBindings]
#   エラー: [schema、version、player、bindingが不正な場合はValueErrorを送出する]
# }
def _parse_bindings(data: object) -> KeyboardBindings:
    if not isinstance(data, dict):
        raise ValueError("input config must be an object")

    expected_keys = {"version", "players"}
    unknown_keys = set(data) - expected_keys
    missing_keys = expected_keys - set(data)
    if unknown_keys:
        names = ", ".join(sorted(unknown_keys))
        raise ValueError(f"unknown input config fields: {names}")
    if missing_keys:
        names = ", ".join(sorted(missing_keys))
        raise ValueError(f"missing input config fields: {names}")

    version = data["version"]
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != INPUT_CONFIG_VERSION
    ):
        raise ValueError(f"unsupported input config version: {version!r}")

    players = data["players"]
    if not isinstance(players, dict):
        raise ValueError("input config players must be an object")

    parsed: dict[int, dict[str, str]] = {}
    for player_name, bindings in players.items():
        player = _parse_player_id(player_name)
        if not isinstance(bindings, dict):
            raise ValueError(f"bindings for player {player} must be an object")
        parsed[player] = dict(bindings)

    if set(parsed) != REQUIRED_PLAYERS:
        raise ValueError("input config must define exactly players 0 and 1")

    return KeyboardBindings(parsed)


# {
#   責務: [_parse_player_id: JSON上のplayer名をcanonicalな非負整数へ変換する]
#   処理: [10進数字文字列を整数化し、先頭ゼロ等の非canonical表記を拒否する]
#   引数: [player_name: players objectの未検証key]
#   戻り値: [変換済みplayer番号]
#   エラー: [文字列でない値、数字以外、またはcanonicalでない表記にValueErrorを送出する]
# }
def _parse_player_id(player_name: object) -> int:
    if not isinstance(player_name, str) or not player_name.isdecimal():
        raise ValueError(f"invalid player id: {player_name!r}")
    player = int(player_name)
    if str(player) != player_name:
        raise ValueError(f"invalid player id: {player_name!r}")
    return player


# {
#   責務: [_write_default_config: 現在のschemaと標準key割当で初期設定を書く]
#   処理: [versionとplayer別default bindingから整形済みUTF-8 JSONを生成し、末尾改行付きで保存する]
#   引数: [path: 新規input.jsonの保存先]
#   戻り値: [なし]
#   副作用: [設定ファイルをfilesystemへ書き込む]
#   エラー: [書き込み失敗を原因付きValueErrorとして伝える]
# }
def _write_default_config(path: Path) -> None:
    payload = {
        "version": INPUT_CONFIG_VERSION,
        "players": {
            str(player): bindings
            for player, bindings in sorted(DEFAULT_ACTION_KEYS.items())
        },
    }
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ValueError(f"failed to write default input config: {exc}") from exc
