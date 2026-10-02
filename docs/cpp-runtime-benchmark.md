# C++ Headless Runtime Benchmark

`kadoka_tetris_runtime_benchmark` records an initial native baseline for Issue #37. It exercises the C++ `HeadlessRuntime` directly and does not launch Python or claim transport/worker-scaling results.

## Run

```powershell
cmake --build build-cpp --config Release --target kadoka_tetris_runtime_benchmark
build-cpp\Release\kadoka_tetris_runtime_benchmark.exe --seed 123 --games 8 --ticks 10000 --warmup 2 --repeats 5
```

All parameters are bounded: games 1-64, ticks 1-1,000,000, warmup 0-10, and repeats 1-21. Each game slot uses seed `seed + slot`; every measured repeat recreates the runtime. The deterministic policy sees only `PlayerObservation` and submits semantic proposals through `HeadlessRuntime`.

The executable prints one JSON object with the input configuration, median startup time, observation throughput, tick-advance throughput, full decision-roundtrip throughput, fixed-horizon episode throughput, and a trace checksum. Every measured repeat must produce the same checksum or the benchmark exits with an error. Warmup runs are excluded from reported medians.

Record the source revision, compiler/build configuration, and machine alongside the JSON output when comparing runs. Compare values only across matching seeds, game count, tick count, build type, and workload. The baseline is serial; parallel worker scaling and Python transport overhead require separate future benchmark cases.
