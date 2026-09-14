# Kadoka Tetris AI

外部コマンドで動作する対戦テトリスとプレイAIの開発プロジェクト。
人間・CPU・外部プログラムが同じ意味的操作インターフェースを使用する。

## 現在の状態

初期のコア実装が進行中です。現在は以下の土台があります。

- 盤面、7-bag、ミノ、HOLD、移動・回転・固定・ライン消去
- tick単位の意味的コマンド受付
- キーボード入力とJSON Lines外部入力のadapter
- 評価関数型の配置探索AI
- キャラクターAI「かどか」の専用評価基盤
- 2プレイヤー対戦・AI対戦の初期基盤
- Pygameによる最小プレイ画面
- Windows向けPyInstaller `onedir` 配布ビルド基盤

TETR.IO準拠の細部、完全な対戦攻撃処理、入力タイミング、UI、設定画面、外部AI連携、トップAIなどは継続実装中です。

## 標準環境

- Python 3.11系
- GUI: Pygame 2.6.1
- 自動テスト: Python `unittest`
- 静的解析: Ruff（correctnessルールから段階導入）
- Windows配布: PyInstaller 6.22.2 `onedir`
- ビルド入口: `build.bat`
- 配布結果: `dist/KadokaTetrisAI/`

ユーザー側にPython・pip・IDE等を要求せず、配布用ディレクトリ一式だけでEXEを起動できる状態を維持する。
ZIPファイルそのものの自動生成は必須ではなく、生成された配布用ディレクトリをそのままZIP化して第三者へ渡せればよい。

Python/Pygame/PyInstaller構成は現時点の採用案であり固定ではない。常時配布可能性、保守性、UI、API連携、CIなどで明確な問題が継続する場合は、実装規模が小さいうちにGodot等への移行を検討する。

## CI

GitHub Actionsでは、通常品質チェックと配布チェックを分離する。

### Python CI

PRとmain更新時にUbuntu上で高速に実行する。

1. Python 3.11セットアップ
2. `src` / `tests` / `tools` の構文コンパイル確認
3. Ruffによるcorrectness静的解析
4. 全`unittest`実行

既存コードには旧来の圧縮された記述が残っているため、現段階ではフォーマット全強制を行わず、実害のある静的解析から段階的に厳しくする。

### Windows distribution build

PRとmain更新時にWindows上で実際の配布経路を検証する。

1. `build.bat` 実行
2. 全自動テスト
3. PyInstaller `onedir` ビルド
4. 凍結EXEのsmoke test
5. `UserData` / Config初期化確認
6. 配布ディレクトリをartifactとして保存

## Windows配布ビルド

Windowsでリポジトリ直下から次を実行する。

```bat
build.bat
```

`build.bat` は以下を順番に行う。

1. `.build-venv` に専用Python環境を作成
2. `requirements-build.txt` の依存を導入
3. 自動テストを実行
4. PyInstaller `onedir` で `dist/KadokaTetrisAI/` を生成
5. 生成した `KadokaTetrisAI.exe --smoke-test` を実行
6. `UserData/Config` と `UserData/Logs` の初期化を確認

成功した `dist/KadokaTetrisAI/` は、そのディレクトリ一式をZIP化して配布できる形を目標とする。

## 開発環境からの起動

`src` をPythonパスに追加して起動する。

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

現段階のPygame画面は最小実装で、完全なゲームUIや自動重力・ロック遅延等は今後拡張する。

## localhost JSONL入力API

外部AI・テストツールから操作する場合、明示的にポートを指定するとlocalhost限定のTCP APIを起動できる。

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

不正な操作・未知プレイヤー・未知フィールド等はエラーとして返す。

APIからtick、sequence、ゲーム内部状態などを指定する方式にはせず、外部入力はキーボード入力と同じ `InputAction` を経由し、アプリ側が現在tickとsequenceを割り当てる。
これによりAPI専用のゲーム処理を作らず、入力経路を共通化する。

## UserData

実行ファイルと同じ場所にユーザー固有データを分離する。

```text
KadokaTetrisAI/
├─ KadokaTetrisAI.exe
├─ UserData/
│  ├─ Config/
│  │  └─ input.json
│  └─ Logs/
└─ PyInstallerが生成するランタイム・依存ファイル
```

アプリ本体の更新時にも `UserData` を可能な限り引き継げる構造とする。

## 最初に読む資料

- [作業ルール](AGENTS.md)
- [コーディングルール](docs/コーディングルール.md)
- [開発AI用チートシート](docs/AI用チートシート.md)
- [簡単な設計書](docs/設計書.md)
- [既存の開発予定](docs/開発予定.md)
- [実装手順](docs/実装手順.md)
- [評価者からのフィードバック](docs/評価/評価者からのフィードバック.md)

## 配置

| 場所 | 責務 |
| --- | --- |
| `src/tetris/core/` | 盤面、ミノ、乱数、状態遷移 |
| `src/tetris/application/` | コマンド受付、意味入力ルーティング、固定刻みの進行、対戦調整 |
| `src/tetris/ai/` | 観測から操作を選ぶプレイAI |
| `src/tetris/adapters/` | キーボード、JSONL API、外部入出力、Pygame表示 |
| `config/` | ルール・AI重みのJSON |
| `tests/` | GUI不要の自動テスト |
| `tools/` | 開発・配布補助ツール |
| `docs/` | 設計、予定、評価 |

## License

このプロジェクトは [MIT License](LICENSE) の下で公開します。
