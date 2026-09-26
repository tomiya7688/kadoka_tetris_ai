# AI Context

AI-assisted work should start here. Do not preload every document, Issue, benchmark log or generated artifact.

## Project

- Name: Kadoka Tetris AI
- Runtime language: C++20
- Learning/tooling language: Python 3.11
- Purpose: deterministic C++ Tetris core/runtime, human/AI semantic command execution, Python AI learning and experiment tooling, benchmark/observation tooling and portable Windows distribution

## Language Boundary

The sibling projects Othello and Shougi lead the runtime architecture.

- C++ owns authoritative game rules/state, high-frequency simulation, headless runtime and runtime-facing AI execution.
- Python is for AI learning, dataset generation, experiments, evaluation, conversion and research tooling.
- Python must not become the authoritative game-state owner after migration.
- GUI/adapters submit semantic actions/proposals to the C++ runtime.
- Do not route the native C++ hot path through Python or a process boundary.

The legacy Python core under `src/tetris/core/` is a migration reference until equivalent C++ functionality is complete. New authoritative core work belongs under top-level `core/`.

## Source of Truth

- Repository working rules: `AGENTS.md`
- Coding rules: `docs/コーディングルール.md`
- C++ migration policy: `docs/cpp-core-migration.md`
- Context/validation routing: `docs/context-routing.md`
- Sibling-project policy: `docs/sibling-project-alignment.md`
- Current task/planning: `docs/開発予定.md` and explicit user/GitHub task when relevant
- C++ Core: `core/`
- C++ Headless Runtime: `runtime/`
- C++ visible Observation: `runtime/include/kadoka/tetris/runtime/observation.hpp`
- Python learning/tooling/runtime adapters during migration: `src/tetris/`
- Tests: `tests_cpp/`, `tests/`

## Start Here

1. Read the current task and this file.
2. Select a route in `docs/context-routing.md`.
3. Read target source and matching tests.
4. Open detailed design/feedback docs only when needed by that route.
5. Stop broad exploration when Goal / Required / Acceptance and validation are clear.

## Important Invariants

- C++ Core owns canonical Tetris state and rules.
- Human and AI actions use the same semantic command validation/state transition path.
- AI output is a proposal; AI must not mutate canonical state directly.
- Core stays independent from GUI, Python, keyboard, filesystem and wall clock.
- Explicit RNG seeds and integer ticks preserve deterministic reproduction.
- Runtime/gameplay code must not depend on benchmark/training/analysis tooling.
- AI does not receive hidden future pieces or internal RNG state beyond the defined observation.
- Python learning/tooling may depend on Runtime interfaces; C++ Core must not depend on Python learning code.
- Distribution behavior is a separate acceptance boundary from source tests.

## Ignore Normally

- `.build-venv/`, `build/`, `build-cpp/`, `dist/`
- generated datasets and large benchmark logs
- unrelated feedback/history/docs
- successful CI/build logs after the pass/fail result is known

## Validation

Typical broad validation:

```text
python tools/kadoka_rule_checker.py .
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build-cpp --config Release
ctest --test-dir build-cpp -C Release --output-on-failure
python -m compileall -q src tests tools
python -m ruff check src tests tools
python -m unittest discover -s tests -v
build.bat
```

Use targeted tests first for local logic changes. Run distribution build/smoke when packaging, dependencies, paths, settings or startup behavior are affected.

## Working Rules

- Search first, read second.
- Do not mix unrelated refactors into a task.
- Prefer fixed seeds/inputs for AI comparisons.
- During C++ migration, compare behavior against the existing Python implementation where practical.
- Summaries/indexes do not replace source-of-truth code/specs.
- Report relevant unverified areas explicitly.
