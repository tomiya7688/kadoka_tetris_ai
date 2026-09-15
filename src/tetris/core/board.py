from .tetromino import Tetromino


class Board:
    def __init__(self, width=10, visible_height=20, hidden_rows=2):
        if width <= 0 or visible_height <= 0 or hidden_rows < 0:
            raise ValueError("invalid dimensions")
        self.width = width
        self.height = visible_height + hidden_rows
        self.hidden_rows = hidden_rows
        self._cells = [[False] * width for _ in range(self.height)]

    def occupied(self, x, y):
        return self._cells[y][x]

    def can_place(self, piece, origin):
        ox, oy = origin
        for x, y in piece.cells:
            px, py = ox + x, oy + y
            if (
                px < 0
                or px >= self.width
                or py < 0
                or py >= self.height
                or self._cells[py][px]
            ):
                return False
        return True

    def lock(self, piece, origin):
        if not self.can_place(piece, origin):
            raise ValueError("piece cannot be locked")
        ox, oy = origin
        for x, y in piece.cells:
            self._cells[oy + y][ox + x] = True

    def clear_full_rows(self):
        keep = [row for row in self._cells if not all(row)]
        cleared = self.height - len(keep)
        self._cells = [[False] * self.width for _ in range(cleared)] + keep
        return cleared

    def add_garbage(self, hole_columns) -> bool:
        """Raise the stack and append garbage rows with one hole each.

        Returns True when occupied cells were pushed above the top of the field, or
        when more garbage rows were inserted than the field can physically contain.
        """
        holes = tuple(hole_columns)
        for hole in holes:
            if (
                not isinstance(hole, int)
                or isinstance(hole, bool)
                or hole < 0
                or hole >= self.width
            ):
                raise ValueError("garbage hole must be a valid column")
        if not holes:
            return False

        count = len(holes)
        dropped_count = min(count, self.height)
        overflow = count > self.height or any(
            any(row) for row in self._cells[:dropped_count]
        )

        if count >= self.height:
            kept_rows = []
            visible_holes = holes[-self.height :]
        else:
            kept_rows = self._cells[count:]
            visible_holes = holes

        garbage_rows = []
        for hole in visible_holes:
            row = [True] * self.width
            row[hole] = False
            garbage_rows.append(row)

        self._cells = kept_rows + garbage_rows
        return overflow

    def cells(self):
        return (
            (x, y)
            for y, row in enumerate(self._cells)
            for x, occupied in enumerate(row)
            if occupied
        )
