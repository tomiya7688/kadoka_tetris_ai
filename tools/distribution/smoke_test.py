"""Smoke-test a generated Windows onedir distribution."""

import subprocess
import sys
from pathlib import Path


REQUIRED_USER_DATA_DIRECTORIES = ("Config", "Logs")
REQUIRED_USER_DATA_FILES = (Path("Config") / "input.json",)


def verify_distribution(distribution_dir: Path) -> None:
    executable = distribution_dir / "KadokaTetrisAI.exe"
    if not executable.is_file():
        raise RuntimeError(f"missing executable: {executable}")

    subprocess.run(
        [str(executable), "--smoke-test", "--api-port", "0"],
        cwd=distribution_dir,
        check=True,
        timeout=15,
    )

    user_data = distribution_dir / "UserData"
    for name in REQUIRED_USER_DATA_DIRECTORIES:
        path = user_data / name
        if not path.is_dir():
            raise RuntimeError(f"missing runtime directory: {path}")

    for relative_path in REQUIRED_USER_DATA_FILES:
        path = user_data / relative_path
        if not path.is_file():
            raise RuntimeError(f"missing runtime file: {path}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: smoke_test.py DIST_DIR", file=sys.stderr)
        return 2

    distribution_dir = Path(argv[1]).resolve()
    verify_distribution(distribution_dir)
    print("[smoke] distribution OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
