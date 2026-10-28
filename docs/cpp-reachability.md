# C++の到達不能コード検査

## 背景と目的

意図せず実行できなくなった文を早期に見つけるため、CIでC++のコンパイラ警告を検査します。

## 検査方法

GitHub-hosted Ubuntu 24.04のClang 18でCMakeの全ターゲットをRelease構成でビルドします。`-Wunreachable-code-aggressive`で到達不能コードを検出し、`-Werror=unreachable-code -Werror=unreachable-code-aggressive`で該当警告をエラーにします。CIは意図的に到達不能な文が同じ設定で拒否されることを先に確認し、コンパイルデータベースで全C++ソースへのフラグ適用と無効化の有無を検査します。追跡中の `.h` と `.hpp` はそれぞれ主入力として、C APIのビルド用マクロを有効・無効にした両方で検査します。意図的な到達不能文を含むヘッダーが拒否されることも確認します。ビルド後にCTestを実行します。

## 開発者の実行方法

Linux環境にClang 18とCMakeを用意し、リポジトリのルートからBashで次を実行してください。

```bash
(
set -euo pipefail
while IFS= read -r -d '' header; do
  for macro in '' '-DKADOKA_TETRIS_C_API_BUILD'; do
    clang++-18 -std=c++20 -DNDEBUG -Wunreachable-code-aggressive \
      -Werror=unreachable-code -Werror=unreachable-code-aggressive \
      -Icore/include -Iruntime/include -x c++ -fsyntax-only ${macro:+"$macro"} "$header"
  done
done < <(git ls-files -z -- '*.h' '*.hpp')
cmake -S . -B build-cpp-reachability -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCMAKE_CXX_COMPILER=clang++-18 -DCMAKE_CXX_FLAGS="-Wunreachable-code-aggressive -Werror=unreachable-code -Werror=unreachable-code-aggressive"
cmake --build build-cpp-reachability --config Release --parallel 2
ctest --test-dir build-cpp-reachability -C Release --output-on-failure
)
```

この検査は静的解析です。ヘッダーの個別検査はLinuxのRelease相当の設定で行います。インクルード順や他のマクロ、プラットフォームに依存する構成、未実体化テンプレート、実行時条件による到達可能性は保証しません。警告を確認するときは、意図的な防御処理と実際に到達できない処理を区別してください。
