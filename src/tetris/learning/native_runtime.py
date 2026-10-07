import ctypes as ct
import threading
import weakref
from collections.abc import Iterable, Sequence
from itertools import islice
from pathlib import Path

from ._library import check_status, load_library
from ._native_observation import NativeObservation
from ._native_proposal import NativeProposal
from .learning_observation import LearningObservation

ACTION_CODES = {
    "move_left": 0, "move_right": 1,
    "rotate_cw": 2, "rotate_ccw": 3,
    "soft_drop": 4, "hard_drop": 5, "hold": 6,
}


# {
# 責務: [unsigned: 指定幅の符号なし整数として扱えるPython値を検証する]
# 処理: [型と範囲を確認し、範囲外の値を拒否する]
# 引数: [value: 検証値, bits: bit幅, name: エラー表示用の値名]
# 戻り値: 検証済みのvalue
# エラー: boolを含む整数以外、負数、bit幅上限以上の値でValueErrorを送出する
# }
def unsigned(value: int, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < (1 << bits):
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")
    return value


# {
# 責務: [copied_observation: ctypes ObservationをPython所有の可視スナップショットへ変換する]
# 処理: [未設定ミノをNoneへ変換し、配列をtupleとbytesへコピーする]
# 引数: [raw: C ABIから受け取ったNativeObservation]
# 戻り値: LearningObservationの値コピー
# }
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


# {
# 責務: [
# NativeRuntime: C++ Headless Runtime handleの所有権とPython学習用操作を管理する
# ]
# フィールド: [
# _player_count: Runtime生成時のplayer数
# _lock: ctypes呼び出しを直列化する再入可能lock
# _library: 関数定義済みC ABIライブラリ
# _handle: C++ Runtimeのopaque handle
# _cleanup: handleを一度だけ破棄するfinalizer
# ]
# 処理: [Runtime生成、可視Observationのコピー、semantic proposal送信、tick進行、close時のhandle解放]
# 補足: 各workerは独立したNativeRuntimeを所有する。Python側でゲーム状態を保持しない
# }
class NativeRuntime:
    """One owned C++ Runtime for learning; use a with block or explicit close().

    Calls on this instance are serialized because ctypes releases the GIL.
    Each worker should own its own instance. No Python gameplay state is used.
    """

    # {
    # 責務: [__init__: seed列からC++ Runtimeを作成し、そのhandleを所有する]
    # 処理: [player数とseedを検証し、共有ライブラリを読み込んでfinalizerを登録する]
    # 引数: [self: 生成するRuntime, library_path: C ABI共有ライブラリ, seeds: playerごとの初期seed]
    # 戻り値: なし
    # エラー: seedが1..64個でない場合、seedがuint64範囲外の場合、library/ABI/生成に失敗した場合に例外を送出する
    # }
    def __init__(self, library_path: str | Path, seeds: Iterable[int]):
        values = list(islice(seeds, 65))
        if not 1 <= len(values) <= 64:
            raise ValueError("seeds must contain 1..64 values")
        self._player_count = len(values)
        seeds_array = (ct.c_uint64 * len(values))(
            *(unsigned(seed, 64, "seed") for seed in values)
        )
        self._lock = threading.RLock()
        self._library = load_library(library_path)
        self._handle = ct.c_void_p()
        check_status(self._library.kt_create(seeds_array, len(values), ct.byref(self._handle)))
        # Finalizerの登録に失敗した場合も、生成済みhandleを漏らさない。
        try:
            self._cleanup = weakref.finalize(self, self._library.kt_destroy, self._handle)
        except BaseException:
            self._library.kt_destroy(self._handle)
            raise

    # {
    # 責務: [_require_open: 操作対象のC++ Runtimeがまだ開いていることを確認する]
    # 処理: [finalizerの生存状態からclose済みか判定し、閉じていれば拒否する]
    # 引数: [self: 検査対象Runtime]
    # 戻り値: なし
    # エラー: close済みの場合にRuntimeErrorを送出する
    # }
    def _require_open(self) -> None:
        if not self._cleanup.alive:
            raise RuntimeError("Tetris Runtime is closed")

    # {
    # 責務: [close: C++ Runtime handleを一度だけ解放する]
    # 処理: [lock内でfinalizerを実行し、以降の操作を不許可にする]
    # 引数: [self: 解放対象Runtime]
    # 戻り値: なし
    # }
    def close(self) -> None:
        with self._lock:
            self._cleanup()

    # {
    # 責務: [__enter__: with文へ開いたRuntimeを渡す]
    # 処理: [lock内でopen状態を検証してselfを返す]
    # 引数: [self: 利用するRuntime]
    # 戻り値: withブロック内で使うNativeRuntime
    # エラー: close済みの場合にRuntimeErrorを送出する
    # }
    def __enter__(self) -> "NativeRuntime":
        with self._lock:
            self._require_open()
        return self

    # {
    # 責務: [__exit__: withブロック終了時にRuntimeを解放する]
    # 処理: [終了理由にかかわらずcloseを呼び出す]
    # 引数: [self: 解放するRuntime, exception_type / exception / traceback: with文の終了情報]
    # 戻り値: なし
    # }
    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()

    # {
    # 責務: [observe: 指定playerの可視ObservationをC++ Runtimeから取得する]
    # 処理: [player番号とopen状態を検証し、native snapshotをPython所有の値へコピーする]
    # 引数: [self: 対象Runtime, player: Observationを取得するplayer番号]
    # 戻り値: LearningObservationの値コピー
    # エラー: playerが整数範囲外の場合、またはRuntimeがclose済みの場合に失敗する
    # }
    def observe(self, player: int = 0) -> LearningObservation:
        unsigned(player, 32, "player")
        with self._lock:
            self._require_open()
            raw = NativeObservation()
            check_status(self._library.kt_observe(
                self._handle, player, ct.byref(raw), ct.sizeof(raw)
            ))
        return copied_observation(raw)

    # {
    # 責務: [observe_many: 全playerの可視Observationを一度のC ABI呼び出しで取得する]
    # 処理: [player数分の構造体を用意し、各スナップショットをPython値へコピーする]
    # 引数: [self: 対象Runtime]
    # 戻り値: player番号順のLearningObservation tuple
    # エラー: Runtimeがclose済みの場合にRuntimeErrorを送出する
    # }
    def observe_many(self) -> tuple[LearningObservation, ...]:
        """Copy visible observations for every player with one native call."""
        with self._lock:
            self._require_open()
            raw = (NativeObservation * self._player_count)()
            check_status(self._library.kt_observe_many(
                self._handle, raw, self._player_count
            ))
        return tuple(copied_observation(item) for item in raw)

    # {
    # 責務: [submit: 一人分のsemantic action proposalをC++ Runtimeへ登録する]
    # 処理: [整数とaction列を検証し、action code配列として一括送信する]
    # 引数: [self: 対象Runtime, player: 対象player, tick: 適用tick, first_sequence: 最初のaction sequence, actions: semantic action列]
    # 戻り値: なし
    # エラー: 範囲外整数、未定義action、action数超過、close済みRuntimeを拒否する
    # }
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

    # {
    # 責務: [submit_many: 一tick分の複数player proposalを原子的に登録する]
    # 処理: [各proposalを検証しaction列を一つの配列へ平坦化してC++ Runtimeへ一度に渡す]
    # 引数: [self: 対象Runtime, tick: 適用tick, proposals: (player, first_sequence, actions)の列]
    # 戻り値: なし
    # エラー: 不正なproposal、action数超過、close済みRuntimeを拒否する
    # }
    def submit_many(
        self,
        tick: int,
        proposals: Iterable[tuple[int, int, Iterable[str]]],
    ) -> None:
        """Atomically submit (player, first_sequence, actions) proposals for one tick."""
        unsigned(tick, 64, "tick")
        values = list(islice(proposals, 65))
        if not 1 <= len(values) <= 64:
            raise ValueError("batch must contain 1..64 proposals")
        native_proposals = (NativeProposal * len(values))()
        # ABIのproposalは共通action配列を参照するため、offset付きで一列にまとめる。
        flattened: list[int] = []
        for index, proposal in enumerate(values):
            if not isinstance(proposal, Sequence) or len(proposal) != 3:
                raise ValueError("each proposal must be (player, first_sequence, actions)")
            player, first_sequence, actions = proposal
            unsigned(player, 32, "player")
            unsigned(first_sequence, 64, "first_sequence")
            action_names = list(islice(actions, 4097))
            if len(action_names) > 4096 or len(flattened) + len(action_names) > 4096:
                raise ValueError("batch may contain at most 4096 actions")
            if any(not isinstance(action, str) or action not in ACTION_CODES for action in action_names):
                raise ValueError("unknown semantic action")
            native_proposals[index] = NativeProposal(
                player, first_sequence, len(flattened), len(action_names)
            )
            flattened.extend(ACTION_CODES[action] for action in action_names)
        action_array = (ct.c_uint8 * len(flattened))(*flattened)
        with self._lock:
            self._require_open()
            check_status(self._library.kt_submit_many(
                self._handle, tick, native_proposals, len(values), action_array, len(flattened)
            ))

    # {
    # 責務: [advance: C++ Runtimeを一tick進め、処理結果の数値を返す]
    # 処理: [open状態を確認してadvanceを呼び、tickと処理command数を値で返す]
    # 引数: [self: 進行対象Runtime]
    # 戻り値: (処理済みtick, 処理command数)
    # エラー: Runtimeがclose済みの場合にRuntimeErrorを送出する
    # }
    def advance(self) -> tuple[int, int]:
        """Return (processed tick, commands processed), not an independently owned state."""
        with self._lock:
            self._require_open()
            tick, commands = ct.c_uint64(), ct.c_uint64()
            check_status(self._library.kt_advance(
                self._handle, ct.byref(tick), ct.byref(commands)
            ))
            return tick.value, commands.value
