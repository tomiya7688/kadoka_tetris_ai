import unittest

from tetris.core import GameState
from tetris.observation import VersusPlayerObservation, VisibleVersusObserver


class VisibleVersusObservationTests(unittest.TestCase):
    def test_observation_matches_displayed_player_states_and_garbage_meters(self):
        own = GameState(seed=1)
        opponent = GameState(seed=2)
        observer = VisibleVersusObserver()

        observation = observer.observe(
            own,
            opponent,
            incoming_garbage=3,
            opponent_incoming_garbage=5,
        )

        self.assertIsInstance(observation, VersusPlayerObservation)
        self.assertEqual(observation.own.current_piece, own.active.kind)
        self.assertEqual(observation.own.hold_piece, own.hold)
        self.assertEqual(observation.own.next_pieces, own.next_pieces)
        self.assertEqual(observation.opponent.current_piece, opponent.active.kind)
        self.assertEqual(observation.opponent.next_pieces, opponent.next_pieces)
        self.assertEqual(observation.incoming_garbage, 3)
        self.assertEqual(observation.opponent_incoming_garbage, 5)

    def test_versus_observation_does_not_expose_combat_or_rng_internals(self):
        observation = VisibleVersusObserver().observe(
            GameState(seed=3),
            GameState(seed=4),
            incoming_garbage=2,
            opponent_incoming_garbage=1,
        )

        for forbidden in (
            "game_state",
            "bag",
            "rng",
            "last_lock_event",
            "pieces_locked",
            "outgoing_attack",
            "cancelled_garbage",
        ):
            self.assertFalse(hasattr(observation, forbidden))
            self.assertFalse(hasattr(observation.own, forbidden))
            self.assertFalse(hasattr(observation.opponent, forbidden))

    def test_garbage_meter_values_are_validated(self):
        own = GameState(seed=5)
        opponent = GameState(seed=6)
        observer = VisibleVersusObserver()

        with self.assertRaisesRegex(ValueError, "incoming_garbage"):
            observer.observe(own, opponent, -1, 0)
        with self.assertRaisesRegex(ValueError, "opponent_incoming_garbage"):
            observer.observe(own, opponent, 0, True)


if __name__ == "__main__":
    unittest.main()
