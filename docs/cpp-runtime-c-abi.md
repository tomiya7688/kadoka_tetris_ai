# C++ Runtime C ABI candidate

Issue #37のin-process bridge候補です。Pythonの`ctypes.CDLL`から呼べるC ABIを共有ライブラリとして提供します。正式transportの選択、Python学習API、比較benchmarkは次の作業です。Core/RuntimeにPythonの依存はありません。

## Build and contract

通常のCMake buildで`kadoka_tetris_bridge.dll`（Windows）、`libkadoka_tetris_bridge.so`（Linux）が生成されます。Windows Releaseでは`build-cpp/Release/`にあります。C headerの正本は`runtime/include/kadoka/tetris/runtime/c_api.h`です。

- ABI versionは1。consumerは`kt_abi_version()`と`kt_observation_size()`を照合します。構造体には固定幅整数だけを使用し、自然alignment・cdeclで呼び出します。異なるbitness、packing、ABI versionを混ぜません。
- 初期候補は10×20可視盤面・hidden 2行・NEXT 5個の標準設定のみ。1〜64 playerのseedを`kt_create()`へ渡します。
- `kt_observe()`は可視盤面のrow-major mask、active/hold/NEXT、進行metadata、現在tickをcaller-owned bufferへコピーします。hidden行、bag、RNGは公開しません。失敗時はbufferを変更しません。
- `kt_submit()`は意味的action列をC++のatomic proposal検証へ渡します。proposalの長さは0〜4096。適用は`kt_advance()`で行います。空proposalはNULL actionsを許可します。
- Runtimeはgame over後のactionを無視します（command処理数には含めます）。同じproposalの途中でtop outしても、後続actionでterminal stateを変更しません。
- statusはOK、invalid argument、out of range、out of memory、internal errorの5種類。C++例外はABI境界でstatusへ変換します。
- `kt_create()`成功ごとに`kt_destroy()`を一度呼びます。NULL destroyは許可します。create失敗時のhandleはNULLです。
- handleはopaqueな所有権tokenです。consumerは改造、二重解放、解放後の利用をしてはいけません。非NULLのpointerは有効な指定型の領域を指す必要があり、不正pointer自体の安全性をC ABIは保証しません。
- 同じhandleの呼び出しは直列化します。独立workerは独立handleを所有します。snapshotの書き換えはcanonical stateへ影響しません。

共有ライブラリは学習用の候補artifactです。既存GUI配布にはまだ組み込みません。Windows/Linux CIのCMake buildは実際の共有ライブラリにlinkしたconsumerを実行します。Python wrapper、配布物への同梱、transport比較・worker scalingは未実装です。

## Evidence

`tests_cpp/c_api_test.cpp`はReleaseでも無効にならないchecksで、32 seed × 32 tickのnative Runtimeとの全可視field parity、copy isolation、独立handle、複数player、invalid proposalのatomic rejection、重複sequence・overflow・過去tick・NULL・buffer sizeを検証します。handleはRAIIで解放し、同じCTestをASan/LSan/UBSan CIでも実行します。

兄弟Othelloの現行CMakeではRuntimeとCreatorを別targetに分離しています。この依存方向を確認し、TetrisではPython headersを要求せず、C ABI adapterだけを別shared targetにしました。
