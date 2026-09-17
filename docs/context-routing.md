# Context Routing

変更内容から、最初に読む source / tests / docs / validation を絞るための地図です。全資料を先に読まず、共有契約へ影響するときだけ範囲を広げます。

## core

盤面、ツモ、移動、回転、ロック、消去、ゲームオーバー等。

- Authoritative Source: `core/include/`, `core/src/`
- C++ Tests: `tests_cpp/`
- Migration reference only: `src/tetris/core/`, `tests/test_core.py`, `tests/test_game_state.py`
- Docs: `docs/cpp-core-migration.md`, `docs/コーディングルール.md`
- Validation: 対象CTest -> C++ core全体 -> parityに関係するPython test
- Rule: 新しいゲームルールをPython coreだけへ追加しない

## commands-runtime

人間/AI共通の意味的コマンド、対戦進行、アプリケーション調停。

- Target Source: C++ Runtime（core移行に合わせて追加）
- Migration source: `src/tetris/application/`, `src/tetris/adapters/`
- Tests: C++ runtime testsを優先し、既存Python testsを移行参照にする
- Invariant: 人間とAIは同じ権威あるC++状態遷移を通る
- Validation: deterministic input/seedを優先

## ai-runtime

AI backend、proposal、外部process/script transport、authoritative command境界。

- Target: C++ Runtime backend boundary
- Python role: 学習backend、dataset、評価・実験用adapter
- Current migration source: `src/tetris/application/ai_backend.py`, `src/tetris/application/ai_runner.py`, `src/tetris/application/command.py`, `src/tetris/application/ai_match.py`
- Tests: runtime境界のC++ testsを追加しつつ、`tests/test_ai_backend_runtime.py`, `tests/test_ai_match.py`, `tests/test_commands.py` を挙動参照にする
- Docs: `docs/ai-runtime-backend.md`, `docs/sibling-project-alignment.md`
- Invariant: AIはproposalのみ返し、状態遷移はC++ Runtime/Coreが所有する
- Performance: native backendへPython/process/serialization overheadを持ち込まない

## ai-learning

AI学習、dataset生成、weight sweep、研究実験。

- Source: `src/tetris/ai/`, `src/tetris/cpu/`, `src/tetris/benchmark/` と今後のtraining modules
- Language: Pythonを標準とする
- Runtime access: C++ Runtimeのobservation/action bridge経由
- Invariant: Python学習コードがcanonical game stateを独自実装しない
- Validation: fixed seed / fixed config / bounded games

## combat

攻撃、garbage、combo、B2B、T-Spin等。

- Target Source: C++ Core/Runtime
- Migration reference: Python core/application内のcombat関連実装
- Tests: C++ deterministic combat tests + `tests/test_attack.py`, `tests/test_combat_events.py`, `tests/test_garbage.py` を移行参照

## observation

AIへ渡す観測、可視化用観測。

- Target producer: C++ Runtime
- Python consumer/tooling: `src/tetris/observation/`
- Existing reference: `src/tetris/application/ai_backend.py::public_observation`
- Invariant: hidden future pieces / internal RNG stateを漏らさない

## benchmark

CPU評価、weight sweep、計測。

- Runtime benchmark: C++
- 学習・集計・可視化: Python
- Source: `src/tetris/benchmark/`, 関連AI実装
- Validation: fixed seeds / fixed config / bounded games。同一条件以外の数値を直接比較しない

## distribution

C++ Runtime、Python tooling/UI、PyInstallerまたは後続packaging、runtime path、設定/UserData、配布物。

- Source: `CMakeLists.txt`, `build.bat`, `tools/distribution/`, `src/tetris/runtime_paths.py`, `requirements-build.txt`
- CI: `.github/workflows/windows-build.yml`
- Validation: C++ build/test + source tests + 生成artifact smoke

## build-policy

CI、ruff、CMake、checker、依存境界、開発ルール。

- Source: `.github/workflows/`, `CMakeLists.txt`, `pyproject.toml`, `tools/kadoka_rule_checker.py`, `AGENTS.md`
- Docs: `docs/コーディングルール.md`, `docs/sibling-project-alignment.md`, `docs/cpp-core-migration.md`
- Validation: checker -> C++ build/CTest -> compileall -> ruff -> unittest

## Broadening Rules

次の場合は全体検証へ広げます。

- core/public command contract変更
- C++/Python bridge変更
- observation contract変更
- dependency/build/package変更
- AIとhuman共通状態遷移変更
- 影響範囲が不明

それ以外はtargeted validationで十分なら探索・検証を止めます。

## Ignore Normally

- `.build-venv/`, `build/`, `build-cpp/`, `dist/`
- generated benchmark/dataset outputs
- 大きな成功ログ
- 無関係なfeedback/history/docs
