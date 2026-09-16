# AI Runtime Backend Boundary

Kadoka Tetris AI uses the same execution-boundary vocabulary as the Othello and Shogi sibling projects while keeping Tetris-specific observations and semantic actions.

## Boundary

```text
GameState
   |
AIBackend.decide()
   |
AIProposal(actions)
   |
run_ai_turn()
   |
Command validation
   |
TickEngine / VersusSession
   |
authoritative GameState transition
```

An AI proposal is not authoritative state. The application validates every semantic action and only the command/tick path may apply it to the game.

## Backend kinds

`AIBackendKind` uses the family-wide names:

- `native`
- `dynamic_library`
- `external_process`
- `script`
- `network`

These names describe execution/transport, not AI strength or architecture.

## Native backend

`NativePlannerBackend` adapts the existing Python `PlacementPlanner` without adding serialization or subprocess overhead to its decision path.

```text
PlacementPlanner.choose()
        |
NativePlannerBackend
        |
AIProposal
        |
run_ai_turn()
```

The same shape can be retained when the built-in runtime is migrated to C++.

## Proposal and authority

`AIProposal` contains semantic actions such as:

```text
rotate_cw
move_left
move_right
hard_drop
hold
```

`run_ai_turn()` validates the complete proposal by constructing `Command` objects before submitting any command. Therefore a proposal such as:

```text
move_left, teleport
```

is rejected atomically: `move_left` is not queued before the invalid second action is discovered.

`Command` itself also validates player/tick/sequence/action on direct construction. This keeps the authoritative boundary valid for human, AI and adapter inputs.

## Public observation

External/script backends receive a serialized public observation rather than the mutable `GameState` object. The observation contains:

- board dimensions and occupied cells
- active piece kind/position/rotation
- hold and hold-used state
- visible next queue
- game-over flag
- lines/combo/B2B/pieces-locked counters

It intentionally does not expose the bag RNG object or hidden future pieces beyond the configured public next queue.

## Persistent process transport

`PersistentProcessAIBackend` keeps one subprocess alive and exchanges one JSON object per line.

Request:

```json
{"type":"decide","request_id":1,"observation":{"board":{},"active":{}}}
```

Response:

```json
{"type":"result","request_id":1,"actions":["move_left","hard_drop"],"diagnostics":{"source":"example"}}
```

The request id must match. Malformed JSON, invalid response shape, process exit and timeout are errors.

### Script backend

A Python script is just the same persistent transport with `kind=script`:

```python
PersistentProcessAIBackend(
    kind=AIBackendKind.SCRIPT,
    name="my-script-ai",
    executable=sys.executable,
    arguments=("my_ai.py",),
)
```

### External executable backend

A standalone executable uses `kind=external_process` and is otherwise identical.

This removes per-decision process startup. One backend instance owns one process; parallel headless workers should own independent backend instances rather than share a global subprocess lock.

## Failure behavior

- Unknown semantic action: rejected before command submission.
- Wrong request id: rejected.
- Malformed JSON/result: rejected.
- Process exit: reported as runtime failure.
- Timeout: reported as `TimeoutError`.
- Game already over: `run_ai_turn()` does not call the backend.

## Performance rule

Do not force serialization/process overhead onto native built-in AI. Native and future C++ in-process paths stay direct. Persistent external/script transport exists for language independence and distribution flexibility.

## Sibling mapping

```text
Othello: IAIEngine -> Game::play
Shogi:   AIBackend -> TurnRunner -> Position::after_move
Tetris:  AIBackend -> run_ai_turn -> Command/TickEngine
```

The games share authority semantics and backend vocabulary, not state or move binary formats.
