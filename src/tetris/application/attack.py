"""Deterministic versus attack and garbage calculations."""
def attack_for_clear(lines: int, combo: int = 0, back_to_back: bool = False) -> int:
    if lines < 0 or combo < 0: raise ValueError("lines and combo must be nonnegative")
    base = {0: 0, 1: 0, 2: 1, 3: 2, 4: 4}.get(lines, 0)
    if lines > 4: base = 4 + (lines - 4)
    bonus = max(0, combo - 1)
    if back_to_back and lines >= 4: base += 1
    return base + bonus

def cancel_attack(incoming: int, outgoing: int) -> tuple[int, int]:
    if incoming < 0 or outgoing < 0: raise ValueError("attack must be nonnegative")
    cancelled = min(incoming, outgoing)
    return incoming - cancelled, outgoing - cancelled
