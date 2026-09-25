# C++ Headless Runtime（初期境界）

`kadoka_tetris_runtime` はC++ Coreの上位に置く決定論的な意味的コマンド実行層。各プレイヤーのcanonical stateはC++ `GameState` が所有し、Runtimeはその状態を直接書き換えるAI APIを公開せず、const参照で読み取る。

## コマンド

`SemanticCommand` はplayer、tick、sequence、actionを持つ。actionは `move_left`、`move_right`、`rotate_cw`、`rotate_ccw`、`soft_drop`、`hard_drop`、`hold` に対応する。存在しないplayer、過去tick、同じplayer/tick内で重複するsequence、不正actionは受付時に拒否する。同tickの順序はplayer番号、sequence番号で決定する。

`advance()` は現在tickのコマンドを適用し、コマンドがないtickでもtickを1つ進める。同一seed・同一コマンド列は同一状態列を生成する。tick進行や意味的入力をGUIと壁時計から独立させる。

## 今回の境界

これは単独盤面のheadless runtimeと共有コマンド経路の初期実装である。重力・lock delay、対戦combat調停、AIBackend transport、Python bridge、JSONL transportは含めない。後続工程は同じC++ state transition入口へ接続し、C++ CoreへのPython依存を追加しない。

