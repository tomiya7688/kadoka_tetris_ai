# AIモデルメタデータ

Kadoka Tetris AI は兄弟プロジェクト共通の `kadoka.ai_metadata.v1` を採用する。

これは **モデル/AIの横断メタデータ** であり、現在のPython設定形式や将来のC++ Runtime用model/package形式そのものを固定するものではない。ゲーム固有の重み、探索設定、planner、実行モデル等はTetrisに適した形式を使ってよい。

## 必須項目

```json
{
  "format": "kadoka.ai_metadata.v1",
  "model_id": "kadoka.tetris.example",
  "model_name": "Kadoka Tetris Example",
  "model_version": "0.1.0",
  "architecture": "heuristic_planner",
  "game": "tetris",
  "license": "MIT"
}
```

意味は3兄弟で共通とする。

- `format`: `kadoka.ai_metadata.v1`
- `model_id`: 安定した機械可読ID
- `model_name`: 表示名
- `model_version`: モデル/パッケージ版
- `architecture`: 高水準のAI方式
- `game`: `tetris`
- `license`: 文字列またはobject。技術モデルとキャラクターのライセンスが異なる場合はobjectを使う。

## 共通optional項目

- `format_version`
- `variant`
- `runtime_requirements`
- `search_config`
- `training_recipe`
- `dataset_provenance`
- `determinism`
- `benchmark_results`
- `source`
- `distribution`
- `created_at`

Tetris固有の追加項目は許可するが、共通名の意味は兄弟間で変えない。

## Tetrisでの利用

特に以下を記録する。

- planner / evaluator / policy等のarchitecture
- 判断能力とHuman Execution Model等の実行モデルを分離した設定
- seed対応と再現モード
- Observation仕様版
- search/node budget条件
- benchmarkのDecision / Search / Execution条件
- 学習Datasetのprovenance
- bundled / downloaded / user-trained / externalの由来

## 将来C++移行との関係

Issue #20 のC++移行後もこのファイルの意味は維持する。

```text
metadata.json
   -> model catalog / training / benchmark / distribution情報

C++ Runtime package/model
   -> 実際の推論・探索・実行に必要な形式
```

Runtime hot pathが毎手このmetadataを解析する設計にはしない。

## ルール

1. Runtime/package manifestが実行時の正本。
2. metadataへ巨大weight/datasetを直接入れない。
3. 絶対パス、秘密情報、一時ログを入れない。
4. benchmarkは条件・hardware・versionを識別可能にする。
5. Datasetは可能ならdataset ID/hash/recipeを残す。
6. キャラクターライセンスと技術モデルのライセンスを区別可能にする。

`models/examples/family_metadata.json` をCIで検証する。
