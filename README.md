# Kadoka Tetris AI

外部コマンドで動作する対戦テトリスとプレイAIの開発プロジェクト。
人間・CPU・外部プログラムが同じ意味的操作インターフェースを使用する。

## アーキテクチャ方針

Kadoka Othello AI / Kadoka Shougi AI で先行している構造へ合わせ、Tetrisもゲーム本体はC++へ移行する。

```text
C++ Core / Runtime
    ↓ observation
Python AI learning / dataset / experiment tooling
    ↓ proposal
C++ Runtime validation
    ↓
canonical next state
```

- **C++**: authoritative game core、Runtime、Headless、高頻度simulation、native AI実行境界
- **Python**: AI学習、dataset生成、評価、実験、weight sweep、変換、研究tooling

AIやGUIはcanonical stateを直接書き換えず、C++ Runtimeへ意味的な操作proposalを渡す。
既存 `src/tetris/core/` はC++移行中の挙動参照として残し、移行完了後のcanonical実装にはしない。

詳細は `docs/cpp-core-migration.md` を参照する。

## 現在の状態

C++ Coreへの移行を開始しています。現在C++側には以下があります。

- ミノ基本形
- ActivePieceと正規化回転
- クロスプラットフォーム固定seedの7-bag
- 盤面、配置判定、固定
- ライン消去
- garbage挿入とoverflow判定
- CMake / CTest
- Linux / Windows CIでのC++ build/test

既存Python実装側には、移行対象・挙動参照として以下の機能があります。

- HOLD、移動・回転・固定・ライン消去を含むGameState
- tick単位の意味的コマンド受付
- キーボード入力とJSON Lines外部入力のadapter
- プレイヤーから見える盤面幾何だけを切り出す不変Observation基盤
- 評価関数型の配置探索AI
- キャラクターAI「かどか」の専用評価基盤
- 2プレイヤー対戦・AI対戦の初期基盤
- Pygameによる最小プレイ画面
- Windows向けPyInstaller `onedir` 配布ビルド基盤

TETR.IO準拠の細部、完全な対戦攻撃処理、入力タイミング、UI、設定画面、外部AI連携、トップAI、およびPython runtimeからC++ runtimeへの切り替えは継続実装中です。

## 標準環境

### Runtime / Core

- C++20
- CMake 3.20+
- 自動テスト: CTest

### Learning / Tooling

- Python 3.11系
- GUI（移行中）: Pygame 2.6.1
- Python自動テスト: `unittest`
- 静的解析: Ruff（correctnessルールから段階導入）
- Architecture checker: `tools/kadoka_rule_checker.py`

### 現行Windows配布

- PyInstaller 6.22.2 `onedir`
- ビルド入口: `build.bat`
- 配布結果: `dist/KadokaTetrisAI/`

現行のWindows配布はまだPython gameplay runtimeを含む移行前経路です。C++ RuntimeがGameState/Applicationまで到達した段階で、配布物もC++ runtimeを含む構成へ切り替える。

ユーザー側にPython・pip・IDE等を要求せず、配布用ディレクトリ一式だけで実行できる状態は維持する。
ZIPファイルそのものの自動生成は必須ではなく、生成された配布用ディレクトリをそのままZIP化して第三者へ渡せればよい。

## AI支援開発

最初に大量のdocsを読むのではなく、`AI_CONTEXT.md` から作業を開始する。

```text
python tools/context_route.py --list
python tools/context_route.py core
python tools/kadoka_rule_checker.py .
```

`docs/context-routing.md` が変更カテゴリから source / tests / docs / validation を直接ルーティングする。
Goal / Required / Acceptance と対象契約・検証方法が十分なら、無関係な探索を続けない。

Kadoka Othello AI / Kadoka Shougi AI は兄弟プロジェクトであり、CI・Runtime境界・benchmark・checkerなどの有効な手法を相互導入する。詳細は `docs/sibling-project-alignment.md` を参照する。

## CI

GitHub Actionsでは、C++ Core品質チェック、Python学習/tooling品質、配布artifactチェックを分離して考える。

### Core + Python CI

PRとmain更新時にUbuntu上で実行する。

1. architecture dependency checker
2. family model metadata検証
3. C++ Core configure/build
4. CTest
5. Python source compile確認
6. Ruff correctness静的解析
7. Python `unittest`

checkerはstyleを重複して判定せず、依存境界など機械的に確定できる規則だけを扱う。

### Windows distribution build

PRとmain更新時にWindows上で実際の配布経路を検証する。

1. C++ Core configure/build
2. CTest
3. `build.bat` 実行
4. Python側自動テスト
5. 現行PyInstaller `onedir` ビルド
6. 凍結EXEのsmoke test
7. `UserData` / Config初期化確認
8. 配布ディレクトリをartifactとして保存

C++ Coreの成功、Python source test成功、distribution artifact成功は別の証拠として扱う。

## C++ Coreビルド

Linux等:

```text
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build-cpp --config Release
ctest --test-dir build-cpp -C Release --output-on-failure
```

Windowsでも同じCMake targetをVisual Studio generator経由でビルドできる。

## Windows配布ビルド

Windowsでリポジトリ直下から次を実行する。

```bat
build.bat
```

現行 `build.bat` は移行中のPython配布経路として以下を行う。

1. `.build-venv` に専用Python環境を作成
2. `requirements-build.txt` の依存を導入
3. Python自動テストを実行
4. PyInstaller `onedir` で `dist/KadokaTetrisAI/` を生成
5. 生成した `KadokaTetrisAI.exe --smoke-test` を実行
6. `UserData/Config` と `UserData/Logs` の初期化を確認

Windows CIではこの前段でC++ Core build/CTestも実行する。

## 開発環境からの現行GUI起動

C++ Runtimeへの接続前は、既存Python GUIを次で起動できる。

PowerShell例:

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main
```

GUIを開かず、UserData初期化だけ確認する場合:

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main --smoke-test
```

主なPlayer 1デフォルト操作は以下。

| キー | 操作 |
| --- | --- |
| Left / Right | 左右移動 |
| Down | ソフトドロップ |
| Space | ハードドロップ |
| Up | 右回転 |
| Z | 左回転 |
| C | HOLD |

キー割り当ては `UserData/Config/input.json` からPlayer 1 / Player 2ごとに変更できる。

## Observation境界

AIや画面認識がゲーム内部状態へ直接依存しないため、ObservationをRuntimeとの公開境界にする。

現在のPython `BoardObservation` は以下だけを保持する。

- 可視フィールドの幅・高さ
- 可視範囲にある固定済みセル
- 可視範囲にある操作中ミノのセル

hidden rows、7-bag、乱数状態、内部GameState参照などはObservationへ含めない。
C++ Runtime移行後はC++側が同等の公開Observationを生成し、Python学習・画面認識・外部AIがその境界を使用する。

## localhost JSONL入力API

外部AI・テストツールから操作する場合、現行Python runtimeでは明示的にポートを指定するとlocalhost限定のTCP APIを起動できる。

```powershell
$env:PYTHONPATH = "src"
python -m tetris.main --api-port 8765
```

配布EXEでも同様に指定できる。

```bat
KadokaTetrisAI.exe --api-port 8765
```

APIはデフォルトでは無効で、指定時も `127.0.0.1` のみにbindする。
1行につき1操作のJSON Lines形式を使用する。

```json
{"player":0,"action":"move_left"}
{"player":0,"action":"rotate_cw"}
{"player":0,"action":"hard_drop"}
```

成功時:

```json
{"ok":true,"queued":true}
```

C++ Runtime移行後も、外部入力はAPI専用の状態遷移を作らず、人間/AI共通のsemantic action境界へ接続する。

## UserData

実行ファイルと同じ場所にユーザー固有データを分離する。

```text
KadokaTetrisAI/
├─ KadokaTetrisAI.exe
├─ UserData/
│  ├─ Config/
│  │  └─ input.json
│  └─ Logs/
└─ runtime dependencies
```

アプリ本体の更新時にも `UserData` を可能な限り引き継げる構造とする。

## 最初に読む資料

通常は次の順で十分。

1. [AI Context](AI_CONTEXT.md)
2. 現在タスク
3. [Context Routing](docs/context-routing.md) の該当route
4. 対象source + matching tests
5. 必要な場合だけ詳細設計・開発予定・評価フィードバック

常に全資料を先読みしない。

## 配置

| 場所 | 責務 |
| --- | --- |
| `core/include/`, `core/src/` | authoritative C++ Tetris Core |
| `tests_cpp/` | C++ Core/Runtime correctness tests |
| `src/tetris/core/` | 移行中の旧Python core・挙動参照 |
| `src/tetris/application/` | 現行Python application。C++ Runtimeへ段階移行 |
| `src/tetris/observation/` | Python学習/tooling向けObservation |
| `src/tetris/ai/`, `src/tetris/cpu/` | AI学習・探索・実験 |
| `src/tetris/benchmark/` | benchmark、weight sweep、分析 |
| `src/tetris/adapters/` | GUI、JSONL API、外部入出力adapter |
| `config/` | ルール・AI重みのJSON |
| `tests/` | Python学習/tooling・移行参照テスト |
| `tools/` | 開発・配布・変換補助ツール |
| `docs/` | 設計、予定、評価 |

## License

このプロジェクトは [MIT License](LICENSE) の下で公開します。
