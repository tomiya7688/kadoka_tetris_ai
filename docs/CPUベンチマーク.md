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

配布EXEはwindowedビルドなので、結果は標準出力だけに依存せずJSONファイルへ保存する。
デフォルト保存先は `UserData/Logs/cpu-benchmark.json`。

任意の保存先を指定する場合:

```text
--benchmark-output path/to/result.json
```

## 再現性

`--benchmark-seed N` を指定すると最初のゲームがseed N、2ゲーム目がN+1、以降も1ずつ増加する。
CPU比較では同じseed範囲を使用する。

## 主要な出力

ゲームごとに以下を記録する。

- 配置したミノ数
- 消去ライン数
- game overの有無
- piece limit到達の有無
- tick limit到達の有無
- 最終盤面高 / 最終穴数
- 最大盤面高 / 最大穴数
- 平均盤面高 / 平均穴数
- CPU判断呼び出し回数
- CPU判断に使用した累積時間
- 1配置あたり判断時間
- 1配置あたりtick数

レポート全体には複数ゲームの合計・平均値も含める。

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

- Easy / Normal / Hardの同一seed一括比較
- CSV出力
- 並列実行
- CPUバージョン・評価重みの記録
- 対戦ベンチマーク
- Block Slime / Kadokaモデルとの共通ベンチマーク
- CIでの性能退行検出
