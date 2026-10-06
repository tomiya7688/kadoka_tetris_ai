# C++ Runtime C ABI candidate

Issue #37のin-process bridge候補です。Pythonの`ctypes.CDLL`から呼べるC ABIを共有ライブラリとして提供します。Python学習APIは`src/tetris/learning/`にあります。正式transportの選択と比較benchmarkは未完了です。Core/RuntimeにPythonの依存はありません。

## Build and contract

通常のCMake buildで`kadoka_tetris_bridge.dll`（Windows）、`libkadoka_tetris_bridge.so`（Linux）が生成されます。Windows Releaseでは`build-cpp/Release/`にあります。C headerの正本は`runtime/include/kadoka/tetris/runtime/c_api.h`です。

- ABI versionは1。consumerは`kt_abi_version()`と`kt_observation_size()`を照合します。構造体には固定幅整数だけを使用し、自然alignment・cdeclで呼び出します。異なるbitness、packing、ABI versionを混ぜません。
- 初期候補は10×20可視盤面・hidden 2行・NEXT 5個の標準設定のみ。1〜64 playerのseedを`kt_create()`へ渡します。
- `kt_observe()`は可視盤面のrow-major mask、active/hold/NEXT、進行metadata、現在tickをcaller-owned bufferへコピーします。hidden行、bag、RNGは公開しません。失敗時はbufferを変更しません。
- `kt_observe_many()`は全playerのsnapshotをcaller-owned配列へ一括コピーします。countはruntimeのplayer数と一致させます。失敗時は配列を変更しません。
- `kt_submit()`は意味的action列をC++のatomic proposal検証へ渡します。proposalの長さは0〜4096。適用は`kt_advance()`で行います。空proposalはNULL actionsを許可します。
- `kt_submit_many()`は最大64 proposal、合計4096 actionを一括検証して登録します。action範囲、player、tick、sequence、action値のどれかが不正なら、batch全体を登録しません。
- Runtimeはgame over後のactionを無視します（command処理数には含めます）。同じproposalの途中でtop outしても、後続actionでterminal stateを変更しません。
- statusはOK、invalid argument、out of range、out of memory、internal errorの5種類。C++例外はABI境界でstatusへ変換します。
- `kt_create()`成功ごとに`kt_destroy()`を一度呼びます。NULL destroyは許可します。create失敗時のhandleはNULLです。
- handleはopaqueな所有権tokenです。consumerは改造、二重解放、解放後の利用をしてはいけません。非NULLのpointerは有効な指定型の領域を指す必要があり、不正pointer自体の安全性をC ABIは保証しません。
- 同じhandleの呼び出しは直列化します。独立workerは独立handleを所有します。snapshotの書き換えはcanonical stateへ影響しません。

共有ライブラリは学習用の候補artifactです。既存GUI配布にはまだ組み込みません。Windows/Linux CIでは、実際の共有ライブラリにlinkしたC++ consumerとPython wrapperを実行します。worker scalingは未計測です。

## Python learning API

Python学習・dataset・評価toolingだけが利用するAPIです。GUIやnative gameplayにはPythonを必須にしません。標準ライブラリの`ctypes`だけを使用し、Python coreへのfallbackはありません。

```python
from tetris.learning import NativeRuntime

# Callerが生成済みライブラリのpathを選ぶ。検索pathへの自動fallbackはしない。
with NativeRuntime("build-cpp/Release/kadoka_tetris_bridge.dll", [123, 456]) as runtime:
    observation = runtime.observe(0)
    runtime.submit(0, observation.tick, 0, ["rotate_cw", "hard_drop"])
    processed_tick, commands_processed = runtime.advance()
    next_observation = runtime.observe(0)
```

Linuxではpathを`build-cpp/libkadoka_tetris_bridge.so`へ変更します。実行時は`PYTHONPATH=src`を設定します。構造体のABI versionとsizeを生成前に照合し、不一致はエラーにします。

複数playerでは`observe_many()`で全snapshotを受け取り、`submit_many(tick, [(player, first_sequence, actions), ...])`で一括登録できます。batch APIはforeign-function call回数を減らし、proposal全体を原子的に検証します。

- `LearningObservation`はfrozen dataclassで、maskはimmutableな`bytes`、NEXTは`tuple`です。native memoryへの参照は返しません。
- action名は`move_left`、`move_right`、`rotate_cw`、`rotate_ccw`、`soft_drop`、`hard_drop`、`hold`です。
- seeds/tick/sequenceはuint64、playerはuint32の範囲をPython側でも検査し、ctypesによる負数・巨大整数のwrapを防ぎます。boolや浮動小数も受け付けません。
- proposal検証はC++が正本です。重複sequence・overflow・過去tick等は`ValueError`、observationの範囲外playerは`IndexError`になります。
- `with`または`close()`で解放します。closeは複数回呼べます。終了済みinstanceの操作は`RuntimeError`です。忘れたcloseの補助としてfinalizerもありますが、通常は明示的に閉じます。
- 同一instanceの呼出しとcloseはlockで直列化します。worker間でhandleを共有・転送せず、それぞれ独立instanceを生成します。observe→submit→advanceの一連の手順全体がtransactionになるわけではありません。

targeted tests:

```powershell
$env:PYTHONPATH = "src"
$env:KADOKA_TETRIS_BRIDGE = "build-cpp/Release/kadoka_tetris_bridge.dll"
python -m unittest discover -s tests -p 'test_native_runtime*.py' -v
```

通常のPython-only環境ではlibrary指定がなければintegration testsだけskipします。CIではlibrary pathを必ず指定し、存在しない・ABI不一致の場合はfailします。ABI不一致のunit testsは常に実行します。

## Evidence

`tests_cpp/c_api_test.cpp`はReleaseでも無効にならないchecksで、32 seed × 32 tickのnative Runtimeとの全可視field parity、copy isolation、独立handle、複数player、invalid proposalのatomic rejection、重複sequence・overflow・過去tick・NULL・buffer sizeを検証します。handleはRAIIで解放し、同じCTestをASan/LSan/UBSan CIでも実行します。

兄弟Othelloの現行CMakeではRuntimeとCreatorを別targetに分離しています。この依存方向を確認し、TetrisではPython headersを要求せず、C ABI adapterだけを別shared targetにしました。
