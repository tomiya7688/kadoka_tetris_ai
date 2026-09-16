import sys
import unittest
from pathlib import Path

from tetris.application import (
    AIBackendKind,
    AIProposal,
    Command,
    FunctionAIBackend,
    PersistentProcessAIBackend,
    VersusSession,
    run_ai_turn,
)
from tetris.core import GameState


HELPER = Path(__file__).parent / "helpers" / "persistent_ai.py"


class AIBackendRuntimeTests(unittest.TestCase):
    def make_session(self):
        return VersusSession({0: GameState(1), 1: GameState(2)})

    def make_process_backend(self, mode="normal", *, kind=AIBackendKind.SCRIPT, timeout=0.5):
        return PersistentProcessAIBackend(
            kind=kind,
            name=f"test-{mode}",
            executable=sys.executable,
            arguments=(str(HELPER), "--mode", mode),
            timeout_seconds=timeout,
        )

    def test_command_validates_direct_construction(self):
        with self.assertRaises(ValueError):
            Command(player=0, tick=0, sequence=0, action="teleport")

    def test_runner_schedules_without_direct_state_mutation(self):
        session = self.make_session()
        backend = FunctionAIBackend(
            AIBackendKind.NATIVE,
            "left",
            lambda game: AIProposal(("move_left",)),
        )
        start_x = session.games[0].active.x
        result = run_ai_turn(session, backend, player=0, sequence_start=0)

        self.assertEqual(result.next_sequence, 1)
        self.assertEqual(session.games[0].active.x, start_x)
        session.advance()
        self.assertEqual(session.games[0].active.x, start_x - 1)

    def test_invalid_proposal_is_atomic(self):
        session = self.make_session()
        backend = FunctionAIBackend(
            AIBackendKind.NATIVE,
            "bad",
            lambda game: AIProposal(("move_left", "teleport")),
        )
        with self.assertRaises(ValueError):
            run_ai_turn(session, backend, player=0, sequence_start=0)
        self.assertEqual(dict(session.engine.pending), {})

    def test_game_over_skips_backend(self):
        session = self.make_session()
        session.games[0].game_over = True
        calls = 0

        def decide(game):
            nonlocal calls
            calls += 1
            return AIProposal(("hard_drop",))

        backend = FunctionAIBackend(AIBackendKind.NETWORK, "unused", decide)
        result = run_ai_turn(session, backend, player=0, sequence_start=3)
        self.assertTrue(result.skipped)
        self.assertEqual(result.next_sequence, 3)
        self.assertEqual(calls, 0)

    def test_script_backend_reuses_process(self):
        game = GameState(5)
        with self.make_process_backend() as backend:
            first = backend.decide(game)
            second = backend.decide(game)
            self.assertEqual(backend.kind, AIBackendKind.SCRIPT)
            self.assertEqual(first.diagnostics["request_count"], "1")
            self.assertEqual(second.diagnostics["request_count"], "2")
            self.assertIn(first.diagnostics["active"], "IOTSZJL")

    def test_external_process_uses_same_runner(self):
        session = self.make_session()
        with self.make_process_backend(
            "hard_drop",
            kind=AIBackendKind.EXTERNAL_PROCESS,
        ) as backend:
            result = run_ai_turn(session, backend, player=0, sequence_start=0)
            self.assertEqual(result.commands[0].action, "hard_drop")
            locked_before = session.games[0].pieces_locked
            session.advance()
            self.assertEqual(session.games[0].pieces_locked, locked_before + 1)

    def test_external_invalid_action_never_reaches_tick_engine(self):
        session = self.make_session()
        with self.make_process_backend("illegal_action") as backend:
            with self.assertRaises(ValueError):
                run_ai_turn(session, backend, player=0, sequence_start=0)
        self.assertEqual(dict(session.engine.pending), {})

    def test_malformed_response_is_rejected(self):
        with self.make_process_backend("malformed") as backend:
            with self.assertRaises(RuntimeError):
                backend.decide(GameState(1))

    def test_process_exit_is_rejected(self):
        with self.make_process_backend("exit") as backend:
            with self.assertRaises(RuntimeError):
                backend.decide(GameState(1))

    def test_timeout_is_rejected(self):
        with self.make_process_backend("timeout", timeout=0.05) as backend:
            with self.assertRaises(TimeoutError):
                backend.decide(GameState(1))


if __name__ == "__main__":
    unittest.main()
