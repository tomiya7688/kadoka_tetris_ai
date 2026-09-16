"""Pure combat rules shared by the engine, CPU simulation, and benchmarks."""

from collections.abc import Callable

from .tetromino import PieceType


_T_PIVOTS = {
    0: (1, 1),
    1: (0, 1),
    2: (1, 0),
    3: (1, 1),
}


def attack_for_clear(
    lines: int,
    combo: int = 0,
    back_to_back: bool = False,
    *,
    t_spin: bool = False,
    perfect_clear: bool = False,
) -> int:
    """Return deterministic attack for a normalized clear result."""
    if lines < 0 or combo < 0:
        raise ValueError("lines and combo must be nonnegative")

    if t_spin:
        base = {0: 0, 1: 2, 2: 4, 3: 6}.get(lines, 6 + max(0, lines - 3))
        difficult_clear = lines > 0
    else:
        base = {0: 0, 1: 0, 2: 1, 3: 2, 4: 4}.get(lines, 0)
        if lines > 4:
            base = 4 + (lines - 4)
        difficult_clear = lines >= 4

    if back_to_back and difficult_clear:
        base += 1
    if lines > 0:
        base += max(0, combo - 1)
    if perfect_clear and lines > 0:
        base += 10
    return base


def is_t_spin_placement(
    piece: PieceType,
    rotation: int,
    origin_x: int,
    origin_y: int,
    *,
    width: int,
    height: int,
    occupied: Callable[[int, int], bool],
    last_rotation: bool,
    top_out_of_bounds_occupied: bool = True,
) -> bool:
    """Apply the engine's current three-corner T-Spin rule to a placement.

    ``occupied`` must describe the board *before* the T piece is locked. Side and
    bottom out-of-field corners always count as occupied. Runtime GameState also uses
    the default ``top_out_of_bounds_occupied=True`` because y<0 is a real field wall.
    A visible-only simulator may pass False because y<0 in visible coordinates means
    hidden rows whose contents are unknown rather than a known wall.
    """
    if piece != PieceType.T or not last_rotation:
        return False

    pivot_x, pivot_y = _T_PIVOTS[rotation % 4]
    center_x = origin_x + pivot_x
    center_y = origin_y + pivot_y
    occupied_corners = 0
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x = center_x + dx
        y = center_y + dy
        if x < 0 or x >= width or y >= height:
            occupied_corners += 1
        elif y < 0:
            occupied_corners += int(top_out_of_bounds_occupied)
        elif occupied(x, y):
            occupied_corners += 1
    return occupied_corners >= 3
