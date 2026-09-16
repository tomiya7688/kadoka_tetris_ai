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

CPU同士を実際のGarbage対戦で比較する場合:

```bat
KadokaTetrisAI.exe --benchmark-versus easy hard --benchmark-games 10 --benchmark-max-pieces 200 --benchmark-seed 0
```

`--benchmark-versus A B` は1 seedにつき2戦行う。
1戦目はA=P1 / B=P2、2戦目はA=P2 / B=P1と左右を反転する。
両者には同一のミノseedを与え、2戦とも同一のGarbage穴seedを使う。
したがって `--benchmark-games 10` なら20戦になる。

配布EXEはwindowedビルドなので、結果は標準出力だけに依存せずJSONファイルへ保存する。
通常ベンチマークのデフォルト保存先は `UserData/Logs/cpu-benchmark.json`、対戦ベンチマークは `UserData/Logs/cpu-versus-benchmark.json`。

任意の保存先を指定する場合:

```text
--benchmark-output path/to/result.json
```

## 再現性

`--benchmark-seed N` を指定すると最初のゲームがseed N、2ゲーム目がN+1、以降も1ずつ増加する。
CPU比較では同じseed範囲を使用する。

標準CPUの評価重みは `UserData/Config/standard_cpu.json` から読み込む。
重みを変更して比較する場合もseed範囲を固定する。

## 1人用ベンチマーク

JSONには `benchmark_schema_version`、CPUプロファイル情報、評価器情報を含める。
現在のbenchmark schemaはv3。

ゲームごとに主に以下を記録する。

- 配置したミノ数
- 消去ライン数 / lines per placement
- 生成攻撃量 / attack per placement / attack per line
- T-Spin回数
- Perfect Clear回数
- B2B difficult clear回数
- 最大Combo
- game overの有無
- piece limit / tick limit
- 最終・最大・平均の盤面高 / 穴数 / 凹凸
- CPU判断回数 / 判断時間

`--benchmark-cpu all` は `summary_by_level`、weight sweepは `summary_by_candidate` を持つ。

## CPU-vs-CPU対戦ベンチマーク

対戦用JSONは独立した `versus_benchmark_schema_version` を持つ。
各ミラー戦について以下を記録する。

- 勝者 / draw
- KO / piece-limit / tick-limit
- A/Bがどちらのplayer slotを使ったか
- 配置数 / ライン数
- outgoing attack
- cancelled garbage
- garbage received
- T-Spin / Perfect Clear / max combo
- 最終stack height / holes
- CPU判断時間
- neutral / defense / pressureで作った配置プラン数

集計はplayer 0/1ではなく競技者A/Bへ戻して行うため、左右を入れ替えた結果を同じCPU側へ合算できる。

## 公平性と可視情報境界

1人用CPUは `PlayerObservation`、対戦CPUは `VersusPlayerObservation` だけを判断入力にする。

```text
VersusSession
    ↓ 可視情報抽出
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

ベンチマークハーネスは勝敗や計測のためGameState / PlayerResultを読むが、それらはCPUへ渡さない。
LockEvent、bag/RNG内部状態、攻撃履歴、相殺履歴などもCPU判断入力には含めない。

## 停止条件

通常は両者が `--benchmark-max-pieces` に到達するか、どちらかがKOすると終了する。
CPU停止や不具合で無限ループしないよう1配置あたり最大120tick相当の安全上限を持つ。

## 今後の拡張

- CSV出力
- 並列実行
- T-Spin Mini / SRS準拠判定による攻撃指標の精密化
- Block Slime / Kadokaモデルとの共通対戦ベンチマーク
- CIでの性能退行検出
