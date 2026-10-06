import ctypes as ct


class NativeProposal(ct.Structure):
    _fields_ = [
        ("player", ct.c_uint32),
        ("first_sequence", ct.c_uint64),
        ("action_offset", ct.c_uint32),
        ("action_count", ct.c_uint32),
    ]
