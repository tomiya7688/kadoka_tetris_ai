# 開発エージェント向けルール

作業開始時はまず `AI_CONTEXT.md` と現在タスクを読み、`docs/context-routing.md` から対象routeを選ぶ。このroute文書をサブシステム索引（project map）として使い、重複する索引は作らない。
全docs・全Issue・全履歴を先に読まない。Gitのstatus・差分規模・remote deltaを確認し、対象sourceとmatching testsを優先する。関連Issueや詳細資料は必要なものだけ読む。
`docs/開発予定.md` と評価フィードバックは、予定選択・「次へ」・該当機能の評価を扱う時に読む。
今回の作業箇所に関する既存変更も確認し、ユーザーの変更を上書き・削除しない。

- Goal / Required / Acceptance evidence / affected boundary が揃ったら広い探索を止める。新たな疑問、失敗、未知の影響が出た時だけ必要範囲を追加で調べる。
- 静的解析で判定できることはchecker/searchに任せ、繰り返す確認はまとめ、必要なファイル範囲だけ読む。長いコマンド出力やログは判定結果・要点・参照先に圧縮し、成功ログを会話へ繰り返し載せない。
- **authoritative gameplay core / runtime はC++で実装する。** 新しいゲームルールをPython coreだけへ追加しない。
- **PythonはAI学習・dataset生成・評価・実験・変換・研究toolingを主責務とする。** C++ CoreからPython学習コードへ逆依存しない。
- 既存 `src/tetris/core/` はC++移行中の挙動参照であり、移行完了後のcanonical state ownerにしない。
- 1クラス1ファイル、1クラス1責務、1関数1処理。
- GUI・コア・プレイAIを分離し、人間とAIは同じ意味的コマンドで操作する。
- AI出力は提案であり、canonical stateを直接書き換えない。C++ Core/Runtimeの権威ある検証経路を通す。
- gameplay/runtimeからbenchmark・training・dataset analysisへ逆依存しない。
- ツモ制約を守る。AIに未公開の将来ツモや内部乱数状態を渡さない。
- 軽い設計は docs/設計書.md、詳細は docs/機能名/機能説明書.md に書く。
- 表はMarkdown、図はMermaidを使う。
- 「次へ」は予定とフィードバックを確認し、次の小さな検証可能な項目を進める。
- CI/build/release、AI共通I/F、Runtime/tooling境界、benchmark、model/package、checkerを大きく変更する前に `docs/sibling-project-alignment.md` を見て兄弟repoの現行方式を短く確認する。盲目的にはコピーしない。
- C++ Core/Runtime変更はCMake build + CTestを基本検証とし、必要に応じて既存Python testsを移行参照として使う。
- Python学習/tooling変更はcompileall / Ruff / unittestを基本検証とする。
- 機能を追加する際は作業ブランチで実装・テストし、mainへの反映とGitHub更新を行う。
  初回はGitの状態・remote・公開先を確認する。公開先不明なら推測でリポジトリを作らない。
  無関係なファイルをコミットしない。強制pushや既存変更の破棄はしない。
- **このプロジェクトは開発中の常時配布可能性を品質条件とする。** main は原則として、いつでも第三者向け配布ビルドを生成できる状態に保つ。
- 配布ビルドは `build.bat` などの単一入口、または同等のビルダー1コマンドで生成できるようにする。複数の手作業やIDE固有操作を必須にしない。
- 配布対象は、ユーザー側にPython・pip・IDE等の開発環境を要求せず、**生成された配布用ディレクトリ一式をそのままZIP化して第三者へ渡せる状態**を目標とする。ZIPファイル自体の自動生成は必須ではない。
- 実装変更後は、可能な限り通常の自動テストに加えて配布ビルドを生成し、少なくとも起動確認・必須ファイル存在確認・設定/UserData初期化などの簡易スモークテストを実行する。
- Codexは作業完了前に、原則として「checker/targeted tests → C++ Core CTest → Python通常テスト → 配布に影響する場合は配布ビルド → 配布物スモークテスト」の順で検証する。
- 新しい依存関係やアセット、パス処理、設定方式を追加するときは、開発環境だけでなく配布ビルドでも動作するかを確認する。絶対パスやローカル環境固有設定への依存を作らない。
- ランダム性を含むAI改善・benchmarkは、同じseed群・同じ条件・bounded runtimeで比較する。
- 完了した項目は開発予定から削除する。部分完了は未完了部分を残す。
- 対応済みフィードバックは過去のフィードバック.mdへ移してから元の項目を削除する。
- 実行した検証と未検証事項を報告する。GUI未確認をGUI動作確認済みと書かない。配布ビルドを生成していない場合も、生成済みと書かない。
