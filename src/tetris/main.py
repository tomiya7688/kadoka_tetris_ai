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
    StandardCpuVersusBenchmark,
    StandardCpuWeightSweep,
)
from tetris.cpu import (
    StandardCpuStrategy,
    VersusStandardCpuStrategy,
    ensure_standard_cpu_config,
    load_standard_cpu_config,
    standard_cpu_profile,
)
from tetris.input_config import load_keyboard_bindings
from tetris.runtime_paths import ensure_user_data


# {
#   責務: [build_parser: アプリ実行・対戦・benchmark用のCLI引数を定義する]
#   処理: [1: smoke test、player、API、CPU、versusの引数を登録する 2: 排他的なbenchmark modeと共通計測条件を登録する 3: parserを返す]
#   引数: [なし]
#   戻り値: [選択肢・既定値・相互排他条件を設定したArgumentParser]
#   エラー: [不正な引数はparse_args実行時にargparseがusageを表示してSystemExitを送出する]
# }
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
        help="in versus mode, let the visible opponent-aware CPU control player 2",
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
    benchmark_mode.add_argument(
        "--benchmark-versus",
        nargs=2,
        metavar=("LEVEL_A", "LEVEL_B"),
        choices=("easy", "normal", "hard"),
        default=None,
        help="run mirrored visible CPU-vs-CPU matches for two levels",
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
        help="number of reproducible benchmark seeds (versus runs two mirrored legs each)",
    )
    parser.add_argument(
        "--benchmark-max-pieces",
        type=int,
        default=100,
        help="maximum locked pieces per player in each benchmark game",
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


# {
#   責務: [main: 設定とCLI選択に応じてbenchmark・smoke test・通常プレイを起動する]
#   処理: [1: 引数を解析する 2: UserDataとCPU設定を初期化する 3: benchmark modeを先に実行する 4: 入力bindingを読み、smoke test・versus・通常画面へ分岐する]
#   引数: [argv: parseするCLI引数列。Noneならprocess引数を使う]
#   戻り値: [選択したmodeまたはPygameAppが返す終了コード]
#   副作用: [UserData/Configを初期化し、選択modeに応じてbenchmark出力、API serverまたはGUIを実行する]
#   エラー: [argparseのSystemExitおよび初期化・mode実行中の例外を呼び出し元へ伝える]
# }
def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    user_data = ensure_user_data(args.data_root)
    config_dir = user_data / "Config"
    ensure_standard_cpu_config(config_dir)

    if (
        args.benchmark_cpu is not None
        or args.benchmark_weight_sweep is not None
        or args.benchmark_versus is not None
    ):
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


# {
#   責務: [_run_versus: 人間同士または人間対CPUのversus画面を起動する]
#   処理: [1: versus非対応のlocalhost APIと通常CPU指定を拒否する 2: 指定時はConfigから重みを読みversus用CPU strategyを作る 3: binding・garbage seed・CPUをversus appへ渡す]
#   引数: [args: parserが検証したversus mode設定 bindings: player別入力割当 config_dir: CPU設定の保存先]
#   戻り値: [PygameVersusApp.runが返す終了コード]
#   副作用: [versus用GUIを起動し、必要なら標準CPU設定を読み込む]
#   エラー: [localhost APIまたは通常CPU指定時はValueErrorを送出し、設定読み込み・GUI起動の例外は伝播する]
# }
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
        cpu_strategy = VersusStandardCpuStrategy(
            standard_cpu_profile(args.versus_cpu_level),
            weights=cpu_config.weights,
        )
    return PygameVersusApp(
        bindings=bindings,
        garbage_seed=args.versus_garbage_seed,
        cpu_strategy=cpu_strategy,
    ).run()


# {
#   責務: [_run_cpu_benchmark: 選択された標準CPU benchmarkを実行して結果を保存する]
#   処理: [1: UserDataのConfigから標準CPU重みを読み込む 2: 指定されたversus・weight sweep・全CPU比較・単一CPUのbenchmarkを選ぶ 3: 共通のゲーム数とseedで実行する 4: 結果をJSONへ変換して出力先へ保存し標準出力にも表示する]
#   引数: [args: parserが検証したbenchmark modeと計測条件 user_data: UserDataのルートパス]
#   戻り値: [結果ファイルの保存後に返す終了コード0]
#   副作用: [CPU設定を読み込みbenchmarkを実行し、必要なら出力先directoryを作成してJSONを書き標準出力へ表示する]
#   エラー: [設定読み込み・benchmark実行・directory作成・ファイル書き込みで発生した例外を伝播する]
# }
def _run_cpu_benchmark(args: argparse.Namespace, user_data: Path) -> int:
    cpu_config = load_standard_cpu_config(user_data / "Config")
    default_filename = "cpu-benchmark.json"
    if args.benchmark_versus is not None:
        benchmark = StandardCpuVersusBenchmark(
            args.benchmark_versus[0],
            args.benchmark_versus[1],
            max_pieces_per_player=args.benchmark_max_pieces,
            weights=cpu_config.weights,
        )
        default_filename = "cpu-versus-benchmark.json"
    elif args.benchmark_weight_sweep is not None:
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
