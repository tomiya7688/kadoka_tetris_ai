"""Deterministic versus attack and garbage calculations."""

from tetris.core import LockEvent, attack_for_clear


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
