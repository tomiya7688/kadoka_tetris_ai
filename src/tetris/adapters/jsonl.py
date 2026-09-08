"""Dependency-free JSON Lines command adapter."""
import json
from typing import Iterable, Iterator
from tetris.application.command import Command

def decode_commands(lines: Iterable[str]) -> Iterator[Command]:
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            data=json.loads(line)
            yield Command.from_dict(data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid command at line {number}: {exc}") from exc

def encode_event(event: dict) -> str:
    if not isinstance(event, dict):
        raise ValueError("event must be an object")
    return json.dumps(event, ensure_ascii=False, separators=(",", ":"))
