from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
# {
# 責務: [
# LearningObservation: C++ Runtimeからコピーした可視状態をPython学習toolingへ渡す
# ]
# フィールド: [
# tick / pieces_locked / active_kind / active_x / active_y / active_rotation: 現在の進行と操作中ミノ
# hold_kind / hold_used / next_pieces: HOLDと公開済みNEXT
# lines / combo / back_to_back_active / game_over: 公開された対戦状態
# locked_cells / active_cells: hidden rowを含まない10x20行優先盤面
# ]
# 処理: [値だけを保持し、C++のcanonical stateや内部乱数状態へ参照を持たない]
# }
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
