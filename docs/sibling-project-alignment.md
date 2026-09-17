# 兄弟プロジェクト連携方針

Kadoka Tetris AI / Kadoka Othello AI / Kadoka Shougi AI は兄弟プロジェクトとして、実績のある開発手法・CI・境界設計を相互に取り込みます。ただしゲーム固有ルールやAIアルゴリズム自体を無理に共通化しません。

## 共通原則

- canonicalなゲーム状態はC++ coreが所有する。
- AI出力は提案であり、human入力と同じ権威ある検証・状態遷移を通す。
- correctness before strength。
- gameplay/runtime hot pathからtraining / Creator / dataset conversion / rich analysisを分離する。
- RNG/時刻等は可能な限り明示的なseed・入力・tickで再現可能にする。
- GUIより先にheadless/structured validationを使う。
- hot pathでは測定根拠のある局所最適化を許可するが、依存方向を逆転させない。

## Tetrisの言語境界

Othello / Shougi の先行構造へ合わせ、TetrisもRuntime/CoreはC++を正本とします。

```text
C++ Core / Runtime
        ↓ observation
Python AI learning / dataset / experiment tooling
        ↓ proposal
C++ Runtime validation
        ↓
canonical next state
```

Pythonは学習・dataset・評価・実験・変換などに使います。C++ native hot pathへPython callbackを必須にしません。

既存 `src/tetris/core/` はC++移行中の挙動参照であり、移行完了後のcanonical runtime実装にはしません。

## 共通AI backend vocabulary

兄弟プロジェクトでは、AIの実行方式を次の共通カテゴリで表します。

- `native`
- `dynamic_library`
- `external_process`
- `script`
- `network`

これはAIの強さや探索方式ではなく、RuntimeからAIを呼ぶtransport/execution方式を表します。

Tetrisでは、

```text
Observation
    ↓
AI backend / adapter
    ↓
semantic command
    ↓
authoritative C++ game core
```

へ揃えます。backendが内部状態を直接変更することはありません。

外部process/scriptはCoreへ混ぜず、Runtime/adapter層に置きます。大量simulationでは毎判断process spawnする方式を標準にせず、persistent sessionまたはnative/in-process経路を優先します。

## 他兄弟から取り込むもの

### Kadoka Othello AI

- `AI_CONTEXT.md` + Context Routingによるコンテキスト削減
- Runtime / Creator-tooling分離
- 機械判定可能な規約だけを短く出すrule checker
- model/runtimeと開発解析処理の分離
- C++ Runtimeを中心にしたheadless大量実行

### Kadoka Shougi AI

- correctness-before-strengthの明文化
- AI/engine結果はcore検証前は非権威
- 小さい再現局面による回帰テスト
- core/runtime/protocolの一方向依存
- `AIBackend` によるnative/process/script/network共通Runner境界
- C++ Core / Runtime と外部toolingの分離

### Kadoka Tetris AIから兄弟へ返すもの

- explicit seed + integer tickによる決定性
- source CIと配布artifact CIを別証拠として扱う
- `build.bat` 1コマンド配布ビルド
- 生成配布物そのもののsmoke test
- 実施していないGUI/配布検証を「確認済み」と書かない運用

## 兄弟確認を行う変更

以下を新設・大幅変更するときは、兄弟repoの現行実装を短く確認してから決めます。

- CI/build/release
- AI共通I/F
- Runtime/tooling境界
- benchmark方法
- model/package形式
- coding-rule checker
- distribution/artifact validation

目的はコード共有そのものではなく、同じ問題を3回別々に解くことを避けることです。
