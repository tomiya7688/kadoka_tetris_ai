"""Persistent keyboard input configuration stored under UserData/Config."""

import json
from pathlib import Path

from tetris.adapters.keyboard_bindings import DEFAULT_ACTION_KEYS, KeyboardBindings


INPUT_CONFIG_FILENAME = "input.json"
INPUT_CONFIG_VERSION = 1
REQUIRED_PLAYERS = frozenset({0, 1})


def load_keyboard_bindings(config_dir: Path) -> KeyboardBindings:
    path = ensure_input_config(config_dir)
    data = _read_json(path)
    return _parse_bindings(data)


def ensure_input_config(config_dir: Path) -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / INPUT_CONFIG_FILENAME
    if not path.exists():
        _write_default_config(path)
    return path


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input config JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"failed to read input config: {exc}") from exc


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

    if data["version"] != INPUT_CONFIG_VERSION:
        raise ValueError(f"unsupported input config version: {data['version']!r}")

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


def _parse_player_id(player_name: object) -> int:
    if not isinstance(player_name, str) or not player_name.isdecimal():
        raise ValueError(f"invalid player id: {player_name!r}")
    player = int(player_name)
    if str(player) != player_name:
        raise ValueError(f"invalid player id: {player_name!r}")
    return player


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
