from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LearningObservation:
    """Copied visible state: masks are 10x20 row-major bytes, never hidden rows.

    Piece codes are I/O/T/S/Z/J/L = 0..6. Absent active/hold kind is None.
    Coordinates use the visible board; an active origin can be above row zero.
    """

    tick: int
    pieces_locked: int
    active_kind: int | None
    active_x: int
    active_y: int
    active_rotation: int
    hold_kind: int | None
    lines: int
    combo: int
    next_pieces: tuple[int, ...]
    hold_used: bool
    game_over: bool
    back_to_back_active: bool
    locked_cells: bytes
    active_cells: bytes
