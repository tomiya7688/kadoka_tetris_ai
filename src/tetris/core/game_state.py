from .active_piece import ActivePiece
from .bag import SevenBag
from .board import Board
from .tetromino import PieceType, Tetromino


class GameState:
    def __init__(
        self,
        seed=None,
        width=10,
        visible_height=20,
        hidden_rows=2,
        next_count=5,
    ):
        if not isinstance(next_count, int) or isinstance(next_count, bool) or next_count < 0:
            raise ValueError("next_count must be a nonnegative integer")

        self.board = Board(width, visible_height, hidden_rows)
        self.bag = SevenBag(seed)
        self.next_count = next_count
        self._next_queue = [next(self.bag) for _ in range(next_count)]
        self.active = None
        self.hold = None
        self.hold_used = False
        self.game_over = False
        self.lines = 0
        self.spawn()

    @property
    def next_pieces(self) -> tuple[PieceType, ...]:
        return tuple(self._next_queue)

    def spawn(self):
        if self._next_queue:
            kind = self._next_queue.pop(0)
            self._next_queue.append(next(self.bag))
        else:
            kind = next(self.bag)

        self.active = ActivePiece(kind, (self.board.width - 4) // 2, 0)
        if not self.board.can_place(
            Tetromino(self.active.kind, self.active.cells()),
            (self.active.x, self.active.y),
        ):
            self.game_over = True

    def _can(self, piece):
        return self.board.can_place(
            Tetromino(piece.kind, piece.cells()),
            (piece.x, piece.y),
        )

    def move(self, dx, dy=0):
        candidate = ActivePiece(
            self.active.kind,
            self.active.x + dx,
            self.active.y + dy,
            self.active.rotation,
        )
        if self._can(candidate):
            self.active = candidate
            return True
        return False

    def rotate(self, direction=1):
        candidate = ActivePiece(
            self.active.kind,
            self.active.x,
            self.active.y,
            self.active.rotation + direction,
        )
        if self._can(candidate):
            self.active = candidate
            return True
        for dx in (-1, 1, -2, 2):
            candidate.x = self.active.x + dx
            if self._can(candidate):
                self.active = candidate
                return True
        return False

    def hard_drop(self):
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.lock()
        return distance

    def lock(self):
        self.board.lock(
            Tetromino(self.active.kind, self.active.cells()),
            (self.active.x, self.active.y),
        )
        self.lines += self.board.clear_full_rows()
        self.hold_used = False
        self.spawn()

    def hold_piece(self):
        if self.hold_used:
            return False
        old = self.hold
        self.hold = self.active.kind
        self.hold_used = True
        if old is None:
            self.spawn()
        else:
            self.active = ActivePiece(old, (self.board.width - 4) // 2, 0)
        if not self._can(self.active):
            self.game_over = True
        return True
