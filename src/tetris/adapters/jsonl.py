"""Dependency-free JSON Lines adapters for commands and semantic input."""

import json
from typing import Iterable, Iterator

from tetris.application.command import Command
from tetris.application.input_action import InputAction


def decode_commands(lines: Iterable[str]) -> Iterator[Command]:
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            yield Command.from_dict(data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid command at line {number}: {exc}") from exc


def decode_input_action(line: str) -> InputAction:
    if not isinstance(line, str):
        raise ValueError("input action must be text")
    if not line.strip():
        raise ValueError("input action must not be empty")

    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input action JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("input action must be an object")

    expected_fields = {"player", "action"}
    unknown_fields = set(data) - expected_fields
    missing_fields = expected_fields - set(data)
    if unknown_fields:
        names = ", ".join(sorted(unknown_fields))
        raise ValueError(f"unknown input action fields: {names}")
    if missing_fields:
        names = ", ".join(sorted(missing_fields))
        raise ValueError(f"missing input action fields: {names}")

    return InputAction(player=data["player"], action=data["action"])


def encode_event(event: dict) -> str:
    if not isinstance(event, dict):
        raise ValueError("event must be an object")
    return json.dumps(event, ensure_ascii=False, separators=(",", ":"))
