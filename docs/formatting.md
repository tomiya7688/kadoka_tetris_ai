# 変更ファイルの整形

開発者間の整形差分を抑えるため、Pythonは既存のRuff 0.16.7、C++はclang-format 21.1.8を使用します。バージョンは`requirements-ci.txt`で固定します。ゲーム本体や配布物には追加しません。

repositoryのルートで、既存の開発用仮想環境を有効にしてから次を実行してください。

```powershell
python -m pip install -r requirements-ci.txt
python tools/format_code.py tools/format_code.py tests/test_format_code.py
python tools/format_code.py --check tools/format_code.py tests/test_format_code.py
```

最初のコマンドは準備、次のコマンドは整形、最後のコマンドは書換えなしの検査を行います。C++も同じ入口へファイル名を指定してください。formatterの版が固定値と異なる場合は実行を中止します。

```powershell
python tools/format_code.py core/src/active_piece.cpp
python tools/format_code.py --check core/src/active_piece.cpp
```

実装担当は作業後に今回の変更ファイルだけへ整形を実行し、check、関連テスト、自己レビュー、追加レビューの順に進めてください。他者が作業中のファイルは指定しないでください。引数なしで全体を整形する操作は提供しません。

対象は`core/`、`runtime/`、`benchmarks_cpp/`、`tests_cpp/`、`src/`、`tests/`、`tools/`配下のPython・C/C++ファイルです。生成物、vendor、隠しディレクトリ、cache、link、対象外の拡張子は整形しません。原文保持が必要なサンプルは対象rootの外へ置いてください。CMake・Markdown・YAMLの自動整形はこの入口の対象外です。

Pythonは`pyproject.toml`、C++は`.clang-format`に従います。C++は兄弟repoのLLVM系設定を参考にC++20・4スペース・120桁とし、既存include順と構造化コメントを保持します。

CIはPRのbase/head、mainへのpushのbefore/head間で追加・変更されたsourceだけを検査します。既存sourceの一括整形は行いません。手元でもcommit間の検査ができますが、この指定には未コミット差分が含まれないため、作業直後は上記のファイル指定を使用してください。

```powershell
python tools/format_code.py --check --base origin/main --head HEAD
```

検査が成功すると終了コード0になり、未整形・依存不足・不正なpathは失敗として報告します。導入後も通常のlint・テスト・メモリ安全性CI・配布検証を併用します。
