import unittest

from tetris.application import Command, VersusSession
from tetris.core import Board, GameState, PieceType, Tetromino


def _single_cell() -> Tetromino:
    return Tetromino(PieceType.O, ((0, 0),))


def _row_occupancy(board: Board, y: int) -> tuple[bool, ...]:
    return tuple(board.occupied(x, y) for x in range(board.width))


def _hole_column(board: Board, y: int) -> int:
    holes = [x for x in range(board.width) if not board.occupied(x, y)]
    if len(holes) != 1:
        raise AssertionError(f"expected exactly one garbage hole, got {holes}")
    return holes[0]


class GarbageTests(unittest.TestCase):
    def test_board_garbage_raises_stack_and_adds_one_hole_rows(self):
        board = Board(width=4, visible_height=4, hidden_rows=0)
        board.lock(_single_cell(), (1, 3))

        overflow = board.add_garbage((0, 2))

        self.assertFalse(overflow)
        self.assertTrue(board.occupied(1, 1))
        self.assertEqual(_row_occupancy(board, 2), (False, True, True, True))
        self.assertEqual(_row_occupancy(board, 3), (True, True, False, True))

    def test_board_reports_cells_pushed_above_top(self):
        board = Board(width=4, visible_height=4, hidden_rows=0)
        board.lock(_single_cell(), (0, 0))

        self.assertTrue(board.add_garbage((1,)))

    def test_game_state_tops_out_when_garbage_overflows(self):
        game = GameState(seed=1, width=4, visible_height=4, hidden_rows=0)
        game.board.lock(_single_cell(), (0, 0))
        game.game_over = False

        overflow = game.add_garbage((1,))

        self.assertTrue(overflow)
        self.assertTrue(game.game_over)

    def test_pending_garbage_waits_until_defender_locks(self):
        game_a = GameState(seed=2)
        game_b = GameState(seed=3)
        session = VersusSession({0: game_a, 1: game_b}, garbage_seed=99)

        session.queue_attack(0, 2)
        session.advance()

        self.assertEqual(session.results[1].incoming_garbage, 2)
        self.assertEqual(session.results[1].garbage_received, 0)

        session.submit(Command(1, session.engine.tick, 0, "hard_drop"))
        session.advance()

        self.assertEqual(session.results[1].incoming_garbage, 0)
        self.assertEqual(session.results[1].garbage_received, 2)
        for y in (game_b.board.height - 2, game_b.board.height - 1):
            self.assertEqual(sum(_row_occupancy(game_b.board, y)), game_b.board.width - 1)

    def test_same_garbage_seed_produces_same_hole_pattern(self):
        def receive(seed: int) -> tuple[int, int, int]:
            defender = GameState(seed=10)
            session = VersusSession(
                {0: GameState(seed=9), 1: defender},
                garbage_seed=seed,
            )
            session.queue_attack(0, 3)
            session.submit(Command(1, 0, 0, "hard_drop"))
            session.advance()
            start = defender.board.height - 3
            return tuple(
                _hole_column(defender.board, y)
                for y in range(start, defender.board.height)
            )

        self.assertEqual(receive(1234), receive(1234))

    def test_cancellation_reduces_garbage_before_delivery(self):
        game_a = GameState(seed=11)
        game_b = GameState(seed=12)
        session = VersusSession({0: game_a, 1: game_b}, garbage_seed=7)

        session.queue_attack(0, 4)
        session.queue_attack(1, 2)
        session.advance()
        self.assertEqual(session.results[1].incoming_garbage, 2)

        session.submit(Command(1, session.engine.tick, 0, "hard_drop"))
        session.advance()

        self.assertEqual(session.results[1].garbage_received, 2)
        self.assertEqual(session.results[1].incoming_garbage, 0)


if __name__ == "__main__":
    unittest.main()
