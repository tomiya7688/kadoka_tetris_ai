# C++ 可視Observation

`observe_player(const GameState&)` は値コピーの `PlayerObservation` を生成する。`HeadlessRuntime::observe(player)` からプレイヤー番号を指定して取得できる。盤面は可視高さと可視座標（上端をy=0）で表し、hidden rowsの固定セルは含めない。操作中ミノは可視範囲内のセルだけを `active_cells` に含め、種別・x・可視座標y・rotationも返す。HOLD/hold-used、表示NEXT、game-over、消去行・combo・B2B・lock数を含め、学習consumerが合法手判断に必要な状態を取得できる。

Observation型はBoard/GameStateへの参照、bag、seed、RNG状態を保持しない。AIやPython bridgeへはこのスナップショットを渡し、戻り値はsemantic action proposalとしてC++ Runtimeで検証する。

外部向けのJSON schema/transport、対戦相手情報、combat meterは別工程で定義する。
