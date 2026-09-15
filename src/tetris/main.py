"""Application entry point for source and frozen builds."""

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from tetris.adapters.jsonl_api_server import JsonlApiServer
from tetris.adapters.pygame_app import PygameApp
from tetris.benchmark import StandardCpuBenchmark
from tetris.cpu import StandardCpuStrategy, standard_cpu_profile
from tetris.input_config import load_keyboard_bindings
from tetris.runtime_paths import ensure_user_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="KadokaTetrisAI")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="initialize portable runtime directories and config, then exit",
    )
    parser.add_argument(
        "--player",
        type=int,
        choices=(0, 1),
        default=0,
        help="keyboard binding profile to use (0 or 1)",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=None,
        help="enable localhost JSONL input API on this TCP port",
    )
    parser.add_argument(
        "--cpu-level",
        choices=("off", "easy", "normal", "hard"),
        default="off",
        help="enable the built-in visible-only standard CPU",
    )
    parser.add_argument(
        "--benchmark-cpu",
        choices=("easy", "normal", "hard"),
        default=None,
        help="run the selected standard CPU headlessly and exit",
    )
    parser.add_argument(
        "--benchmark-games",
        type=int,
        default=1,
        help="number of reproducible headless benchmark games",
    )
    parser.add_argument(
        "--benchmark-max-pieces",
        type=int,
        default=100,
        help="maximum locked pieces per benchmark game",
    )
    parser.add_argument(
        "--benchmark-seed",
        type=int,
        default=0,
        help="first benchmark RNG seed; later games increment it by one",
    )
    parser.add_argument(
        "--benchmark-output",
        type=Path,
        default=None,
        help="benchmark JSON output path (default: UserData/Logs/cpu-benchmark.json)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    user_data = ensure_user_data(args.data_root)

    if args.benchmark_cpu is not None:
        return _run_cpu_benchmark(args, user_data)

    bindings = load_keyboard_bindings(user_data / "Config")
    if args.smoke_test:
        return _run_smoke_test(args.api_port, args.player)

    cpu_strategy = None
    if args.cpu_level != "off":
        cpu_strategy = StandardCpuStrategy(standard_cpu_profile(args.cpu_level))

    return PygameApp(
        bindings=bindings,
        player=args.player,
        api_port=args.api_port,
        cpu_strategy=cpu_strategy,
    ).run()


def _run_cpu_benchmark(args: argparse.Namespace, user_data: Path) -> int:
    benchmark = StandardCpuBenchmark(
        args.benchmark_cpu,
        max_pieces=args.benchmark_max_pieces,
    )
    report = benchmark.run(
        game_count=args.benchmark_games,
        seed=args.benchmark_seed,
    )
    output_path = args.benchmark_output or user_data / "Logs" / "cpu-benchmark.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    output_path.write_text(payload + "\n", encoding="utf-8")
    if sys.stdout is not None:
        print(payload)
    return 0


def _run_smoke_test(api_port: int | None, player: int) -> int:
    if api_port is None:
        return 0
    server = JsonlApiServer(api_port, {player})
    server.start()
    server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
