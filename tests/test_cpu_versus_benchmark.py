import json
import tempfile
import unittest
from pathlib import Path

from tetris.benchmark import (
    VERSUS_BENCHMARK_SCHEMA_VERSION,
    StandardCpuVersusBenchmark,
)
from tetris.main import build_parser, main


class StandardCpuVersusBenchmarkTests(unittest.TestCase):
    def test_one_seed_runs_two_mirrored_legs(self):
        report = StandardCpuVersusBenchmark(
            "easy",
            "normal",
            max_pieces_per_player=1,
        ).run(game_count=1, seed=100)

        self.assertEqual(len(report.legs), 2)
        normal_leg, mirrored_leg = report.legs
        self.assertFalse(normal_leg.mirrored)
        self.assertTrue(mirrored_leg.mirrored)
        self.assertEqual(normal_leg.seed, 100)
        self.assertEqual(mirrored_leg.seed, 100)
        self.assertEqual(normal_leg.garbage_seed, 100)
        self.assertEqual(mirrored_leg.garbage_seed, 100)
        self.assertEqual(normal_leg.a.player, 0)
        self.assertEqual(normal_leg.b.player, 1)
        self.assertEqual(mirrored_leg.a.player, 1)
        self.assertEqual(mirrored_leg.b.player, 0)

    def test_report_contains_combat_and_mode_metrics(self):
        payload = StandardCpuVersusBenchmark(
            "hard",
            "hard",
            max_pieces_per_player=1,
        ).run(game_count=1, seed=101).to_dict()

        self.assertEqual(
            payload["versus_benchmark_schema_version"],
            VERSUS_BENCHMARK_SCHEMA_VERSION,
        )
        self.assertEqual(payload["mode"], "cpu-versus")
        self.assertEqual(payload["mirrored_legs_per_seed"], 2)
        self.assertEqual(set(payload["summary"]), {"a", "b"})
        for competitor in ("a", "b"):
            summary = payload["summary"][competitor]
            self.assertIn("total_attack", summary)
            self.assertIn("total_garbage_received", summary)
            self.assertIn("decision_ms_per_placement", summary)
            self.assertEqual(
                set(summary["mode_plan_counts"]),
                {"neutral", "defense", "pressure"},
            )

    def test_seed_range_is_reproducible_and_sequential(self):
        report = StandardCpuVersusBenchmark(
            "easy",
            "easy",
            max_pieces_per_player=1,
        ).run(game_count=2, seed=110)

        self.assertEqual([leg.seed for leg in report.legs], [110, 110, 111, 111])

    def test_cli_writes_versus_json_without_gui(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "versus.json"

            exit_code = main(
                [
                    "--benchmark-versus",
                    "easy",
                    "normal",
                    "--benchmark-games",
                    "1",
                    "--benchmark-max-pieces",
                    "1",
                    "--benchmark-seed",
                    "120",
                    "--benchmark-output",
                    str(output),
                    "--data-root",
                    str(root),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "cpu-versus")
            self.assertEqual(payload["level_a"], "easy")
            self.assertEqual(payload["level_b"], "normal")
            self.assertEqual(payload["seed_start"], 120)
            self.assertEqual(len(payload["legs"]), 2)

    def test_benchmark_modes_are_mutually_exclusive(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "--benchmark-cpu",
                    "easy",
                    "--benchmark-versus",
                    "easy",
                    "hard",
                ]
            )

    def test_invalid_piece_limit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "max_pieces_per_player"):
            StandardCpuVersusBenchmark("easy", "normal", max_pieces_per_player=0)


if __name__ == "__main__":
    unittest.main()
