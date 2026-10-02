# Versions

## Unreleased - 2026-09-09
- 初期評価関数（消去行数・穴・総高さ・凹凸）を追加。
- ワークフロー文書と実装手順に従い、GUI非依存のテストを追加。
- GitHub Issue確認、ブランチ作成、PRはGit未初期化のため未実施。

## Unreleased - 2026-09-25
- 可視NEXT内の配置候補をseed付きロールアウトで比較するMonte Carlo plannerを追加。
- C++ Core上で意味的コマンドを固定tick処理するheadless runtime初期版を追加。

## Unreleased - 2026-09-26
- C++ Runtimeからhidden rowsとbag/RNGを除いたplayer-visible observationを生成。
- AI_CONTEXT・route索引・ワークフローにタスク単位のコンテキスト削減と段階的検証の手順を反映。

## Unreleased - 2026-09-28
- HeadlessRuntimeからプレイヤー別の可視Observationを値コピーで取得可能にした。

## Unreleased - 2026-09-29
- Python学習bridgeに向け、C++ Observationへactive piece位置・回転とプレイ進行metadataを追加。

## Unreleased - 2026-10-02
- Issue #37に向けてPython learning bridgeの責務境界とtransport比較ベンチ条件を設計。
