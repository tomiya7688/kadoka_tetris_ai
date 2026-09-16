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

## 到達可能配置と火力評価

標準CPU v2は `VisibleAttackPlacementPlanner` を使う。

現在ミノについては、最終座標だけを列挙せず、左右移動・回転・soft dropを使う到達可能な操作経路を探索する。
そのため、単純hard dropでは届かないtuckや、最後の成功操作を回転にする配置も候補にできる。

最終候補に対して、可視情報だけで確定できる以下の基礎火力を実対戦と同じ攻撃表で加点する。

- ライン消去
- 到達操作列と可視盤面から確定できるT-Spin
- Perfect Clear

ComboとB2Bの内部カウンタは現時点では画面に表示していないため、CPUの火力推定には使わない。
ベンチマーク側は実際のLockEventからCombo/B2Bを計測できるが、その値をCPU判断へ戻してはいけない。

可視盤面上端より上はhidden rowであり、CPUには内容が見えない。そのためT-Spin推定でも、可視座標 `y < 0` を勝手に壁・occupiedとして扱わない。

## 初期モード

対戦用標準CPUは3モードを持つ。

### neutral

通常の標準CPU評価重みを使い、基礎火力の重みは `2.0`。

### defense

以下のどちらかで選択する。

- pending Garbageが3以上
- 自盤面の可視stack heightが15以上

穴、穴の上を覆うブロック、高さへの罰則を強め、ライン消去も少し優先する。
Garbageを受ける前後で掘りやすい盤面を維持することを狙う。
基礎火力の重みは `1.0` とし、生存性を優先する。

### pressure

以下のどちらかで選択する。

- 相手の可視stack heightが14以上
- 相手のpending Garbageが4以上

ライン消去の価値を上げ、高さ・凹凸への罰則を少し緩める。
さらに基礎火力の重みを `4.0` に上げ、相手が危険なときに刺せる攻撃を優先しやすくする。

## 判断保持

モード判定は新しいミノの配置プランを作る時だけ行う。
一度作った操作列は途中で相手盤面やGarbage量が変わっても保持する。

これにより、1ミノの操作中にpressure/defenseが切り替わって左右移動をやり直すような振動を防ぐ。

## 現在の限界

この段階の `VersusStandardCpuStrategy` は軽量な標準CPUであり、Block Slimeではない。

T-Spinは「現在の盤面に既に存在する、到達可能なT-Spin配置」を評価できるようになったが、まだT-Spin形そのものを数手かけて構築する専用探索は行わない。

まだ以下は専用探索していない。

- T-Spin構築・T-Spin継続形の価値評価
- PC構築
- B2B/Comboを可視UIから扱う設計
- 相手への実際の到達火力を含めたminimax
- Garbage穴位置を使う将来downstack予測
- 相手のPC連打阻止
- 相手の攻撃タイミング予測

これらはCPU-vs-CPU対戦ベンチマークで火力・勝敗・被Garbageの変化を確認しながら段階的に追加する。
