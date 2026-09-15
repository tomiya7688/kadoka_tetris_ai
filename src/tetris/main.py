"""Application entry point for source and frozen builds."""

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from tetris.adapters.jsonl_api_server import JsonlApiServer
from tetris.adapters.pygame_app import PygameApp
from tetris.adapters.pygame_versus_app import PygameVersusApp
from tetris.benchmark import (
    StandardCpuBenchmark,
    StandardCpuComparison,
    StandardCpuWeightSweep,
)
from tetris.cpu import (
    StandardCpuStrategy,
    ensure_standard_cpu_config,
    load_standard_cpu_config,
    standard_cpu_profile,
)
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
        "--versus",
        action="store_true",
        help="open the two-player visible versus screen",
    )
    parser.add_argument(
        "--versus-cpu-level",
        choices=("off", "easy", "normal", "hard"),
        default="off",
        help="in versus mode, let the built-in CPU control player 2",
    )
    parser.add_argument(
        "--versus-garbage-seed",
        type=int,
        default=0,
        help="deterministic garbage-hole seed for versus mode",
    )
    benchmark_mode = parser.add_mutually_exclusive_group()
    benchmark_mode.add_argument(
        "--benchmark-cpu",
        choices=("easy", "normal", "hard", "all"),
        default=None,
        help="run one standard CPU level, or compare all levels headlessly",
    )
    benchmark_mode.add_argument(
        "--benchmark-weight-sweep",
        choices=("easy", "normal", "hard"),
        default=None,
        help="sweep each evaluator weight around the configured baseline",
    )
    parser.add_argument(
        "--benchmark-weight-step",
        type=float,
        default=0.25,
        help="fractional +/- step for weight sweep candidates (default: 0.25)",
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
        help="benchmark JSON output path",
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
    config_dir = user_data / "Config"
    ensure_standard_cpu_config(config_dir)

    if args.benchmark_cpu is not None or args.benchmark_weight_sweep is not None:
        return _run_cpu_benchmark(args, user_data)

    bindings = load_keyboard_bindings(config_dir)
    if args.smoke_test:
        return _run_smoke_test(args.api_port, args.player)

    if args.versus:
        return _run_versus(args, bindings, config_dir)

    cpu_strategy = None
    if args.cpu_level != "off":
        cpu_config = load_standard_cpu_config(config_dir)
        cpu_strategy = StandardCpuStrategy(
            standard_cpu_profile(args.cpu_level),
            weights=cpu_config.weights,
        )

    return PygameApp(
        bindings=bindings,
        player=args.player,
        api_port=args.api_port,
        cpu_strategy=cpu_strategy,
    ).run()


def _run_versus(
    args: argparse.Namespace,
    bindings,
    config_dir: Path,
) -> int:
    if args.api_port is not None:
        raise ValueError("localhost API is not yet available in versus mode")
    if args.cpu_level != "off":
        raise ValueError("use --versus-cpu-level for versus mode")

    cpu_strategy = None
    if args.versus_cpu_level != "off":
        cpu_config = load_standard_cpu_config(config_dir)
        cpu_strategy = StandardCpuStrategy(
            standard_cpu_profile(args.versus_cpu_level),
            weights=cpu_config.weights,
        )
    return PygameVersusApp(
        bindings=bindings,
        garbage_seed=args.versus_garbage_seed,
        cpu_strategy=cpu_strategy,
    ).run()


def _run_cpu_benchmark(args: argparse.Namespace, user_data: Path) -> int:
    cpu_config = load_standard_cpu_config(user_data / "Config")
    default_filename = "cpu-benchmark.json"
    if args.benchmark_weight_sweep is not None:
        benchmark = StandardCpuWeightSweep(
            args.benchmark_weight_sweep,
            max_pieces=args.benchmark_max_pieces,
            base_weights=cpu_config.weights,
            step_fraction=args.benchmark_weight_step,
        )
        default_filename = "cpu-weight-sweep.json"
    elif args.benchmark_cpu == "all":
        benchmark = StandardCpuComparison(
            max_pieces=args.benchmark_max_pieces,
            weights=cpu_config.weights,
        )
    else:
        benchmark = StandardCpuBenchmark(
            args.benchmark_cpu,
            max_pieces=args.benchmark_max_pieces,
            weights=cpu_config.weights,
        )

    report = benchmark.run(
        game_count=args.benchmark_games,
        seed=args.benchmark_seed,
    )
    output_path = args.benchmark_output or user_data / "Logs" / default_filename
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
