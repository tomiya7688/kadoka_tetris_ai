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

標準CPU v4は `VisibleTSpinReadyPlanner` を使う。

現在ミノについては、最終座標だけを列挙せず、左右移動・回転・soft dropを使う到達可能な操作経路を探索する。
そのため、単純hard dropでは届かないtuckや、最後の成功操作を回転にする配置も候補にできる。

最終候補に対して、可視情報だけで確定できる以下の基礎火力を実対戦と同じ攻撃表で加点する。

- ライン消去
- 到達操作列と可視盤面から確定できるT-Spin
- Perfect Clear

ComboとB2Bの内部カウンタは現時点では画面に表示していないため、CPUの火力推定には使わない。
ベンチマーク側は実際のLockEventからCombo/B2Bを計測できるが、その値をCPU判断へ戻してはいけない。

可視盤面上端より上はhidden rowであり、CPUには内容が見えない。そのためT-Spin推定でも、可視座標 `y < 0` を勝手に壁・occupiedとして扱わない。

### 表示NEXTを使ったT-Spin先読み

v3以降では、探索深度内にある表示NEXTのTミノについても、安価な最終座標列挙ではなく到達可能なsemantic action探索を行う。
これにより、現在ミノでT-Spinを打てる場合だけでなく、Normalなら主に1手先、Hardなら主に2手先までの表示NEXTを使い、先行する配置でT-Spin形を作った結果として得られる将来火力を評価できる。

先読み中の非Tミノは従来どおり軽量な幾何drop近似を使う。すべての将来ミノを操作列探索へ切り替えないことで、T-Spin対応による探索コスト増加を局所化する。

この判断に使うのは現在の可視盤面と表示NEXTだけであり、非表示bagやRNG内部状態は参照しない。

### 探索深度外のT-Spin readiness

v4では `VisibleTSpinReadinessEvaluator` を追加し、Tがまだ探索深度内に見えていなくても、現在の可視盤面に残っている有用なT-Spin穴を軽量に評価する。

readinessとして数えるのは、仮にTを入れた場合に以下をすべて満たす可視スロットだけとする。

- Tの4セルがすべて可視範囲内で空いている
- その位置からさらに1段下へ落ちない
- 実ゲームと同じthree-corner条件を満たす
- 少なくとも1ライン消去になる

評価値は、そのスロットへ将来Tを入れた場合の基礎attackの最大値とする。実際に表示NEXTへTが入った後は従来どおりsemantic action探索で到達可能性を確認するため、readinessは「将来価値」、実火力評価は「実行可能な手」と役割を分ける。

標準CPUのreadiness重みは `0.75`。対戦モードでは以下とする。

- defense: `0.25`
- neutral: `0.75`
- pressure: `1.25`

したがって、危険時はT-Spin穴の保存より生存・掘りを優先し、相手へ圧力を掛けたい局面では将来火力形をより残しやすくする。

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

T-Spinは、現在ミノ・探索深度内の表示NEXT・探索深度外へ残すreadinessの3段階で扱うようになった。
ただしreadinessはテンプレート認識ではなく幾何ヒューリスティックなので、DT砲など特定の継続テンプレートや、数手先の入口経路まで保証するものではない。

まだ以下は専用探索していない。

- DT砲などのT-Spin継続テンプレート認識
- PC構築
- B2B/Comboを可視UIから扱う設計
- 相手への実際の到達火力を含めたminimax
- Garbage穴位置を使う将来downstack予測
- 相手のPC連打阻止
- 相手の攻撃タイミング予測

これらはCPU-vs-CPU対戦ベンチマークで火力・勝敗・被Garbageの変化を確認しながら段階的に追加する。
