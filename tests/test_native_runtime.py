import gc
import os
import unittest
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from itertools import repeat
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

from tetris.learning import NativeRuntime
from tetris.learning._library import load_library


class NativeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ.get("KADOKA_TETRIS_BRIDGE")
        if not path:
            raise unittest.SkipTest("Set KADOKA_TETRIS_BRIDGE to a built bridge library")
        cls.library_path = Path(path).resolve(strict=True)

    def runtime(self, seeds=(123,)):
        return NativeRuntime(self.library_path, seeds)

    def test_public_snapshot_and_copy_isolation(self):
        with self.runtime() as runtime:
            before = runtime.observe()
            self.assertEqual((before.tick, before.pieces_locked), (0, 0))
            self.assertEqual(len(before.locked_cells), 200)
            self.assertEqual(len(before.active_cells), 200)
            self.assertEqual(len(before.next_pieces), 5)
            self.assertEqual(sum(before.locked_cells), 0)
            self.assertIsNone(before.hold_kind)
            self.assertFalse(hasattr(before, "seed"))
            self.assertFalse(hasattr(before, "bag"))
            with self.assertRaises(FrozenInstanceError):
                before.tick = 99
            runtime.submit(0, 0, 0, ["hard_drop"])
            self.assertEqual(runtime.advance(), (0, 1))
            after = runtime.observe()
            self.assertEqual((after.tick, after.pieces_locked), (1, 1))
            self.assertEqual(sum(after.locked_cells), 4)
            self.assertEqual(sum(before.locked_cells), 0)

    def test_fixed_seed_replay_and_independent_handles(self):
        with self.runtime([11, 29]) as first, self.runtime([11, 29]) as second:
            for tick in range(48):
                for player in range(2):
                    self.assertEqual(first.observe(player), second.observe(player))
                    actions = ["hold", "rotate_cw", "move_left", "hard_drop"]
                    first.submit(player, tick, 0, actions)
                    second.submit(player, tick, 0, actions)
                self.assertEqual(first.advance(), second.advance())
            for player in range(2):
                self.assertEqual(first.observe(player), second.observe(player))
        with self.runtime() as first, self.runtime() as second:
            first.submit(0, 0, 0, ["hard_drop"])
            first.advance()
            self.assertEqual(second.observe().pieces_locked, 0)
            self.assertEqual(second.observe().tick, 0)

    def test_player_isolation(self):
        with self.runtime([11, 29]) as runtime:
            runtime.submit(1, 0, 0, ["hard_drop"])
            runtime.advance()
            self.assertEqual(runtime.observe(0).pieces_locked, 0)
            self.assertEqual(runtime.observe(1).pieces_locked, 1)
            with self.assertRaises(IndexError):
                runtime.observe(2)

    def test_batched_observations_and_proposals_match_serial_api(self):
        with self.runtime([11, 29]) as batched, self.runtime([11, 29]) as serial:
            for tick in range(32):
                self.assertEqual(batched.observe_many(), tuple(
                    serial.observe(player) for player in range(2)
                ))
                proposals = [
                    (0, 0, ["hard_drop"]),
                    (1, 3, ["move_left", "rotate_cw"]),
                ]
                batched.submit_many(tick, proposals)
                for player, sequence, actions in proposals:
                    serial.submit(player, tick, sequence, actions)
                self.assertEqual(batched.advance(), serial.advance())
            self.assertEqual(batched.observe_many(), tuple(
                serial.observe(player) for player in range(2)
            ))

    def test_batch_rejection_is_atomic_and_inputs_are_bounded(self):
        with self.runtime([11, 29]) as runtime:
            with self.assertRaises(ValueError):
                runtime.submit_many(0, [
                    (0, 8, ["move_left"]),
                    (1, 9, ["teleport"]),
                ])
            runtime.submit(0, 0, 8, ["move_right"])
            with self.assertRaises(ValueError):
                runtime.submit_many(0, [
                    (1, 0, ["move_left"]),
                    (1, 0, ["hard_drop"]),
                ])
            self.assertEqual(runtime.advance(), (0, 1))
            with self.assertRaises(ValueError):
                runtime.submit_many(1, [(0, 0, repeat("hard_drop"))])
            with self.assertRaises(ValueError):
                runtime.submit_many(1, [(True, 0, [])])

    def test_unknown_action_rejects_entire_proposal(self):
        with self.runtime() as runtime:
            before = runtime.observe()
            with self.assertRaises(ValueError):
                runtime.submit(0, 0, 0, ["move_left", "teleport"])
            self.assertEqual(runtime.advance(), (0, 0))
            after = runtime.observe()
            self.assertEqual(after.active_x, before.active_x)

    def test_native_sequence_conflict_and_overflow_are_atomic(self):
        with self.runtime() as runtime:
            x = runtime.observe().active_x
            runtime.submit(0, 0, 1, ["move_right"])
            with self.assertRaises(ValueError):
                runtime.submit(0, 0, 0, ["move_left", "move_left"])
            with self.assertRaises(ValueError):
                runtime.submit(0, 0, (1 << 64) - 1, ["hold", "hard_drop"])
            self.assertEqual(runtime.advance(), (0, 1))
            self.assertEqual(runtime.observe().active_x, x + 1)

    def test_future_tick_order_and_past_tick_rejection(self):
        with self.runtime() as runtime:
            runtime.submit(0, 1, 0, ["hard_drop"])
            self.assertEqual(runtime.advance(), (0, 0))
            with self.assertRaises(ValueError):
                runtime.submit(0, 0, 0, [])
            self.assertEqual(runtime.advance(), (1, 1))

    def test_numeric_inputs_cannot_wrap_at_ctypes_boundary(self):
        with self.runtime() as runtime:
            for value in [-1, 1 << 64, True, 1.5]:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    runtime.submit(0, value, 0, ["hard_drop"])
                with self.subTest(sequence=value), self.assertRaises(ValueError):
                    runtime.submit(0, 0, value, ["hard_drop"])
            for player in [-1, 1 << 32, True]:
                with self.subTest(player=player), self.assertRaises(ValueError):
                    runtime.observe(player)
            self.assertEqual(runtime.advance(), (0, 0))

    def test_bounded_iterables_and_seed_validation(self):
        for seeds in [[], repeat(1), [-1], [1 << 64], [True]]:
            with self.assertRaises(ValueError):
                self.runtime(seeds)
        with self.runtime() as runtime:
            with self.assertRaises(ValueError):
                runtime.submit(0, 0, 0, repeat("hard_drop"))
            runtime.submit(0, 0, 0, [])
            self.assertEqual(runtime.advance(), (0, 0))

    def test_terminal_state_stays_unchanged(self):
        with self.runtime() as runtime:
            for tick in range(64):
                runtime.submit(0, tick, 0, ["hard_drop"])
                runtime.advance()
                before = runtime.observe()
                if before.game_over:
                    break
            self.assertTrue(before.game_over)
            self.assertIsNone(before.active_kind)
            self.assertEqual(sum(before.active_cells), 0)
            runtime.submit(0, before.tick, 0, ["hold", "hard_drop"])
            runtime.advance()
            after = runtime.observe()
            self.assertEqual(before.locked_cells, after.locked_cells)
            self.assertEqual(before.hold_kind, after.hold_kind)
            self.assertEqual(before.pieces_locked, after.pieces_locked)

    def test_context_exception_and_double_close_destroy_once(self):
        library = load_library(self.library_path)
        destroy = Mock(wraps=library.kt_destroy)
        library.kt_destroy = destroy
        with patch("tetris.learning.native_runtime.load_library", return_value=library):
            with self.assertRaisesRegex(ValueError, "learner failed"):
                with self.runtime() as runtime:
                    raise ValueError("learner failed")
            runtime.close()
            destroy.assert_called_once()
            for operation in [runtime.observe, runtime.advance, runtime.__enter__]:
                with self.assertRaisesRegex(RuntimeError, "closed"):
                    operation()
            with self.assertRaisesRegex(RuntimeError, "closed"):
                runtime.submit(0, 0, 0, [])

    def test_forgotten_close_is_reclaimed(self):
        library = load_library(self.library_path)
        destroy = Mock(wraps=library.kt_destroy)
        library.kt_destroy = destroy
        with patch("tetris.learning.native_runtime.load_library", return_value=library):
            runtime = self.runtime()
            reference = weakref.ref(runtime)
            del runtime
            gc.collect()
            self.assertIsNone(reference())
            destroy.assert_called_once()

    def test_close_waits_for_in_flight_native_call(self):
        library = load_library(self.library_path)
        native_observe = library.kt_observe
        entered, release, closing = Event(), Event(), Event()

        def blocked_observe(*arguments):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("test release timeout")
            return native_observe(*arguments)

        library.kt_observe = blocked_observe
        destroy = Mock(wraps=library.kt_destroy)
        library.kt_destroy = destroy
        with patch("tetris.learning.native_runtime.load_library", return_value=library):
            with self.runtime() as runtime, ThreadPoolExecutor(max_workers=2) as workers:
                def close():
                    closing.set()
                    runtime.close()

                observing = workers.submit(runtime.observe)
                try:
                    self.assertTrue(entered.wait(5))
                    closed = workers.submit(close)
                    self.assertTrue(closing.wait(5))
                    self.assertFalse(closed.done())
                    destroy.assert_not_called()
                finally:
                    release.set()
                self.assertEqual(observing.result(timeout=5).tick, 0)
                closed.result(timeout=5)
            destroy.assert_called_once()

    def test_missing_library_fails_without_legacy_fallback(self):
        with self.assertRaises(FileNotFoundError):
            NativeRuntime(self.library_path.parent / "missing-runtime-library", [123])
