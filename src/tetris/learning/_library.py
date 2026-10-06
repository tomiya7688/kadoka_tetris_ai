import ctypes as ct
from pathlib import Path

from ._native_observation import NativeObservation
from ._native_proposal import NativeProposal


def load_library(path: str | Path) -> ct.CDLL:
    """Load only the caller-selected library; fail before creating state on ABI drift."""
    library = ct.CDLL(str(Path(path).resolve(strict=True)))
    signatures = {
        "kt_abi_version": ([], ct.c_uint32),
        "kt_observation_size": ([], ct.c_uint32),
        "kt_create": ([ct.POINTER(ct.c_uint64), ct.c_uint32, ct.POINTER(ct.c_void_p)], ct.c_int32),
        "kt_destroy": ([ct.c_void_p], None),
        "kt_observe": ([ct.c_void_p, ct.c_uint32, ct.POINTER(NativeObservation), ct.c_uint32], ct.c_int32),
        "kt_observe_many": ([ct.c_void_p, ct.POINTER(NativeObservation), ct.c_uint32], ct.c_int32),
        "kt_submit": ([ct.c_void_p, ct.c_uint32, ct.c_uint64, ct.c_uint64, ct.POINTER(ct.c_uint8), ct.c_uint32], ct.c_int32),
        "kt_submit_many": ([ct.c_void_p, ct.c_uint64, ct.POINTER(NativeProposal), ct.c_uint32, ct.POINTER(ct.c_uint8), ct.c_uint32], ct.c_int32),
        "kt_advance": ([ct.c_void_p, ct.POINTER(ct.c_uint64), ct.POINTER(ct.c_uint64)], ct.c_int32),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(library, name)
        function.argtypes = arguments
        function.restype = result
    if library.kt_abi_version() != 1:
        raise RuntimeError("Unsupported Tetris Runtime ABI version")
    if library.kt_observation_size() != ct.sizeof(NativeObservation):
        raise RuntimeError("Tetris Runtime observation layout mismatch")
    return library


def check_status(status: int) -> None:
    if status == 0:
        return
    if status == 1:
        raise ValueError("C++ Runtime rejected the argument or proposal")
    if status == 2:
        raise IndexError("C++ Runtime index is out of range")
    if status == 3:
        raise MemoryError("C++ Runtime allocation failed")
    raise RuntimeError(f"C++ Runtime failed with status {status}")
