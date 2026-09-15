# CPUベンチマーク

標準内蔵CPUをGUIなしで自動実行し、強さ・安定性・処理速度を同じ形式で比較するための基盤。

## 実行例

開発環境:

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main --benchmark-cpu easy --benchmark-games 10 --benchmark-max-pieces 200 --benchmark-seed 0
```

配布版:

```bat
KadokaTetrisAI.exe --benchmark-cpu normal --benchmark-games 10 --benchmark-max-pieces 200
```

Easy / Normal / Hardを同一seed範囲で一括比較する場合:

```bat
KadokaTetrisAI.exe --benchmark-cpu all --benchmark-games 10 --benchmark-max-pieces 200 --benchmark-seed 0
```

`all` は各レベルへ同じseed列を与えるため、ランダムなミノ列の差をCPU差と取り違えにくい。

配布EXEはwindowedビルドなので、結果は標準出力だけに依存せずJSONファイルへ保存する。
デフォルト保存先は `UserData/Logs/cpu-benchmark.json`。

任意の保存先を指定する場合:

```text
--benchmark-output path/to/result.json
```

## 再現性

`--benchmark-seed N` を指定すると最初のゲームがseed N、2ゲーム目がN+1、以降も1ずつ増加する。
CPU比較では同じseed範囲を使用する。

標準CPUの評価重みは `UserData/Config/standard_cpu.json` から読み込む。
重みを変更して比較する場合もseed範囲を固定する。

## 結果の識別情報

JSONには `benchmark_schema_version`、CPUプロファイル情報、評価器情報を含める。

- CPU実装ID
- CPUレベル名
- 探索深度
- 入力間隔tick
- lookahead係数
- 評価器ID
- 実際に使用した6つの評価重み

現在の標準CPU実装IDは `standard-visible-v1`、評価器IDは `visible-board-v1`。
アルゴリズム互換性を壊す変更を行う場合は実装IDまたは評価器IDを更新し、古いベンチマーク結果と区別できるようにする。

## 主要な出力

ゲームごとに以下を記録する。

- 配置したミノ数
- 消去ライン数 / lines per placement
- game overの有無
- piece limit到達の有無
- tick limit到達の有無
- 最終盤面高 / 最終穴数 / 最終凹凸
- 最大盤面高 / 最大穴数 / 最大凹凸
- 平均盤面高 / 平均穴数 / 平均凹凸
- CPU判断呼び出し回数
- CPU判断に使用した累積時間
- 1配置あたり判断時間
- 1配置あたりtick数

レポート全体には複数ゲームの合計・平均値も含める。
`--benchmark-cpu all` の比較レポートは `summary_by_level` と各レベルの完全な個別レポートを保持する。

## 公平性

CPUの意思決定は通常プレイ時と同じ経路を使う。

```text
VisiblePlayerObserver
    ↓
PlayerObservation
    ↓
StandardCpuStrategy
    ↓
VisibleCpuController
    ↓
InputAction
    ↓
InputRouter
    ↓
TickEngine
```

ベンチマーク専用にGameState内部値をCPUへ渡す経路は作らない。
盤面品質メトリクスもPlayerObservationの可視盤面から算出する。

ベンチマークハーネス自身は試合終了判定や集計のためにゲームのライン数・game over状態を読むが、それらはCPUの判断入力には使用しない。

## 停止条件

通常は `--benchmark-max-pieces` に到達するかgame overで終了する。
不具合やCPU停止で無限ループしないよう、内部で1配置あたり最大120tickの安全上限を持つ。

## 今後の拡張

- CSV出力
- 並列実行
- 評価重みの自動・半自動探索
- 対戦ベンチマーク
- Block Slime / Kadokaモデルとの共通ベンチマーク
- CIでの性能退行検出
