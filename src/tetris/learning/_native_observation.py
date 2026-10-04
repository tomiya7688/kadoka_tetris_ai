import ctypes as ct


class NativeObservation(ct.Structure):
    """Internal ABI v1 layout; never exposes canonical memory."""

    _fields_ = [
        ("tick", ct.c_uint64),
        ("pieces_locked", ct.c_uint64),
        ("active_kind", ct.c_int32),
        ("active_x", ct.c_int32),
        ("active_y", ct.c_int32),
        ("active_rotation", ct.c_int32),
        ("hold_kind", ct.c_int32),
        ("lines", ct.c_int32),
        ("combo", ct.c_int32),
        ("next_pieces", ct.c_int32 * 5),
        ("hold_used", ct.c_uint32),
        ("game_over", ct.c_uint32),
        ("back_to_back_active", ct.c_uint32),
        ("locked_cells", ct.c_uint8 * 200),
        ("active_cells", ct.c_uint8 * 200),
    ]
