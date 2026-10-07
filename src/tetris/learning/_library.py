import ctypes as ct
from pathlib import Path

from ._native_observation import NativeObservation
from ._native_proposal import NativeProposal


# {
# 責務: [
# load_library: 指定されたC++ Runtimeライブラリを読み込み、ABI契約を確認する
# ]
# 処理: [
# 1: 呼び出し元が指定したパスの共有ライブラリだけを読み込む
# 2: C ABI関数の引数型と戻り値型をctypesへ登録する
# 3: ABI versionとObservation構造体サイズを照合する
# 4: 不一致があればRuntimeを生成する前に例外を送出する
# ]
# 引数: [
# path: C++ Runtime共有ライブラリのパス
# ]
# 戻り値: 読み込みとABI検証が完了したctypes.CDLL
# エラー: パスが存在しない場合、ABIが非対応の場合、構造体配置が異なる場合に失敗する
# }
def load_library(path: str | Path) -> ct.CDLL:
    """Load only the caller-selected library; fail before creating state on ABI drift."""
    library = ct.CDLL(str(Path(path).resolve(strict=True)))
    # PythonとC++で同じ呼び出し規約を使うため、関数ごとの型を先に固定する。
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
    # 構造体を渡す前にABIとレイアウトを照合し、誤ったメモリ解釈を防ぐ。
    if library.kt_abi_version() != 1:
        raise RuntimeError("Unsupported Tetris Runtime ABI version")
    if library.kt_observation_size() != ct.sizeof(NativeObservation):
        raise RuntimeError("Tetris Runtime observation layout mismatch")
    return library


# {
# 責務: [
# check_status: C ABIの状態コードをPython側の例外へ変換する
# ]
# 処理: [
# 1: 成功コードなら呼び出し元へ戻る
# 2: 引数・範囲・割り当て失敗を対応する例外へ変換する
# 3: 未知の状態コードはRuntimeErrorとして保持する
# ]
# 引数: [status: C ABI関数が返した状態コード]
# 戻り値: なし
# エラー: 失敗コードに応じてValueError、IndexError、MemoryErrorまたはRuntimeErrorを送出する
# }
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
