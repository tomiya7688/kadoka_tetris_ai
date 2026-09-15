import unittest

from tetris.benchmark import BENCHMARK_SCHEMA_VERSION, StandardCpuBenchmark


class CpuBenchmarkCombatMetricTests(unittest.TestCase):
    def test_benchmark_schema_records_combat_metrics(self):
        report = StandardCpuBenchmark("easy", max_pieces=4).run(
            game_count=2,
            seed=120,
        )
        payload = report.to_dict()

        self.assertEqual(BENCHMARK_SCHEMA_VERSION, 3)
        self.assertEqual(payload["benchmark_schema_version"], 3)
        for game in payload["games"]:
            self.assertIn("attack_generated", game)
            self.assertIn("attack_per_placement", game)
            self.assertIn("attack_per_line", game)
            self.assertIn("t_spins", game)
            self.assertIn("perfect_clears", game)
            self.assertIn("back_to_back_clears", game)
            self.assertIn("max_combo", game)
            self.assertGreaterEqual(game["attack_generated"], 0)
            self.assertGreaterEqual(game["max_combo"], 0)

        summary = payload["summary"]
        self.assertEqual(
            summary["total_attack_generated"],
            sum(game["attack_generated"] for game in payload["games"]),
        )
        self.assertEqual(
            summary["total_t_spins"],
            sum(game["t_spins"] for game in payload["games"]),
        )
        self.assertIn("attack_per_placement", summary)
        self.assertIn("attack_per_line", summary)


if __name__ == "__main__":
    unittest.main()
