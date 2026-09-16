# AI Context

AI-assisted work should start here. Do not preload every document, Issue, benchmark log or generated artifact.

## Project

- Name: Kadoka Tetris AI
- Main language: Python 3.11
- Purpose: deterministic Tetris core, human/AI semantic command runtime, AI experiments, benchmark/observation tooling and portable Windows distribution

## Source of Truth

- Repository working rules: `AGENTS.md`
- Coding rules: `docs/コーディングルール.md`
- Context/validation routing: `docs/context-routing.md`
- Sibling-project policy: `docs/sibling-project-alignment.md`
- Current task/planning: `docs/開発予定.md` and explicit user/GitHub task when relevant
- Source/tests: `src/tetris/`, `tests/`

## Start Here

1. Read the current task and this file.
2. Select a route in `docs/context-routing.md`.
3. Read target source and matching tests.
4. Open detailed design/feedback docs only when needed by that route.
5. Stop broad exploration when Goal / Required / Acceptance and validation are clear.

## Important Invariants

- Core owns canonical Tetris state and rules.
- Human and AI actions use the same semantic command validation/state transition path.
- AI output is a proposal; AI must not mutate canonical state directly.
- Core stays independent from GUI, keyboard, filesystem and wall clock.
- Explicit RNG seeds and integer ticks preserve deterministic reproduction.
- Runtime/gameplay code must not depend on benchmark/training/analysis tooling.
- AI does not receive hidden future pieces or internal RNG state beyond the defined observation.
- Distribution behavior is a separate acceptance boundary from source tests.

## Ignore Normally

- `.build-venv/`, `build/`, `dist/`
- generated datasets and large benchmark logs
- unrelated feedback/history/docs
- successful CI/build logs after the pass/fail result is known

## Validation

Typical broad validation:

```text
python tools/kadoka_rule_checker.py .
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
- Summaries/indexes do not replace source-of-truth code/specs.
- Report relevant unverified areas explicitly.
