import ctypes as ct
import threading
import weakref
from collections.abc import Iterable
from itertools import islice
from pathlib import Path

from ._library import check_status, load_library
from ._native_observation import NativeObservation
from .learning_observation import LearningObservation

ACTION_CODES = {
    "move_left": 0, "move_right": 1,
    "rotate_cw": 2, "rotate_ccw": 3,
    "soft_drop": 4, "hard_drop": 5, "hold": 6,
}


def unsigned(value: int, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < (1 << bits):
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")
    return value


def copied_observation(raw: NativeObservation) -> LearningObservation:
    return LearningObservation(
        tick=raw.tick, pieces_locked=raw.pieces_locked,
        active_kind=None if raw.active_kind == -1 else raw.active_kind,
        active_x=raw.active_x, active_y=raw.active_y, active_rotation=raw.active_rotation,
        hold_kind=None if raw.hold_kind == -1 else raw.hold_kind,
        lines=raw.lines, combo=raw.combo, next_pieces=tuple(raw.next_pieces),
        hold_used=bool(raw.hold_used), game_over=bool(raw.game_over),
        back_to_back_active=bool(raw.back_to_back_active),
        locked_cells=bytes(raw.locked_cells), active_cells=bytes(raw.active_cells),
    )


class NativeRuntime:
    """One owned C++ Runtime for learning; use a with block or explicit close().

    Calls on this instance are serialized because ctypes releases the GIL.
    Each worker should own its own instance. No Python gameplay state is used.
    """

    def __init__(self, library_path: str | Path, seeds: Iterable[int]):
        values = list(islice(seeds, 65))
        if not 1 <= len(values) <= 64:
            raise ValueError("seeds must contain 1..64 values")
        seeds_array = (ct.c_uint64 * len(values))(
            *(unsigned(seed, 64, "seed") for seed in values)
        )
        self._lock = threading.RLock()
        self._library = load_library(library_path)
        self._handle = ct.c_void_p()
        check_status(self._library.kt_create(seeds_array, len(values), ct.byref(self._handle)))
        try:
            self._cleanup = weakref.finalize(self, self._library.kt_destroy, self._handle)
        except BaseException:
            self._library.kt_destroy(self._handle)
            raise

    def _require_open(self) -> None:
        if not self._cleanup.alive:
            raise RuntimeError("Tetris Runtime is closed")

    def close(self) -> None:
        with self._lock:
            self._cleanup()

    def __enter__(self) -> "NativeRuntime":
        with self._lock:
            self._require_open()
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()

    def observe(self, player: int = 0) -> LearningObservation:
        unsigned(player, 32, "player")
        with self._lock:
            self._require_open()
            raw = NativeObservation()
            check_status(self._library.kt_observe(
                self._handle, player, ct.byref(raw), ct.sizeof(raw)
            ))
        return copied_observation(raw)

    def submit(self, player: int, tick: int, first_sequence: int, actions: Iterable[str]) -> None:
        unsigned(player, 32, "player")
        unsigned(tick, 64, "tick")
        unsigned(first_sequence, 64, "first_sequence")
        values = list(islice(actions, 4097))
        if len(values) > 4096:
            raise ValueError("proposal may contain at most 4096 actions")
        if any(not isinstance(action, str) or action not in ACTION_CODES for action in values):
            raise ValueError("unknown semantic action")
        proposal = (ct.c_uint8 * len(values))(*(ACTION_CODES[action] for action in values))
        with self._lock:
            self._require_open()
            check_status(self._library.kt_submit(
                self._handle, player, tick, first_sequence, proposal, len(values)
            ))

    def advance(self) -> tuple[int, int]:
        """Return (processed tick, commands processed), not an independently owned state."""
        with self._lock:
            self._require_open()
            tick, commands = ct.c_uint64(), ct.c_uint64()
            check_status(self._library.kt_advance(
                self._handle, ct.byref(tick), ct.byref(commands)
            ))
            return tick.value, commands.value
