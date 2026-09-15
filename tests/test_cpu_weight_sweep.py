import json
import math
import tempfile
import unittest
from pathlib import Path

from tetris.benchmark import StandardCpuWeightSweep
from tetris.cpu import VisibleBoardWeights
from tetris.main import build_parser, main


class CpuWeightSweepTests(unittest.TestCase):
    def test_sweep_builds_baseline_and_two_candidates_per_weight(self):
        report = StandardCpuWeightSweep(
            "easy",
            max_pieces=1,
            step_fraction=0.25,
        ).run(game_count=1, seed=80)

        self.assertEqual(len(report.candidates), 13)
        self.assertEqual(report.candidates[0].label, "baseline")
        self.assertTrue(
            all(candidate.report.games[0].seed == 80 for candidate in report.candidates)
        )

        by_label = {candidate.label: candidate for candidate in report.candidates}
        self.assertEqual(by_label["holes:0.75x"].baseline_value, -7.0)
        self.assertEqual(by_label["holes:0.75x"].candidate_value, -5.25)
        self.assertEqual(by_label["holes:1.25x"].candidate_value, -8.75)
        self.assertEqual(by_label["holes:1.25x"].multiplier, 1.25)

    def test_zero_weight_uses_absolute_step_candidates(self):
        report = StandardCpuWeightSweep(
            "easy",
            max_pieces=1,
            base_weights=VisibleBoardWeights(holes=0.0),
            step_fraction=0.2,
        ).run(game_count=1, seed=81)
        by_label = {candidate.label: candidate for candidate in report.candidates}

        self.assertEqual(by_label["holes:-step"].candidate_value, -0.2)
        self.assertEqual(by_label["holes:+step"].candidate_value, 0.2)
        self.assertIsNone(by_label["holes:-step"].multiplier)

    def test_sweep_report_contains_quick_summaries_and_full_reports(self):
        payload = StandardCpuWeightSweep(
            "easy",
            max_pieces=1,
        ).run(game_count=1, seed=82).to_dict()

        self.assertEqual(payload["mode"], "weight-sweep")
        self.assertEqual(payload["candidate_count"], 13)
        self.assertIn("baseline", payload["summary_by_candidate"])
        baseline = payload["candidates"][0]
        self.assertEqual(baseline["report"]["games"][0]["seed"], 82)

    def test_invalid_step_fraction_is_rejected(self):
        for value in (0.0, -0.1, 1.1, math.nan):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "step_fraction"):
                    StandardCpuWeightSweep("easy", step_fraction=value)

    def test_cli_writes_default_weight_sweep_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            exit_code = main(
                [
                    "--benchmark-weight-sweep",
                    "easy",
                    "--benchmark-games",
                    "1",
                    "--benchmark-max-pieces",
                    "1",
                    "--benchmark-seed",
                    "90",
                    "--benchmark-weight-step",
                    "0.1",
                    "--data-root",
                    str(root),
                ]
            )

            self.assertEqual(exit_code, 0)
            output = root / "UserData" / "Logs" / "cpu-weight-sweep.json"
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "weight-sweep")
            self.assertEqual(payload["step_fraction"], 0.1)
            self.assertEqual(payload["candidate_count"], 13)
            self.assertEqual(payload["candidates"][0]["report"]["games"][0]["seed"], 90)

    def test_benchmark_modes_are_mutually_exclusive(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "--benchmark-cpu",
                    "easy",
                    "--benchmark-weight-sweep",
                    "easy",
                ]
            )


if __name__ == "__main__":
    unittest.main()
