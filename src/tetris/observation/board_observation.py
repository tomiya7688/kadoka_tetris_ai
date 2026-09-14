"""Immutable player-visible board geometry."""

from dataclasses import dataclass


Cell = tuple[int, int]


@dataclass(frozen=True)
class BoardObservation:
    """Visible field cells without hidden engine or random-generator state."""

    width: int
    height: int
    locked_cells: frozenset[Cell]
    active_cells: frozenset[Cell]

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("observation dimensions must be positive")
        self._validate_cells(self.locked_cells)
        self._validate_cells(self.active_cells)
        if self.locked_cells & self.active_cells:
            raise ValueError("locked and active cells must not overlap")

    def occupied(self, x: int, y: int) -> bool:
        cell = (x, y)
        return cell in self.locked_cells or cell in self.active_cells

    def _validate_cells(self, cells: frozenset[Cell]) -> None:
        for x, y in cells:
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                raise ValueError(f"observation cell is out of bounds: {(x, y)}")
