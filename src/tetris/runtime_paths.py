"""Runtime paths that work in source and frozen distributions."""

import sys
from pathlib import Path


USER_DATA_SUBDIRECTORIES = ("Config", "Logs")


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def ensure_user_data(root: Path | None = None) -> Path:
    base = root if root is not None else application_root()
    user_data = base / "UserData"
    user_data.mkdir(parents=True, exist_ok=True)
    for name in USER_DATA_SUBDIRECTORIES:
        (user_data / name).mkdir(exist_ok=True)
    return user_data
