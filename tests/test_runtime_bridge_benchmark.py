import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class RuntimeBridgeBenchmarkTests(unittest.TestCase):
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
                "--seed", "123", "--games", "2", "--ticks", "96",
                "--warmup", "0", "--repeats", "2",
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
        self.assertEqual(report["configuration"]["games"], 2)
        self.assertGreater(report["native"]["median_decision_roundtrips_per_second"], 0)
        self.assertGreater(report["python_bridge"]["median_decision_roundtrips_per_second"], 0)
        self.assertGreater(report["batch_speedup_vs_serial_bridge"], 0)
