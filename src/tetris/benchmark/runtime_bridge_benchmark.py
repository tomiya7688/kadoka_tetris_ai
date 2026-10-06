"""Compare the C++ native baseline with the Python ctypes learning bridge."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import platform
import statistics
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from tetris.learning import NativeRuntime
from tetris.learning.native_runtime import ACTION_CODES

MASK64 = (1 << 64) - 1
FNV_OFFSET = 14695981039346656037
FNV_PRIME = 1099511628211
ACTION_NAMES = tuple(ACTION_CODES)


@dataclass(frozen=True, slots=True)
# {
#   責務: [Options: 再現可能なruntime bridge benchmarkの入力設定を保持する]
#   フィールド: [seed, games, ticks, warmup, repeats, workers, library, native_executable]
#   不変条件: [seedと各上限はparse_argsで検証する]
# }
class Options:
    seed: int
    games: int
    ticks: int
    warmup: int
    repeats: int
    workers: int
    library: Path
    native_executable: Path


def parse_args(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--native-executable", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--games", type=int, default=4)
    parser.add_argument("--ticks", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--workers", type=int)
    values = parser.parse_args(argv)
    if not 0 <= values.seed <= MASK64 or not 1 <= values.games <= 64:
        parser.error("seed must fit uint64 and games must be between 1 and 64")
    if values.games - 1 > MASK64 - values.seed:
        parser.error("seed range overflows uint64")
    if not 1 <= values.ticks <= 1_000_000:
        parser.error("ticks must be between 1 and 1000000")
    if not 0 <= values.warmup <= 10 or not 1 <= values.repeats <= 21:
        parser.error("warmup must be 0..10 and repeats must be 1..21")
    if values.workers is None:
        worker_count = min(2, values.games)
    elif values.games == 1 and values.workers == 1:
        worker_count = 1
    elif not 2 <= values.workers <= min(values.games, 16):
        parser.error("workers must be between 2 and min(games, 16)")
    else:
        worker_count = values.workers
    return Options(
        values.seed, values.games, values.ticks, values.warmup, values.repeats, worker_count,
        values.library.resolve(strict=True), values.native_executable.resolve(strict=True),
    )


def hash_integer(checksum: int, value: int) -> int:
    for byte_index in range(8):
        checksum ^= (value >> (byte_index * 8)) & 0xFF
        checksum = (checksum * FNV_PRIME) & MASK64
    return checksum


def hash_observation(checksum: int, observation) -> int:
    checksum = hash_integer(checksum, 10)
    checksum = hash_integer(checksum, 20)
    for cells in (observation.locked_cells, observation.active_cells):
        occupied = sum(cells)
        checksum = hash_integer(checksum, occupied)
        for index, value in enumerate(cells):
            if value:
                checksum = hash_integer(checksum, index % 10)
                checksum = hash_integer(checksum, index // 10)
    has_active = observation.active_kind is not None
    checksum = hash_integer(checksum, has_active)
    if has_active:
        for value in (
            observation.active_kind, observation.active_x,
            observation.active_y, observation.active_rotation,
        ):
            checksum = hash_integer(checksum, value & MASK64)
    has_hold = observation.hold_kind is not None
    checksum = hash_integer(checksum, has_hold)
    if has_hold:
        checksum = hash_integer(checksum, observation.hold_kind)
    checksum = hash_integer(checksum, observation.hold_used)
    checksum = hash_integer(checksum, len(observation.next_pieces))
    for piece in observation.next_pieces:
        checksum = hash_integer(checksum, piece)
    for value in (
        observation.game_over, observation.lines, observation.combo,
        observation.back_to_back_active, observation.pieces_locked,
    ):
        checksum = hash_integer(checksum, int(value) & MASK64)
    return checksum


def choose_actions(observation, tick: int, player: int) -> list[str]:
    if observation.game_over or observation.active_kind is None:
        return []
    action_code = (tick + player + observation.pieces_locked) % 7
    return [ACTION_NAMES[action_code]]


# {
#   責務: [hash_player_trace: 一player分の観測と提案をtrace checksumへ追加する]
#   処理: [1: tickとplayerを追加する 2: 可視Observationを追加する 3: semantic proposalを追加する]
#   引数: [checksum: 前回までのhash tick: 現在tick player: player番号 observation: 可視状態 actions: 提案action]
#   戻り値: [更新後checksum]
# }
def hash_player_trace(checksum: int, tick: int, player: int, observation, actions: list[str]) -> int:
    checksum = hash_integer(checksum, tick)
    checksum = hash_integer(checksum, player)
    checksum = hash_observation(checksum, observation)
    checksum = hash_integer(checksum, len(actions))
    for action in actions:
        checksum = hash_integer(checksum, ACTION_CODES[action])
    return checksum


def run_python_trial(options: Options, *, batched: bool) -> dict:
    seeds = [options.seed + player for player in range(options.games)]
    startup_start = time.perf_counter()
    runtime = NativeRuntime(options.library, seeds)
    startup_seconds = time.perf_counter() - startup_start
    observations_seconds = 0.0
    ticks_seconds = 0.0
    checksum = FNV_OFFSET
    player_checksums = {player: FNV_OFFSET for player in range(options.games)}
    total_start = time.perf_counter()
    try:
        for tick in range(options.ticks):
            observe_start = time.perf_counter()
            observations = (
                runtime.observe_many()
                if batched
                else tuple(runtime.observe(player) for player in range(options.games))
            )
            observations_seconds += time.perf_counter() - observe_start
            proposals = []
            for player, observation in enumerate(observations):
                actions = choose_actions(observation, tick, player)
                checksum = hash_player_trace(checksum, tick, player, observation, actions)
                player_checksums[player] = hash_player_trace(
                    player_checksums[player], tick, player, observation, actions
                )
                proposals.append((player, 0, actions))

            tick_start = time.perf_counter()
            if batched:
                runtime.submit_many(tick, proposals)
            else:
                for player, first_sequence, actions in proposals:
                    runtime.submit(player, tick, first_sequence, actions)
            processed_tick, _ = runtime.advance()
            if processed_tick != tick:
                raise RuntimeError("bridge returned an unexpected processed tick")
            ticks_seconds += time.perf_counter() - tick_start
        total_seconds = time.perf_counter() - total_start
    finally:
        runtime.close()
    return {
        "startup_seconds": startup_seconds,
        "observation_seconds": observations_seconds,
        "tick_seconds": ticks_seconds,
        "total_seconds": total_seconds,
        "checksum": checksum,
        "player_checksums": player_checksums,
    }


# {
#   責務: [run_worker_partition: 一つのthread内で担当gameを実行してplayer別traceを返す]
#   処理: [1: 担当seedでNativeRuntimeを生成する 2: 観測・提案・tick進行を繰り返す 3: Runtimeを閉じてplayer別checksumを返す]
#   引数: [task: 共通benchmark設定と担当player番号]
#   戻り値: [player番号とtrace checksumの組]
#   エラー: [Runtime生成・bridge操作に失敗した場合は例外を呼び出し元へ伝える]
# }
def run_worker_partition(task: tuple[Options, tuple[int, ...]]) -> tuple[tuple[int, int], ...]:
    options, player_slots = task
    seeds = [options.seed + player for player in player_slots]
    player_checksums = {player: FNV_OFFSET for player in player_slots}
    runtime = NativeRuntime(options.library, seeds)
    try:
        # 各threadは独立したRuntimeを所有し、player間の状態共有を避けます。
        for tick in range(options.ticks):
            observations = runtime.observe_many()
            proposals = []
            for local_player, (player, observation) in enumerate(zip(player_slots, observations)):
                actions = choose_actions(observation, tick, player)
                player_checksums[player] = hash_player_trace(
                    player_checksums[player], tick, player, observation, actions
                )
                proposals.append((local_player, 0, actions))
            runtime.submit_many(tick, proposals)
            processed_tick, _ = runtime.advance()
            if processed_tick != tick:
                raise RuntimeError("worker bridge returned an unexpected processed tick")
    finally:
        runtime.close()
    return tuple(sorted(player_checksums.items()))


# {
#   責務: [worker_tasks: player slotをworker数に応じて連続分割する]
#   処理: [1: 均等な担当数を計算する 2: 余りを先頭workerから配分する 3: 空きのないtask列を返す]
#   引数: [options: games数を含む設定 worker_count: 起動するworker数]
#   戻り値: [各workerへ渡す設定とplayer番号のtuple]
# }
def worker_tasks(options: Options, worker_count: int) -> tuple[tuple[Options, tuple[int, ...]], ...]:
    base_size, remainder = divmod(options.games, worker_count)
    tasks = []
    first_player = 0
    for worker_index in range(worker_count):
        player_count = base_size + (worker_index < remainder)
        player_slots = tuple(range(first_player, first_player + player_count))
        tasks.append((options, player_slots))
        first_player += player_count
    return tuple(tasks)


# {
#   責務: [combined_player_checksum: worker結果をplayer順の総合checksumへまとめる]
#   処理: [1: player別結果を番号順に並べる 2: 固定順でchecksumを合成する]
#   引数: [results: 各workerが返したplayer別checksum]
#   戻り値: [worker割り当て順に依存しないuint64 checksum]
# }
def combined_player_checksum(results: tuple[tuple[tuple[int, int], ...], ...]) -> int:
    player_checksums = sorted(
        (player, checksum)
        for worker_result in results
        for player, checksum in worker_result
    )
    combined_checksum = FNV_OFFSET
    for player, checksum in player_checksums:
        combined_checksum = hash_integer(combined_checksum, player)
        combined_checksum = hash_integer(combined_checksum, checksum)
    return combined_checksum


# {
#   責務: [run_worker_trial: 指定worker数で一回のbounded benchmarkを計測する]
#   処理: [1: playerをworkerへ割り当てる 2: thread poolで同時実行する 3: 経過時間とchecksumを返す]
#   引数: [executor: worker thread pool options: workload worker_count: 同時worker数]
#   戻り値: [worker数、wall時間、総合trace checksum]
# }
def run_worker_trial(
    executor: ThreadPoolExecutor,
    options: Options,
    worker_count: int,
) -> dict:
    started_at = time.perf_counter()
    results = tuple(executor.map(run_worker_partition, worker_tasks(options, worker_count)))
    elapsed_seconds = time.perf_counter() - started_at
    return {
        "workers": worker_count,
        "wall_seconds": elapsed_seconds,
        "checksum": combined_player_checksum(results),
    }


# {
#   責務: [await_worker_pool_start: benchmark開始前に全worker threadの起動を揃える]
#   処理: [1: barrier到着を最大30秒待つ 2: timeout時はthread pool初期化失敗を伝える]
#   引数: [barrier: 全workerと呼び出し元が参加する同期barrier]
#   戻り値: [barrierのparticipant index]
#   エラー: [30秒以内に全workerが起動しない場合はBrokenBarrierError]
# }
def await_worker_pool_start(barrier: threading.Barrier) -> int:
    return barrier.wait(timeout=30)


# {
#   責務: [worker_scaling_result: 同一条件の1 workerと複数workerを比較する]
#   処理: [1: 全threadを起動する 2: warmup後に各条件を反復計測する 3: checksum一致を確認して中央値を返す]
#   引数: [options: seed、games、ticks、反復数、worker数を含む設定]
#   戻り値: [worker別throughput、speedup、決定論的checksum]
#   エラー: [worker数によってplayer traceが変わった場合はRuntimeError]
# }
def worker_scaling_result(options: Options, expected_checksum: int) -> dict:
    if options.workers == 1:
        return {
            "scope": "python_ctypes_thread_workers",
            "workers_compared": [1],
            "games": options.games,
            "ticks_per_game": options.ticks,
            "warmup": options.warmup,
            "repeats": options.repeats,
            "matching_worker_traces": None,
            "scaling_available": False,
            "reason": "worker scaling requires at least two games",
        }
    with ThreadPoolExecutor(max_workers=options.workers) as executor:
        # 全workerを計測前に起動し、初回だけthread生成時間が乗る差を除きます。
        start_barrier = threading.Barrier(options.workers + 1)
        start_futures = [
            executor.submit(await_worker_pool_start, start_barrier)
            for _ in range(options.workers)
        ]
        try:
            start_barrier.wait(timeout=30)
            for future in start_futures:
                future.result()
        except threading.BrokenBarrierError as error:
            raise RuntimeError("worker threads did not start within 30 seconds") from error
        for _ in range(options.warmup):
            run_worker_trial(executor, options, 1)
            run_worker_trial(executor, options, options.workers)
        single_worker_trials = [
            run_worker_trial(executor, options, 1) for _ in range(options.repeats)
        ]
        parallel_trials = [
            run_worker_trial(executor, options, options.workers) for _ in range(options.repeats)
        ]
    worker_checksum = single_worker_trials[0]["checksum"]
    if worker_checksum != expected_checksum or any(
        trial["checksum"] != worker_checksum
        for trial in single_worker_trials + parallel_trials
    ):
        raise RuntimeError("worker trace differs from the single-runtime Python bridge trace")
    single_worker_seconds = statistics.median(trial["wall_seconds"] for trial in single_worker_trials)
    parallel_seconds = statistics.median(trial["wall_seconds"] for trial in parallel_trials)
    return {
        "scope": "python_ctypes_thread_workers",
        "workers_compared": [1, options.workers],
        "games": options.games,
        "ticks_per_game": options.ticks,
        "warmup": options.warmup,
        "repeats": options.repeats,
        "trace_checksum": f"{worker_checksum:016x}",
        "matching_worker_traces": True,
        "scaling_available": True,
        "single_worker_games_per_second": options.games / single_worker_seconds,
        "parallel_games_per_second": options.games / parallel_seconds,
        "speedup": single_worker_seconds / parallel_seconds,
        "worker_thread_startup_excluded": True,
        "runtime_creation_included": True,
    }


def median(trials: list[dict], field: str) -> float:
    return statistics.median(trial[field] for trial in trials)


def rates(options: Options, observations: float, ticks: float, total: float) -> dict:
    decisions = options.games * options.ticks
    return {
        "median_observations_per_second": decisions / observations if observations else 0.0,
        "median_tick_advances_per_second": options.ticks / ticks if ticks else 0.0,
        "median_decision_roundtrips_per_second": decisions / total if total else 0.0,
        "median_fixed_horizon_episodes_per_second": options.games / total if total else 0.0,
    }


def python_result(options: Options, trials: list[dict], *, batched: bool) -> dict:
    result = {
        "scope": "python_ctypes_bridge_batched" if batched else "python_ctypes_bridge_serial",
        "seed": options.seed,
        "games": options.games,
        "ticks_per_game": options.ticks,
        "warmup": options.warmup,
        "repeats": options.repeats,
        "median_startup_ms": median(trials, "startup_seconds") * 1000,
        "trace_checksum": f"{trials[0]['checksum']:016x}",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
    }
    result.update(rates(
        options, median(trials, "observation_seconds"),
        median(trials, "tick_seconds"), median(trials, "total_seconds"),
    ))
    return result


def native_result(options: Options) -> dict:
    arguments = [
        str(options.native_executable), "--seed", str(options.seed),
        "--games", str(options.games), "--ticks", str(options.ticks),
        "--warmup", str(options.warmup), "--repeats", str(options.repeats),
    ]
    completed = subprocess.run(arguments, check=True, capture_output=True, text=True, timeout=120)
    result = json.loads(completed.stdout)
    if result["trace_checksum"] != f"{int(result['trace_checksum'], 16):016x}":
        raise RuntimeError("native benchmark checksum formatting is invalid")
    return result


def run_comparison(options: Options) -> dict:
    native = native_result(options)
    bridges = {}
    for batched, name in ((False, "python_serial_bridge"), (True, "python_bridge")):
        for _ in range(options.warmup):
            run_python_trial(options, batched=batched)
        trials = [run_python_trial(options, batched=batched) for _ in range(options.repeats)]
        if len({trial["checksum"] for trial in trials}) != 1:
            raise RuntimeError("fixed-seed Python bridge trace changed between repeats")
        bridges[name] = python_result(options, trials, batched=batched)
        if bridges[name]["trace_checksum"] != native["trace_checksum"]:
            raise RuntimeError(
                f"native and {name} traces differ: "
                f"{native['trace_checksum']} != {bridges[name]['trace_checksum']}"
            )
    candidate = bridges["python_bridge"]
    reference_checksum = combined_player_checksum((tuple(sorted(trials[0]["player_checksums"].items())),))
    worker_scaling = worker_scaling_result(options, reference_checksum)
    return {
        "configuration": {
            "seed": options.seed, "games": options.games, "ticks_per_game": options.ticks,
            "warmup": options.warmup, "repeats": options.repeats, "workers": options.workers,
        },
        "native": native,
        "python_bridge": candidate,
        "python_serial_bridge": bridges["python_serial_bridge"],
        "worker_scaling": worker_scaling,
        "matching_trace": True,
        "batch_speedup_vs_serial_bridge": (
            candidate["median_decision_roundtrips_per_second"]
            / bridges["python_serial_bridge"]["median_decision_roundtrips_per_second"]
        ),
        "roundtrip_slowdown_vs_native": (
            native["median_decision_roundtrips_per_second"]
            / candidate["median_decision_roundtrips_per_second"]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    try:
        result = run_comparison(parse_args(argv))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"benchmark error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
