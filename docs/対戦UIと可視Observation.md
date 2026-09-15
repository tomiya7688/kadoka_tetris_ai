# 対戦UIと可視Observation

2プレイヤー対戦では、AIへゲーム内部状態を直接渡すのではなく、対戦画面へ実際に表示される情報だけを共通Observationへ変換する。

## 起動

2人キーボード対戦:

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main --versus
```

Player 1対標準CPU:

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main --versus --versus-cpu-level normal
```

配布EXEでも同じ引数を使用できる。

```bat
KadokaTetrisAI.exe --versus --versus-cpu-level normal
```

Garbage穴列を再現するseedを指定する場合:

```text
--versus-garbage-seed 123
```

現段階ではversusモードとlocalhost APIの同時使用は未対応。

## 画面に表示する情報

両プレイヤーについて以下を同時表示する。

- 可視盤面
- 操作中ミノ
- ACTIVE
- HOLD
- 表示NEXT
- pending GARBAGE量
- game over時のKO表示

hidden rows、7-bag内部、RNG状態、LockEvent、攻撃履歴、相殺履歴などは表示しない。

## VersusPlayerObservation

`tetris.observation.VersusPlayerObservation` は対戦画面と同じ情報境界を表す。

```text
VersusPlayerObservation
├─ own: PlayerObservation
├─ opponent: PlayerObservation
├─ incoming_garbage
└─ opponent_incoming_garbage
```

`own` と `opponent` は既存の `PlayerObservation` なので、それぞれ以下だけを持つ。

- visible BoardObservation
- current piece
- HOLD
- displayed NEXT

Garbage量をObservationへ含められるのは、今回UI側でも同じ値を明示表示するため。

## 現在の標準CPU

`--versus-cpu-level` で使用する標準CPUは、現時点では従来どおり**自分のPlayerObservationだけ**で判断する。
対戦UIを追加しただけで、相手盤面やGarbageメーターを勝手に既存CPUへ入力してはいない。

今後、相手盤面を利用する対戦CPUを実装する場合は `VersusPlayerObservation` を入力境界にし、画面に表示されていない内部情報へ依存しない。

## 今後

- localhost APIの2プレイヤー対応
- VersusPlayerObservationを利用する対戦用CPU controller/strategy
- 相手の高さ・掘り状態・PC連打などを考慮する判断
- pending Garbageへの防御判断
- CPU-vs-CPU対戦benchmark
- 対戦画面のレイアウト・ミノ色・Garbage表示の改善
