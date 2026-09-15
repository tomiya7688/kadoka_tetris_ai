# 標準CPU評価重み

標準内蔵CPUの盤面評価重みは `UserData/Config/standard_cpu.json` から変更できる。
ファイルが存在しない場合は起動時に現在の既定値で自動生成する。

```json
{
  "version": 1,
  "weights": {
    "cleared_lines": 3.0,
    "aggregate_height": -0.35,
    "max_height": -0.45,
    "holes": -7.0,
    "covered_hole_cells": -1.25,
    "bumpiness": -0.25
  }
}
```

## 各重み

| 項目 | 意味 | 既定値 |
| --- | --- | ---: |
| `cleared_lines` | 1手で消したラインへの加点 | `3.0` |
| `aggregate_height` | 全列の高さ合計への評価 | `-0.35` |
| `max_height` | 最も高い列への評価 | `-0.45` |
| `holes` | ブロック下の穴への評価 | `-7.0` |
| `covered_hole_cells` | 穴の上を覆うブロック数への評価 | `-1.25` |
| `bumpiness` | 隣接列間の高さ差への評価 | `-0.25` |

負の値をより小さくすると、その悪化を強く嫌う。
例えば穴をさらに嫌わせる場合は `holes` を `-10.0` などへ変更する。

## Easy / Normal / Hardとの関係

現段階では全レベルが同じ評価重みを使用する。
レベル差は主に以下で作る。

- 探索深度
- 操作を出すtick間隔
- 可視NEXTの先読み量

これにより評価関数の変更と探索量の変更を分離して比較できる。

## 検証

設定は厳密に検証する。

- `version` と `weights` 以外のトップレベル項目は不可
- 6つの重みは全て必須
- 未知の重みは不可
- 数値以外は不可
- NaN / Infinityは不可

CPUを使用しない通常プレイでは設定内容を読み込まないため、CPU設定の破損でCPU OFFの起動まで妨げない。

## ベンチマーク

ベンチマークJSONには、実際に使用した評価器IDと6つの重みを記録する。

```json
{
  "evaluator": {
    "evaluator_id": "visible-board-v1",
    "weights": {
      "holes": -7.0
    }
  }
}
```

実際の出力には6項目すべて含まれる。
同じseedで重みだけ変更して比較することで、コード変更なしで評価関数の調整結果を確認できる。

## 半自動weight sweep

現在の `standard_cpu.json` を基準に、1つの重みだけを弱めた候補・強めた候補を同じseed列で一括比較できる。

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main --benchmark-weight-sweep normal --benchmark-games 10 --benchmark-max-pieces 200 --benchmark-seed 0
```

既定の `--benchmark-weight-step 0.25` では以下の13候補を作る。

- baseline
- 6重みそれぞれの `lower`
- 6重みそれぞれの `higher`

基準値が0以外なら `0.75x` / `1.25x`、基準値が0なら `-0.25` / `+0.25` を候補にする。
stepは例えば10%なら次のように指定する。

```text
--benchmark-weight-step 0.10
```

全候補は同じseed範囲・同じCPUレベル・同じ配置上限で走る。
結果は既定で `UserData/Logs/cpu-weight-sweep.json` に保存し、`summary_by_candidate` で候補ごとの集計を素早く比較できる。
各候補には完全な個別ベンチマーク結果も保存する。

現段階では結果を見て設定を自動上書きしない。
単純なライン数だけで自動最適化すると、穴・生存性・将来の対戦火力などを犠牲にする可能性があるため、まず比較データを安全に集める段階とする。
