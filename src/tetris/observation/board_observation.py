"""Immutable player-visible board geometry."""

from dataclasses import dataclass
from typing import Iterable


Cell = tuple[int, int]


@dataclass(frozen=True)
class BoardObservation:
    """Visible field cells without hidden engine or random-generator state."""

    width: int
    height: int
    locked_cells: frozenset[Cell]
    active_cells: frozenset[Cell]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.width, int)
            or isinstance(self.width, bool)
            or not isinstance(self.height, int)
            or isinstance(self.height, bool)
            or self.width <= 0
            or self.height <= 0
        ):
            raise ValueError("observation dimensions must be positive integers")

        locked_cells = self._normalize_cells(self.locked_cells)
        active_cells = self._normalize_cells(self.active_cells)
        object.__setattr__(self, "locked_cells", locked_cells)
        object.__setattr__(self, "active_cells", active_cells)

        if locked_cells & active_cells:
            raise ValueError("locked and active cells must not overlap")

    def occupied(self, x: int, y: int) -> bool:
        cell = (x, y)
        return cell in self.locked_cells or cell in self.active_cells

    def _normalize_cells(self, cells: Iterable[Cell]) -> frozenset[Cell]:
        normalized = frozenset(cells)
        for cell in normalized:
            if not isinstance(cell, tuple) or len(cell) != 2:
                raise ValueError(f"invalid observation cell: {cell!r}")
            x, y = cell
            if (
                not isinstance(x, int)
                or isinstance(x, bool)
                or not isinstance(y, int)
                or isinstance(y, bool)
            ):
                raise ValueError(f"invalid observation cell: {cell!r}")
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                raise ValueError(f"observation cell is out of bounds: {cell}")
        return normalized
