import unittest

from tetris.core import GameState, PieceType, Tetromino
from tetris.observation import BoardObservation, VisibleBoardObserver


class ObservationTests(unittest.TestCase):
    def test_hidden_locked_cells_are_not_exposed(self):
        state = GameState(seed=1)
        single = Tetromino(PieceType.O, ((0, 0),))
        state.board.lock(single, (0, 0))
        state.board.lock(single, (1, state.board.hidden_rows))

        observation = VisibleBoardObserver().observe(state)

        self.assertNotIn((0, 0), observation.locked_cells)
        self.assertIn((1, 0), observation.locked_cells)
        self.assertEqual(
            observation.height,
            state.board.height - state.board.hidden_rows,
        )

    def test_active_cells_are_translated_and_clipped_to_visible_field(self):
        state = GameState(seed=2)
        state.active.x = 3
        state.active.y = state.board.hidden_rows - 1

        observation = VisibleBoardObserver().observe(state)

        self.assertTrue(observation.active_cells)
        self.assertTrue(all(y >= 0 for _, y in observation.active_cells))
        self.assertTrue(all(y < observation.height for _, y in observation.active_cells))

    def test_observation_contains_no_engine_or_rng_reference(self):
        observation = VisibleBoardObserver().observe(GameState(seed=3))

        self.assertFalse(hasattr(observation, "bag"))
        self.assertFalse(hasattr(observation, "hold"))
        self.assertFalse(hasattr(observation, "game_state"))
        self.assertFalse(hasattr(observation, "rng"))

    def test_observation_copies_mutable_input_cells(self):
        locked_cells = {(1, 2)}
        observation = BoardObservation(
            width=10,
            height=20,
            locked_cells=locked_cells,
            active_cells=set(),
        )

        locked_cells.add((2, 3))

        self.assertEqual(observation.locked_cells, frozenset({(1, 2)}))
        self.assertIsInstance(observation.active_cells, frozenset)

    def test_observation_rejects_out_of_bounds_cells(self):
        with self.assertRaisesRegex(ValueError, "out of bounds"):
            BoardObservation(
                width=10,
                height=20,
                locked_cells=frozenset({(10, 0)}),
                active_cells=frozenset(),
            )


if __name__ == "__main__":
    unittest.main()
