# Context Routing

変更内容から、最初に読む source / tests / docs / validation を絞るための地図です。全資料を先に読まず、共有契約へ影響するときだけ範囲を広げます。

## core

盤面、ツモ、移動、回転、ロック、消去、ゲームオーバー等。

- Source: `src/tetris/core/`
- Tests: `tests/test_core.py`, `tests/test_game_state.py` と対象機能の近接テスト
- Docs: `docs/コーディングルール.md`、必要時のみ詳細設計
- Validation: 対象 unittest -> core 関連テスト -> shared API変更時のみ全体

## commands-runtime

人間/AI共通の意味的コマンド、対戦進行、アプリケーション調停。

- Source: `src/tetris/application/`, `src/tetris/adapters/`
- Tests: `tests/test_commands.py`, `tests/test_adapters.py`, 対戦関連テスト
- Invariant: 人間とAIは同じ権威ある状態遷移を通る
- Validation: deterministic input/seedを優先

## ai-cpu

AI判断、CPU評価、候補生成、対戦AI。

- Source: `src/tetris/ai/`, `src/tetris/cpu/`
- Tests: `tests/test_ai.py`, `tests/test_ai_match.py`, `tests/test_cpu_benchmark*.py`, `tests/test_cpu_weight_sweep.py`
- Docs: `docs/CPUベンチマーク.md`, `docs/標準CPU評価重み.md` は必要時のみ
- Validation: 同一seed・同一条件で比較。AIへ未公開情報を渡さない

## combat

攻撃、garbage、combo、B2B、T-Spin等。

- Source: core/application内のcombat関連実装
- Tests: `tests/test_attack.py`, `tests/test_combat_events.py`, `tests/test_garbage.py`
- Validation: 小さい決定的局面を優先

## observation

AIへ渡す観測、可視化用観測。

- Source: `src/tetris/observation/`
- Tests: observation/AI関連テスト
- Docs: `docs/対戦UIと可視Observation.md`
- Invariant: hidden future pieces / internal RNG stateを漏らさない

## benchmark

CPU評価、weight sweep、計測。

- Source: `src/tetris/benchmark/`, 関連CPU実装
- Tests: benchmark関連テスト
- Validation: fixed seeds / fixed config / bounded games。同一条件以外の数値を直接比較しない

## distribution

PyInstaller、runtime path、設定/UserData、配布物。

- Source: `build.bat`, `tools/distribution/`, `src/tetris/runtime_paths.py`, `requirements-build.txt`
- Tests: source tests + `tools/distribution/smoke_test.py`
- CI: `.github/workflows/windows-build.yml`
- Validation: source test成功だけで配布成功とみなさず、生成artifactを直接smokeする

## build-policy

CI、ruff、checker、依存境界、開発ルール。

- Source: `.github/workflows/`, `pyproject.toml`, `tools/kadoka_rule_checker.py`, `AGENTS.md`
- Docs: `docs/コーディングルール.md`, `docs/sibling-project-alignment.md`
- Validation: checker -> compileall -> ruff -> unittest

## Broadening Rules

次の場合は全体検証へ広げます。

- core/public command contract変更
- observation contract変更
- dependency/build/package変更
- AIとhuman共通状態遷移変更
- 影響範囲が不明

それ以外はtargeted validationで十分なら探索・検証を止めます。

## Ignore Normally

- `.build-venv/`, `build/`, `dist/`
- generated benchmark/dataset outputs
- 大きな成功ログ
- 無関係なfeedback/history/docs
