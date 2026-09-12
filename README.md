# Tetris

外部コマンドで動作する対戦テトリスとプレイAIの開発プロジェクト。
人間・CPU・外部プログラムが同じ操作インターフェースを使用する。

## 現在の状態
初期資料とディレクトリ構成のみ。ゲーム本体・AI・起動コマンドは未実装。

当面の標準環境は以下とする。

- Python 3.11系
- GUI: Pygame
- テスト: pytest
- Windows配布: PyInstaller `onedir`
- ビルド入口: `build.bat` または同等の1コマンドビルダー
- 配布結果: `dist/KadokaTetrisAI/` のような自己完結した配布用ディレクトリ

ユーザー側にPython・pip・IDE等を要求せず、配布用ディレクトリ一式だけでEXEを起動できる状態を維持する。
ZIPファイルそのものの自動生成は必須ではなく、生成された配布用ディレクトリをそのままZIP化して第三者へ渡せればよい。

Python/Pygame/PyInstaller構成は現時点の採用案であり固定ではない。常時配布可能性、保守性、UI、API連携、CIなどで明確な問題が継続する場合は、実装規模が小さいうちにGodot等への移行を検討する。

依存パッケージは、実装時に検証したバージョンを requirements.txt に記録する。

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
| src/tetris/core/ | 盤面、ミノ、乱数、状態遷移 |
| src/tetris/application/ | コマンド受付、固定刻みの進行、対戦調整 |
| src/tetris/ai/ | 観測から操作を選ぶプレイAI |
| src/tetris/adapters/ | キーボード、外部入出力、Pygame表示 |
| config/ | ルール・AI重みのJSON |
| tests/ | GUI不要の自動テスト |
| docs/ | 設計、予定、評価 |

設定スキーマと実行入口は、それぞれの機能実装時に追加する。

## License

このプロジェクトは [MIT License](LICENSE) の下で公開します。
