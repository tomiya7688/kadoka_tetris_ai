import ctypes as ct


# {
# 責務: [
# NativeProposal: 一括submit用にplayerとflattened action配列の範囲を表す
# ]
# フィールド: [
# player: 提案を送るplayer番号
# first_sequence: 最初のsemantic actionのsequence番号
# action_offset: 共通action配列内の開始位置
# action_count: この提案に含めるaction数
# ]
# 処理: [Python側の検証済み提案をC ABIの固定幅整数レイアウトへ渡す]
# }
class NativeProposal(ct.Structure):
    _fields_ = [
        ("player", ct.c_uint32),
        ("first_sequence", ct.c_uint64),
        ("action_offset", ct.c_uint32),
        ("action_count", ct.c_uint32),
    ]
