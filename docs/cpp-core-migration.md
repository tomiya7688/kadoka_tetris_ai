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

No backend may directly mutate canonical state. The public C++ `GameState` API therefore exposes the board as a const view; movement, rotation, HOLD, garbage and locking go through GameState methods.

## Performance Rule

The native gameplay/self-play hot path must not require:

- Python callbacks per tick/action;
- process startup per action;
- filesystem serialization;
- GUI rendering;
- global locks shared by simulation workers.

Python training integration should use an efficient bridge selected after measurement. Core must stay independent of that bridge implementation.

## Determinism Rule

The C++ runtime defines its own deterministic RNG behavior instead of inheriting Python `random` behavior. The seven-bag currently uses a fixed SplitMix64-based generator and explicit Fisher-Yates shuffle, so a given C++ seed produces the same bag order across supported platforms.

Migration may therefore intentionally change seeded piece sequences from the legacy Python runtime. Once the C++ GameState is authoritative, the C++ sequence is the source of truth.

## Current Migration State

Implemented in C++:

- base tetromino definitions matching the current Python shapes;
- active-piece state and normalized quarter-turn rotation;
- deterministic seven-bag;
- board dimensions and occupancy;
- placement validation;
- piece lock and full-row clear;
- garbage insertion and overflow detection;
- `GameState` spawn and next queue;
- horizontal/vertical movement;
- rotation with the current legacy kick order `-1, +1, -2, +2`;
- hard drop and lock progression;
- one-HOLD-per-piece behavior and HOLD swap;
- lock counters, line counters and combo state;
- normalized `LockEvent` with B2B/perfect-clear/T-Spin fields;
- current three-corner T-Spin placement rule;
- Linux/Windows CMake build and CTest integration.
- Initial C++ `HeadlessRuntime` with semantic command validation, deterministic tick ordering, per-player GameState ownership, and headless CTest.

Still authoritative in the legacy Python runtime until migrated/integrated:

- complete versus combat coordination/attack dispatch;
- gravity/lock-delay progression and C++ AI backend boundary;
- application/runtime integration;
- observation generation from the C++ state;
- GUI/runtime bridge;
- distribution runtime wiring.

The Python `src/tetris/core/` implementation remains only as a migration reference while these callers are moved to C++.

## Validation

C++ core:

```text
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build-cpp --config Release
ctest --test-dir build-cpp -C Release --output-on-failure
```

CI executes the C++ build and CTest on Linux and Windows before the legacy Python/runtime checks. During migration, relevant existing Python tests remain useful as behavior references. Passing Python tests alone does not prove the new C++ authoritative path.
