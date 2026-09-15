import unittest

from tetris.main import build_parser


class VersusCliTests(unittest.TestCase):
    def test_versus_mode_defaults_to_two_human_players(self):
        args = build_parser().parse_args(["--versus"])

        self.assertTrue(args.versus)
        self.assertEqual(args.versus_cpu_level, "off")
        self.assertEqual(args.versus_garbage_seed, 0)

    def test_versus_cpu_level_and_garbage_seed_are_selectable(self):
        args = build_parser().parse_args(
            [
                "--versus",
                "--versus-cpu-level",
                "hard",
                "--versus-garbage-seed",
                "123",
            ]
        )

        self.assertEqual(args.versus_cpu_level, "hard")
        self.assertEqual(args.versus_garbage_seed, 123)


if __name__ == "__main__":
    unittest.main()
