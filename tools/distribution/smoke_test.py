"""Smoke-test a generated Windows onedir distribution."""

import json
import subprocess
import sys
from pathlib import Path


REQUIRED_USER_DATA_DIRECTORIES = ("Config", "Logs")
REQUIRED_USER_DATA_FILES = (
    Path("Config") / "input.json",
    Path("Config") / "standard_cpu.json",
)


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

    _verify_frozen_benchmark(executable, distribution_dir, user_data)


def _verify_frozen_benchmark(
    executable: Path,
    distribution_dir: Path,
    user_data: Path,
) -> None:
    benchmark_output = user_data / "Logs" / "smoke-benchmark.json"
    subprocess.run(
        [
            str(executable),
            "--benchmark-cpu",
            "easy",
            "--benchmark-games",
            "1",
            "--benchmark-max-pieces",
            "1",
            "--benchmark-seed",
            "123",
            "--benchmark-output",
            str(benchmark_output),
        ],
        cwd=distribution_dir,
        check=True,
        timeout=30,
    )

    if not benchmark_output.is_file():
        raise RuntimeError("frozen benchmark did not create JSON output")
    payload = json.loads(benchmark_output.read_text(encoding="utf-8"))
    if payload.get("level") != "easy":
        raise RuntimeError("frozen benchmark reported the wrong CPU level")
    evaluator = payload.get("evaluator", {})
    if evaluator.get("evaluator_id") != "visible-board-v1":
        raise RuntimeError("frozen benchmark did not record evaluator metadata")
    games = payload.get("games", [])
    if len(games) != 1 or games[0].get("placements") != 1:
        raise RuntimeError("frozen benchmark did not place exactly one piece")
    benchmark_output.unlink()


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
