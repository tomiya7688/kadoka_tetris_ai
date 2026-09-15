from .active_piece import ActivePiece
from .bag import SevenBag
from .board import Board
from .lock_event import LockEvent
from .tetromino import PieceType, Tetromino


_T_PIVOTS = {
    0: (1, 1),
    1: (0, 1),
    2: (1, 0),
    3: (1, 1),
}


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
        self.combo = 0
        self.back_to_back_active = False
        self.pieces_locked = 0
        self.last_lock_event: LockEvent | None = None
        self._last_rotation_successful = False
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
        self._last_rotation_successful = False
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
            if dx != 0:
                self._last_rotation_successful = False
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
            self._last_rotation_successful = True
            return True
        for dx in (-1, 1, -2, 2):
            candidate.x = self.active.x + dx
            if self._can(candidate):
                self.active = candidate
                self._last_rotation_successful = True
                return True
        return False

    def hard_drop(self):
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.lock()
        return distance

    def lock(self):
        locked_piece = self.active
        t_spin = self._is_t_spin(locked_piece)
        self.board.lock(
            Tetromino(locked_piece.kind, locked_piece.cells()),
            (locked_piece.x, locked_piece.y),
        )
        cleared_lines = self.board.clear_full_rows()
        self.lines += cleared_lines
        self.pieces_locked += 1

        if cleared_lines > 0:
            self.combo += 1
        else:
            self.combo = 0

        difficult_clear = cleared_lines == 4 or (t_spin and cleared_lines > 0)
        back_to_back = difficult_clear and self.back_to_back_active
        if difficult_clear:
            self.back_to_back_active = True
        elif cleared_lines > 0:
            self.back_to_back_active = False

        perfect_clear = cleared_lines > 0 and not any(self.board.cells())
        self.last_lock_event = LockEvent(
            lock_id=self.pieces_locked,
            piece=locked_piece.kind,
            lines=cleared_lines,
            t_spin=t_spin,
            combo=self.combo,
            back_to_back=back_to_back,
            perfect_clear=perfect_clear,
        )

        self.hold_used = False
        self.spawn()
        return self.last_lock_event

    def hold_piece(self):
        if self.hold_used:
            return False
        old = self.hold
        self.hold = self.active.kind
        self.hold_used = True
        self._last_rotation_successful = False
        if old is None:
            self.spawn()
        else:
            self.active = ActivePiece(old, (self.board.width - 4) // 2, 0)
        if not self._can(self.active):
            self.game_over = True
        return True

    def _is_t_spin(self, piece: ActivePiece) -> bool:
        if piece.kind != PieceType.T or not self._last_rotation_successful:
            return False

        pivot_x, pivot_y = _T_PIVOTS[piece.rotation % 4]
        center_x = piece.x + pivot_x
        center_y = piece.y + pivot_y
        occupied_corners = 0
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x = center_x + dx
            y = center_y + dy
            if x < 0 or x >= self.board.width or y < 0 or y >= self.board.height:
                occupied_corners += 1
            elif self.board.occupied(x, y):
                occupied_corners += 1
        return occupied_corners >= 3
