import ctypes as ct


# {
# 責務: [
# NativeObservation: C++ RuntimeのABI v1 Observationを受け取る固定レイアウトを定義する
# ]
# フィールド: [
# tick / pieces_locked: Runtimeの進行状況
# active_kind / active_x / active_y / active_rotation: 操作中ミノの可視情報
# hold_kind / lines / combo / next_pieces: 利用者へ公開する進行情報
# hold_used / game_over / back_to_back_active: Runtime状態フラグ
# locked_cells / active_cells: 10x20盤面の行優先セル値
# ]
# 処理: [C ABIから値をコピーして受け取る。canonical stateへの参照は保持しない]
# }
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
