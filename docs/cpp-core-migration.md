# C++ Core Migration

## Direction

Kadoka Tetris AI follows the runtime architecture already established by the sibling Othello and Shougi projects.

```text
C++ Core / Runtime
    owns canonical state and rules
           |
           +--> GUI / human adapter
           +--> native AI backend
           +--> Python learning bridge
           +--> headless dataset runtime
```

Python remains important, but its primary responsibility is AI learning and development tooling rather than authoritative gameplay.

## Language Responsibilities

### C++

- board and piece state;
- movement/rotation/lock/line clear;
- bag and deterministic RNG-facing game state;
- combat/garbage rules;
- canonical action validation and state transition;
- headless simulation;
- runtime-facing AI backend boundary;
- high-frequency benchmark paths.

### Python

- training loops;
- dataset generation orchestration;
- experiment configuration;
- model evaluation and analysis;
- weight sweep / visualization;
- data conversion;
- research tools;
- optional UI/tool adapters that call into the C++ runtime.

Python learning code may consume observations and submit action proposals. It must not become a second authoritative implementation after migration.

## Migration Strategy

The existing `src/tetris/core/` implementation is retained temporarily as a behavior reference.

Migration order:

1. `Tetromino` and `Board`;
2. `Bag` and active-piece representation;
3. movement, rotation, lock and line clear;
4. `GameState` and deterministic progression;
5. combat and garbage;
6. headless runtime and AI backend boundary;
7. Python learning bridge;
8. remove Python core from runtime authority.

A migrated feature should have C++ correctness tests before the Python implementation is demoted or removed.

## Authority Rule

AI, GUI and Python tooling only propose semantic actions.

```text
proposal
   |
C++ Runtime validation
   |
C++ Core transition
   |
canonical next state
```

No backend may directly mutate canonical state.

## Performance Rule

The native gameplay/self-play hot path must not require:

- Python callbacks per tick/action;
- process startup per action;
- filesystem serialization;
- GUI rendering;
- global locks shared by simulation workers.

Python training integration should use an efficient bridge selected after measurement. Core must stay independent of that bridge implementation.

## Current Migration State

Implemented in C++:

- base tetromino definitions matching the current Python shapes;
- board dimensions and occupancy;
- placement validation;
- piece lock;
- full-row clear;
- garbage insertion and overflow detection;
- Linux/Windows CMake build and CTest integration.

Still authoritative in the legacy Python runtime until migrated:

- bag;
- active piece;
- full GameState/tick flow;
- rotation/movement behavior;
- combat rules;
- application/runtime integration;
- distribution runtime wiring.

## Validation

C++ core:

```text
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build-cpp --config Release
ctest --test-dir build-cpp -C Release --output-on-failure
```

During migration, relevant existing Python tests remain useful as behavior references. Passing Python tests alone does not prove the new C++ authoritative path.
