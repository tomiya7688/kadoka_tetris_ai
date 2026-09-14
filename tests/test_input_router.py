import unittest

from tetris.application import InputAction, InputRouter, TickEngine
from tetris.core import GameState


class InputRouterTests(unittest.TestCase):
    def test_assigns_sequences_on_current_tick(self):
        engine = TickEngine({0: GameState(seed=1)})
        router = InputRouter(engine)

        first = router.submit(InputAction(0, "move_left"))
        second = router.submit(InputAction(0, "rotate_cw"))

        self.assertEqual(first.tick, 0)
        self.assertEqual(second.tick, 0)
        self.assertEqual(first.sequence, 0)
        self.assertEqual(second.sequence, 1)

    def test_keyboard_and_api_style_actions_share_one_sequence(self):
        engine = TickEngine({0: GameState(seed=2)})
        router = InputRouter(engine)

        keyboard = router.submit(InputAction(0, "move_right"))
        api = router.submit(InputAction(0, "hard_drop"))

        self.assertEqual((keyboard.sequence, api.sequence), (0, 1))
        engine.advance()
        self.assertEqual(engine.tick, 1)

    def test_unknown_player_is_rejected_by_engine(self):
        engine = TickEngine({0: GameState(seed=3)})
        router = InputRouter(engine)

        with self.assertRaisesRegex(ValueError, "unknown player"):
            router.submit(InputAction(1, "move_left"))


if __name__ == "__main__":
    unittest.main()
