import unittest

from tetris.core import GameState
from tetris.cpu import VisibleCpuController
from tetris.observation import PlayerObservation, VisiblePlayerObserver


class RecordingStrategy:
    def __init__(self, action="move_left"):
        self.action = action
        self.observation = None

    def choose(self, observation: PlayerObservation) -> str | None:
        self.observation = observation
        return self.action


class VisibleObservationMetadataTests(unittest.TestCase):
    def test_next_queue_advances_with_spawned_piece(self):
        state = GameState(seed=7, next_count=5)
        visible_next = state.next_pieces

        state.hard_drop()

        self.assertEqual(state.active.kind, visible_next[0])
        self.assertEqual(len(state.next_pieces), 5)
        self.assertEqual(state.next_pieces[:-1], visible_next[1:])

    def test_hold_without_existing_piece_consumes_visible_next(self):
        state = GameState(seed=11, next_count=5)
        first_active = state.active.kind
        visible_next = state.next_pieces

        self.assertTrue(state.hold_piece())

        self.assertEqual(state.hold, first_active)
        self.assertEqual(state.active.kind, visible_next[0])
        self.assertEqual(state.next_pieces[:-1], visible_next[1:])

    def test_player_observation_matches_currently_visible_metadata(self):
        state = GameState(seed=13, next_count=5)
        state.hold_piece()

        observation = VisiblePlayerObserver().observe(state)

        self.assertEqual(observation.current_piece, state.active.kind)
        self.assertEqual(observation.hold_piece, state.hold)
        self.assertEqual(observation.next_pieces, state.next_pieces)
        self.assertIsInstance(observation.next_pieces, tuple)

    def test_cpu_strategy_receives_observation_not_game_state(self):
        state = GameState(seed=17)
        strategy = RecordingStrategy("move_right")
        controller = VisibleCpuController(0, strategy)

        action = controller.choose_action(state)

        self.assertEqual(action.player, 0)
        self.assertEqual(action.action, "move_right")
        self.assertIsInstance(strategy.observation, PlayerObservation)
        self.assertFalse(hasattr(strategy.observation, "bag"))
        self.assertFalse(hasattr(strategy.observation, "rng"))
        self.assertFalse(hasattr(strategy.observation, "game_state"))

    def test_cpu_invalid_action_is_rejected_by_shared_input_model(self):
        controller = VisibleCpuController(0, RecordingStrategy("teleport"))

        with self.assertRaisesRegex(ValueError, "unknown action"):
            controller.choose_action(GameState(seed=19))


if __name__ == "__main__":
    unittest.main()
