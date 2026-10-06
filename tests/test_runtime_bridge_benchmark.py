import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


# {
#   責務: [RuntimeBridgeBenchmarkTests: 実C++ bridgeとbenchmarkのtrace一致を検証する]
#   フィールド: [CIが提供するbridge DLLとnative benchmark executable]
#   処理: [1: 同一seedのnative・serial・batch・worker経路を実行する 2: traceとthroughput結果を確認する]
# }
class RuntimeBridgeBenchmarkTests(unittest.TestCase):
    # {
    #   責務: [test_native_and_python_workloads_match_checksums: nativeとPython bridgeのtrace一致およびworker scalingを検証する]
    #   処理: [1: 実build artifactでbounded benchmarkを起動する 2: native parityとworker別trace一致を確認する]
    #   引数: [なし]
    #   戻り値: [unittest assertion result]
    #   省略: [bridge artifactがないlocal環境ではskipする]
    # }
    def test_native_and_python_workloads_match_checksums(self):
        library = os.environ.get("KADOKA_TETRIS_BRIDGE")
        native = os.environ.get("KADOKA_TETRIS_NATIVE_BENCHMARK")
        if not library or not native:
            raise unittest.SkipTest("CI must provide both built runtime benchmark artifacts")
        root = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(root / "src")
        completed = subprocess.run(
            [
                sys.executable, "-m", "tetris.benchmark.runtime_bridge_benchmark",
                "--library", library, "--native-executable", native,
                "--seed", "123", "--games", "3", "--ticks", "96",
                "--warmup", "0", "--repeats", "2", "--workers", "2",
            ],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=45,
        )
        report = json.loads(completed.stdout)
        self.assertTrue(report["matching_trace"])
        self.assertEqual(report["native"]["trace_checksum"], report["python_bridge"]["trace_checksum"])
        self.assertEqual(report["native"]["trace_checksum"], report["python_serial_bridge"]["trace_checksum"])
        self.assertEqual(report["configuration"]["games"], 3)
        self.assertGreater(report["native"]["median_decision_roundtrips_per_second"], 0)
        self.assertGreater(report["python_bridge"]["median_decision_roundtrips_per_second"], 0)
        self.assertGreater(report["batch_speedup_vs_serial_bridge"], 0)
        self.assertEqual(report["worker_scaling"]["workers_compared"], [1, 2])
        self.assertTrue(report["worker_scaling"]["matching_worker_traces"])
        self.assertTrue(report["worker_scaling"]["scaling_available"])
        self.assertGreater(report["worker_scaling"]["parallel_games_per_second"], 0)
        self.assertGreater(report["worker_scaling"]["speedup"], 0)
