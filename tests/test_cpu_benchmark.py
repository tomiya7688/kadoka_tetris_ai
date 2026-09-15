import json
import tempfile
import unittest
from pathlib import Path

from tetris.benchmark import (
    BENCHMARK_SCHEMA_VERSION,
    StandardCpuBenchmark,
    StandardCpuComparison,
    VisibleBoardMetrics,
)
from tetris.main import main
from tetris.observation import BoardObservation


class CpuBenchmarkTests(unittest.TestCase):
    def test_visible_board_metrics_count_height_holes_and_bumpiness(self):
        board = BoardObservation(
            width=3,
            height=5,
            locked_cells=frozenset({(0, 2), (0, 4), (1, 4)}),
            active_cells=frozenset(),
        )

        metrics = VisibleBoardMetrics.from_observation(board)

        self.assertEqual(metrics.stack_height, 3)
        self.assertEqual(metrics.holes, 1)
        self.assertEqual(metrics.bumpiness, 3)

    def test_easy_benchmark_reaches_small_piece_limit_headlessly(self):
        report = StandardCpuBenchmark("easy", max_pieces=3).run(
            game_count=1,
            seed=31,
        )
        game = report.games[0]

        self.assertEqual(game.placements, 3)
        self.assertTrue(game.reached_piece_limit)
        self.assertFalse(game.tick_limit_reached)
        self.assertGreater(game.decision_calls, 0)
        self.assertGreaterEqual(game.decision_seconds, 0.0)

    def test_report_aggregates_multiple_reproducible_seeds(self):
        report = StandardCpuBenchmark("easy", max_pieces=2).run(
            game_count=2,
            seed=40,
        )
        payload = report.to_dict()

        self.assertEqual([game.seed for game in report.games], [40, 41])
        self.assertEqual(payload["benchmark_schema_version"], BENCHMARK_SCHEMA_VERSION)
        self.assertEqual(payload["mode"], "single-level")
        self.assertEqual(payload["game_count"], 2)
        self.assertEqual(payload["summary"]["total_placements"], 4)
        self.assertIn("decision_ms_per_placement", payload["summary"])
        self.assertEqual(payload["profile"]["implementation_id"], "standard-visible-v1")
        self.assertEqual(payload["profile"]["search_depth"], 1)

    def test_comparison_uses_identical_seed_range_for_every_level(self):
        report = StandardCpuComparison(max_pieces=1).run(
            game_count=2,
            seed=60,
        )
        payload = report.to_dict()

        self.assertEqual(payload["mode"], "comparison")
        self.assertEqual(set(payload["levels"]), {"easy", "normal", "hard"})
        for level_report in report.reports:
            self.assertEqual([game.seed for game in level_report.games], [60, 61])
            self.assertEqual(level_report.max_pieces, 1)

    def test_cli_writes_json_report_without_opening_gui(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "benchmark.json"

            exit_code = main(
                [
                    "--benchmark-cpu",
                    "easy",
                    "--benchmark-games",
                    "1",
                    "--benchmark-max-pieces",
                    "2",
                    "--benchmark-seed",
                    "50",
                    "--benchmark-output",
                    str(output),
                    "--data-root",
                    str(root),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["level"], "easy")
            self.assertEqual(payload["game_count"], 1)
            self.assertEqual(payload["games"][0]["seed"], 50)
            self.assertEqual(payload["games"][0]["placements"], 2)

    def test_cli_all_writes_same_seed_comparison_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "comparison.json"

            exit_code = main(
                [
                    "--benchmark-cpu",
                    "all",
                    "--benchmark-games",
                    "1",
                    "--benchmark-max-pieces",
                    "1",
                    "--benchmark-seed",
                    "70",
                    "--benchmark-output",
                    str(output),
                    "--data-root",
                    str(root),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "comparison")
            self.assertEqual(payload["seed_start"], 70)
            self.assertEqual(set(payload["summary_by_level"]), {"easy", "normal", "hard"})
            for level in ("easy", "normal", "hard"):
                self.assertEqual(payload["levels"][level]["games"][0]["seed"], 70)

    def test_invalid_benchmark_limits_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "max_pieces"):
            StandardCpuBenchmark("easy", max_pieces=0)
        with self.assertRaisesRegex(ValueError, "game_count"):
            StandardCpuBenchmark("easy").run(game_count=0)


if __name__ == "__main__":
    unittest.main()
