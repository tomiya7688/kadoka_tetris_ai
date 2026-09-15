"""Deterministic versus attack and garbage calculations."""

from tetris.core import LockEvent


def attack_for_clear(
    lines: int,
    combo: int = 0,
    back_to_back: bool = False,
    *,
    t_spin: bool = False,
    perfect_clear: bool = False,
) -> int:
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


def attack_for_event(event: LockEvent) -> int:
    return attack_for_clear(
        event.lines,
        combo=event.combo,
        back_to_back=event.back_to_back,
        t_spin=event.t_spin,
        perfect_clear=event.perfect_clear,
    )


def cancel_attack(incoming: int, outgoing: int) -> tuple[int, int]:
    if incoming < 0 or outgoing < 0:
        raise ValueError("attack must be nonnegative")
    cancelled = min(incoming, outgoing)
    return incoming - cancelled, outgoing - cancelled
