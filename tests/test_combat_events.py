import unittest

from tetris.application import Command, VersusSession, attack_for_clear, attack_for_event
from tetris.core import ActivePiece, GameState, PieceType, Tetromino


def _lock_single_cell(game: GameState, x: int, y: int) -> None:
    game.board.lock(Tetromino(PieceType.O, ((0, 0),)), (x, y))


def _prepare_t_spin_single(game: GameState) -> None:
    if game.board.width != 4 or game.board.height != 4:
        raise ValueError("test setup requires a 4x4 board")

    # Three occupied corners around the final T pivot at (1, 1).
    for x, y in ((0, 0), (2, 0), (0, 2)):
        _lock_single_cell(game, x, y)

    # The T fills x=0..2 on row 1; x=3 completes the line.
    _lock_single_cell(game, 3, 1)
    game.active = ActivePiece(PieceType.T, x=0, y=0, rotation=3)
    game.game_over = False


class CombatEventTests(unittest.TestCase):
    def test_t_spin_single_creates_normalized_lock_event(self):
        game = GameState(seed=1, width=4, visible_height=4, hidden_rows=0)
        _prepare_t_spin_single(game)

        self.assertTrue(game.rotate(1))
        event = game.lock()

        self.assertEqual(event.lock_id, 1)
        self.assertEqual(event.piece, PieceType.T)
        self.assertEqual(event.lines, 1)
        self.assertTrue(event.t_spin)
        self.assertEqual(event.combo, 1)
        self.assertFalse(event.back_to_back)
        self.assertFalse(event.perfect_clear)
        self.assertEqual(attack_for_event(event), 2)

    def test_horizontal_move_after_rotation_invalidates_t_spin(self):
        game = GameState(seed=2, width=6, visible_height=6, hidden_rows=0)
        game.active = ActivePiece(PieceType.T, x=1, y=1, rotation=3)
        for x, y in ((1, 1), (3, 1), (1, 3)):
            _lock_single_cell(game, x, y)

        self.assertTrue(game.rotate(1))
        self.assertTrue(game.move(1, 0))
        event = game.lock()

        self.assertFalse(event.t_spin)

    def test_attack_table_supports_t_spin_b2b_combo_and_perfect_clear(self):
        self.assertEqual(attack_for_clear(1, t_spin=True), 2)
        self.assertEqual(
            attack_for_clear(2, combo=3, back_to_back=True, t_spin=True),
            7,
        )
        self.assertEqual(attack_for_clear(4, perfect_clear=True), 14)
        self.assertEqual(attack_for_clear(0, combo=5), 0)

    def test_versus_session_queues_attack_from_lock_event(self):
        game_a = GameState(seed=3, width=4, visible_height=4, hidden_rows=0)
        game_b = GameState(seed=4, width=4, visible_height=4, hidden_rows=0)
        _prepare_t_spin_single(game_a)
        session = VersusSession({0: game_a, 1: game_b})

        session.submit(Command(0, 0, 0, "rotate_cw"))
        session.submit(Command(0, 0, 1, "hard_drop"))
        session.advance()

        self.assertEqual(session.results[0].t_spins, 1)
        self.assertEqual(session.results[0].lines_cleared, 1)
        self.assertEqual(session.results[0].outgoing_attack, 2)
        self.assertEqual(session.results[1].incoming_garbage, 2)

    def test_simultaneous_attack_tracks_cancellation(self):
        game_a = GameState(seed=5)
        game_b = GameState(seed=6)
        session = VersusSession({0: game_a, 1: game_b})

        session.queue_attack(0, 4)
        session.queue_attack(1, 2)
        session.advance()

        self.assertEqual(session.results[0].incoming_garbage, 0)
        self.assertEqual(session.results[1].incoming_garbage, 2)
        self.assertEqual(session.results[0].cancelled_garbage, 2)
        self.assertEqual(session.results[1].cancelled_garbage, 2)
        self.assertEqual(session.results[0].outgoing_attack, 4)
        self.assertEqual(session.results[1].outgoing_attack, 2)


if __name__ == "__main__":
    unittest.main()
