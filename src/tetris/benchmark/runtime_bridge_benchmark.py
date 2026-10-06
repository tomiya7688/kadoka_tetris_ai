"""Compare the C++ native baseline with the Python ctypes learning bridge."""

import argparse
import json
import platform
import statistics
import subprocess
import sys
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
class Options:
    seed: int
    games: int
    ticks: int
    warmup: int
    repeats: int
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
    values = parser.parse_args(argv)
    if not 0 <= values.seed <= MASK64 or not 1 <= values.games <= 64:
        parser.error("seed must fit uint64 and games must be between 1 and 64")
    if values.games - 1 > MASK64 - values.seed:
        parser.error("seed range overflows uint64")
    if not 1 <= values.ticks <= 1_000_000:
        parser.error("ticks must be between 1 and 1000000")
    if not 0 <= values.warmup <= 10 or not 1 <= values.repeats <= 21:
        parser.error("warmup must be 0..10 and repeats must be 1..21")
    return Options(
        values.seed, values.games, values.ticks, values.warmup, values.repeats,
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


def run_python_trial(options: Options, *, batched: bool) -> dict:
    seeds = [options.seed + player for player in range(options.games)]
    startup_start = time.perf_counter()
    runtime = NativeRuntime(options.library, seeds)
    startup_seconds = time.perf_counter() - startup_start
    observations_seconds = 0.0
    ticks_seconds = 0.0
    checksum = FNV_OFFSET
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
                checksum = hash_integer(checksum, tick)
                checksum = hash_integer(checksum, player)
                checksum = hash_observation(checksum, observation)
                actions = choose_actions(observation, tick, player)
                checksum = hash_integer(checksum, len(actions))
                for action in actions:
                    checksum = hash_integer(checksum, ACTION_CODES[action])
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
    return {
        "configuration": {
            "seed": options.seed, "games": options.games, "ticks_per_game": options.ticks,
            "warmup": options.warmup, "repeats": options.repeats,
        },
        "native": native,
        "python_bridge": candidate,
        "python_serial_bridge": bridges["python_serial_bridge"],
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
