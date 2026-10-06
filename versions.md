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
- HeadlessRuntimeに複数semantic actionのatomic proposal受付を追加。
- 固定seed・有界実行・trace checksum付きのC++ headless runtime基準benchmarkを追加。
- C++ CIにASan・LSan・UBSanを追加し、リーク検出が失敗するprobeを実行。

## Unreleased - 2026-10-03
- Python learning bridge候補として、opaque handle・可視snapshot・atomic proposal・例外status変換を持つC ABI共有ライブラリを追加。

## Unreleased - 2026-10-04
- C ABI候補を利用するPython学習用APIを追加。immutableな可視snapshot、入力範囲検査、context managerによる解放、固定seed再現性を検証。

## Unreleased - 2026-10-06
- Python learning bridgeとC++ Runtime baselineの同条件benchmarkを追加。トレースchecksum一致を比較条件とし、両者のthroughputと起動時間を分けて出力。
- Windows Release・seed 123・8 players・500 ticks/playerでtraceが一致。decision roundtripはnative約365,551/s、Python約4,454/s（この計測条件で約82倍差）。
