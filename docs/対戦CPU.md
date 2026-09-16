# 対戦用標準CPU

2プレイヤー対戦では、1人用の `PlayerObservation` ではなく `VersusPlayerObservation` を境界として使う。

```text
VersusSession
    ↓  可視情報だけ抽出
VisibleVersusObserver
    ↓
VersusPlayerObservation
    ↓
VersusStandardCpuStrategy
    ↓
VisibleVersusCpuController
    ↓
InputAction
    ↓
InputRouter / TickEngine
```

## CPUへ渡る情報

- 自分の可視盤面
- 自分のACTIVE / HOLD / 表示NEXT
- 相手の可視盤面
- 相手のACTIVE / HOLD / 表示NEXT
- 画面に表示される自分のpending Garbage量
- 画面に表示される相手のpending Garbage量

以下は渡さない。

- SevenBag / RNG内部状態
- 非表示NEXT
- raw GameState
- LockEvent
- 過去の攻撃履歴
- Garbage相殺履歴
- 内部tickや未表示タイマー

## 初期モード

標準CPUの対戦対応は、既存の可視盤面探索を壊さずに3モードで開始する。

### neutral

通常の標準CPU評価重みをそのまま使う。

### defense

以下のどちらかで選択する。

- pending Garbageが3以上
- 自盤面の可視stack heightが15以上

穴、穴の上を覆うブロック、高さへの罰則を強め、ライン消去も少し優先する。
Garbageを受ける前後で掘りやすい盤面を維持することを狙う。

### pressure

以下のどちらかで選択する。

- 相手の可視stack heightが14以上
- 相手のpending Garbageが4以上

ライン消去の価値を上げ、高さ・凹凸への罰則を少し緩める。
相手が危険なときに、地形を完全に整えることより追加攻撃を優先しやすくする。

## 判断保持

モード判定は新しいミノの配置プランを作る時だけ行う。
一度作った操作列は途中で相手盤面やGarbage量が変わっても保持する。

これにより、1ミノの操作中にpressure/defenseが切り替わって左右移動をやり直すような振動を防ぐ。

## 現在の限界

この段階の `VersusStandardCpuStrategy` は対戦状況で既存評価重みを切り替える軽量な標準CPUであり、Block Slimeではない。

まだ以下は専用探索していない。

- T-Spin構築
- PC構築
- 相手への実際の到達火力を含めたminimax
- Garbage穴位置を使う将来downstack予測
- 相手のPC連打阻止
- 相手の攻撃タイミング予測

これらはCPU-vs-CPU対戦ベンチマークで基準値を作った後に追加する。
