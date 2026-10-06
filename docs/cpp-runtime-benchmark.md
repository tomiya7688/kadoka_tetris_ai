# C++ Headless Runtime Benchmark

`kadoka_tetris_runtime_benchmark` records the C++ native baseline for Issue #37. The Python comparison runs the same policy and workload through the learning API, requires the trace checksums to match, and reports throughput separately. The Python wrapper also measures independent thread workers; each worker owns its own C++ Runtime.

## Run

```powershell
cmake --build build-cpp --config Release --target kadoka_tetris_runtime_benchmark
build-cpp\Release\kadoka_tetris_runtime_benchmark.exe --seed 123 --games 8 --ticks 10000 --warmup 2 --repeats 5
```

All parameters are bounded: games 1-64, ticks 1-1,000,000, warmup 0-10, and repeats 1-21. Each game slot uses seed `seed + slot`; every measured repeat recreates the runtime. The deterministic policy sees only `PlayerObservation` and submits semantic proposals through `HeadlessRuntime`.

The executable prints one JSON object with the input configuration, median startup time, observation throughput, tick-advance throughput, full decision-roundtrip throughput, fixed-horizon episode throughput, and a trace checksum. Every measured repeat must produce the same checksum or the benchmark exits with an error. Warmup runs are excluded from reported medians.

## Compare the Python candidate

Build both targets in Release, set `PYTHONPATH=src`, then run the wrapper with the matching DLL and baseline executable:

```powershell
$env:PYTHONPATH = "src"
python -m tetris.benchmark.runtime_bridge_benchmark `
  --library build-cpp/Release/kadoka_tetris_bridge.dll `
  --native-executable build-cpp/Release/kadoka_tetris_runtime_benchmark.exe `
  --seed 123 --games 8 --ticks 5000 --warmup 2 --repeats 5 --workers 4
```

Linux paths are `build-cpp/libkadoka_tetris_bridge.so` and `build-cpp/kadoka_tetris_runtime_benchmark`. The command returns one JSON object containing native, serial ctypes and batched ctypes medians, per-stage rates, Python version/platform, matching checksums, batch speedup, and worker scaling. Both bridge modes run with the same inputs and must match the native trace.

Worker scaling compares one thread with `--workers` threads using identical seeds and policy. Each thread owns one Runtime for its assigned games. The benchmark combines player trace checksums in stable order and requires all worker counts to match. The scaling report includes median games/second and speedup, and Runtime creation is included in each measurement. Set `--workers` from 2 through `min(games, 16)`; when omitted, the wrapper uses up to two workers. For a single game, scaling is reported as unavailable. Threads can overlap native calls because ctypes releases the GIL, but this result does not demonstrate parallelism for CPU-bound Python learning code.

The benchmark fails if any runner is nondeterministic or traces differ. The startup metric is Runtime construction, including the candidate's library load; it excludes starting the Python interpreter. The timed Python roundtrip includes immutable snapshot conversion, Python policy selection, checksum, ctypes submission, and C++ tick advance. Native measures the corresponding C++ policy and checksum without crossing the Python boundary.

The policy can reach game over before the tick horizon, so a long run includes calls on terminal games. Treat rates as a fixed workload comparison, not as a measurement of full completed Tetris games. Run with identical seeds/options/build mode/machine and retain the emitted configuration with each result.

## Recorded comparison

Local Windows 10 Release run, CPython 3.14.7 / MSVC 18.10.1; seed 123, 8 players, 500 ticks/player, warmup 2, repeats 5. The traces matched at `622275c1bca59bcc`.

| Measure | Native C++ | Python ctypes |
| --- | ---: | ---: |
| Runtime startup (ms) | 0.003 | 0.436 |
| Observations/s | 586,966 | 73,969 |
| Tick advances/s | 2,510,040 | 23,112 |
| Decision roundtrips/s | 365,551 | 4,454 |

This initial serial comparison showed about 82× lower Python decision roundtrip throughput. Its measured path includes immutable snapshot conversion, Python policy selection, and trace hashing, so it reflects the learning call path rather than isolated foreign-function overhead.

The paired serial-versus-batch mode uses the same workload for both Python paths. A Windows Release run on CPython 3.14.7 / MSVC 18.10.1 (seed 123, 8 players, 500 ticks/player, warmup 1, repeats 3) matched checksum `622275c1bca59bcc` in all three paths. Median Python decision roundtrips were 2,822/s serial and 3,199/s batched (1.13×); native was 283,746/s in that run. Treat these as one machine's measurements, not a portable speed promise.

Record the source revision, compiler/build configuration, and machine alongside the JSON output when comparing runs. Compare values only across matching seeds, game count, tick count, build type, and workload. The implementation in `src/tetris/benchmark/runtime_bridge_benchmark.py` is a measurement harness, not a game/runtime dependency.
