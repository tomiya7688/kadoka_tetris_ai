# Pythonの到達不能コード検査

## 背景と目的

型注釈や無条件の制御移動によって到達できない文を見つけ、意図しない処理の放置を減らします。既存のRuff検査と併せて実行します。

## 方法

開発用依存のPyright 1.1.407で `src`、`tests`、`tools` の `reportUnreachable` をエラーとして検査します。CIは意図的に到達不能なサンプルが検出されることもテストします。型注釈に反する入力を実行時に拒否する6箇所は個別に抑制し、不正入力の回帰テストで防御を確認します。対象全体の抑制や入力検証の削除は行いません。

## 開発者の実行方法

リポジトリのルートで `python -m pip install -r requirements-ci.txt` を実行してください。続いて `python -m pyright` を実行してください。テストの前には `src` をPythonのimportパスに追加します。

PowerShellでは次を実行してください。

```powershell
$env:PYTHONPATH = "src"
python -m unittest tests.test_python_reachability
```

Linuxなどのシェルでは次を実行してください。

```bash
PYTHONPATH=src python -m unittest tests.test_python_reachability
```

新たな診断は発生条件を確認し、必要な防御処理には理由と回帰テストを用意してください。

この検査は静的解析です。実行時の全分岐やC++の到達可能性を保証しません。C++の継続検査はIssue #103の残作業です。
