import unittest

from tetris.application import attack_for_event
from tetris.core import (
    ActivePiece,
    GameState,
    PieceType,
    Tetromino,
    is_t_spin_placement,
)
from tetris.cpu import (
    StandardCpuStrategy,
    VersusStandardCpuStrategy,
    VisibleAttackPlacementPlanner,
    VisibleBoardEvaluator,
    VisibleBoardWeights,
    VisiblePerfectClearReadinessEvaluator,
    VisiblePerfectClearReadyPlanner,
    VisibleTSpinReadinessEvaluator,
    VisibleTSpinReadyPlanner,
    standard_cpu_profile,
)
from tetris.observation import BoardObservation, PlayerObservation


def _zero_board_evaluator() -> VisibleBoardEvaluator:
    return VisibleBoardEvaluator(
        VisibleBoardWeights(
            cleared_lines=0.0,
            aggregate_height=0.0,
            max_height=0.0,
            holes=0.0,
            covered_hole_cells=0.0,
            bumpiness=0.0,
        )
    )


def _lock_single_cell(game: GameState, x: int, y: int) -> None:
    game.board.lock(Tetromino(PieceType.O, ((0, 0),)), (x, y))


class VisibleAttackPlannerTests(unittest.TestCase):
    def test_visible_top_is_not_assumed_to_be_an_occupied_hidden_row(self):
        occupied = {(0, 1), (2, 1)}

        runtime_like = is_t_spin_placement(
            PieceType.T,
            0,
            0,
            -1,
            width=4,
            height=4,
            occupied=lambda x, y: (x, y) in occupied,
            last_rotation=True,
        )
        visible_only = is_t_spin_placement(
            PieceType.T,
            0,
            0,
            -1,
            width=4,
            height=4,
            occupied=lambda x, y: (x, y) in occupied,
            last_rotation=True,
            top_out_of_bounds_occupied=False,
        )

        self.assertTrue(runtime_like)
        self.assertFalse(visible_only)

    def test_attack_weight_must_be_finite_and_nonnegative(self):
        for value in (-1.0, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "attack_weight"):
                    VisibleAttackPlacementPlanner(attack_weight=value)

    def test_attack_planner_prefers_reachable_t_spin_single(self):
        locked = frozenset({(0, 0), (2, 0), (0, 2), (3, 1)})
        observation = PlayerObservation(
            board=BoardObservation(
                width=4,
                height=4,
                locked_cells=locked,
                active_cells=frozenset(),
            ),
            current_piece=PieceType.T,
            hold_piece=None,
            next_pieces=(),
        )
        planner = VisibleAttackPlacementPlanner(
            evaluator=_zero_board_evaluator(),
            search_depth=1,
            spawn_y=0,
            attack_weight=10.0,
        )

        move = planner.choose(observation)

        self.assertIn("hard_drop", move.actions)
        self.assertTrue(
            any(action in {"rotate_cw", "rotate_ccw"} for action in move.actions)
        )

        game = GameState(
            seed=1,
            width=4,
            visible_height=4,
            hidden_rows=0,
            next_count=0,
        )
        for x, y in locked:
            _lock_single_cell(game, x, y)
        game.active = ActivePiece(PieceType.T, x=0, y=0, rotation=0)
        game.game_over = False

        for action in move.actions:
            if action == "move_left":
                self.assertTrue(game.move(-1))
            elif action == "move_right":
                self.assertTrue(game.move(1))
            elif action == "rotate_cw":
                self.assertTrue(game.rotate(1))
            elif action == "rotate_ccw":
                self.assertTrue(game.rotate(-1))
            elif action == "soft_drop":
                self.assertTrue(game.move(0, 1))
            elif action == "hard_drop":
                game.hard_drop()
            else:
                self.fail(f"unexpected action: {action}")

        event = game.last_lock_event
        self.assertIsNotNone(event)
        self.assertTrue(event.t_spin)
        self.assertEqual(event.lines, 1)
        self.assertEqual(attack_for_event(event), 2)

    def test_future_visible_t_piece_scores_reachable_t_spin(self):
        locked = frozenset({(0, 0), (2, 0), (0, 2), (3, 1)})
        planner = VisibleAttackPlacementPlanner(
            evaluator=_zero_board_evaluator(),
            search_depth=2,
            spawn_y=0,
            attack_weight=10.0,
        )

        score = planner._best_attack_future_score(
            locked,
            (PieceType.T,),
            depth=1,
            width=4,
            height=4,
            memo={},
        )

        self.assertEqual(score, 20.0)

    def test_readiness_detects_visible_t_spin_single_slot(self):
        locked = frozenset({(0, 0), (2, 0), (0, 2), (3, 1)})
        readiness = VisibleTSpinReadinessEvaluator()

        self.assertEqual(readiness.best_attack(locked, width=4, height=4), 2)
        self.assertEqual(readiness.best_attack(frozenset(), width=4, height=4), 0)

    def test_readiness_weight_must_be_finite_and_nonnegative(self):
        for value in (-1.0, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "readiness_weight"):
                    VisibleTSpinReadyPlanner(readiness_weight=value)

    def test_readiness_is_added_to_visible_board_score(self):
        locked = frozenset({(0, 0), (2, 0), (0, 2), (3, 1)})
        planner = VisibleTSpinReadyPlanner(
            evaluator=_zero_board_evaluator(),
            readiness_weight=0.75,
            attack_weight=0.0,
            spawn_y=0,
        )

        self.assertEqual(planner.evaluator.score(locked, 4, 4), 1.5)

    def test_perfect_clear_readiness_detects_bounded_geometric_completions(self):
        one_piece = frozenset(
            (x, y)
            for y in (18, 19)
            for x in range(10)
            if x not in (4, 5)
        )
        two_pieces = frozenset(
            (x, y)
            for y in (18, 19)
            for x in range(10)
            if x not in (2, 3, 6, 7)
        )
        impossible_one_piece = frozenset(
            (x, y)
            for y in (18, 19)
            for x in range(10)
            if (x, y) not in {(0, 18), (2, 18), (4, 19), (6, 19)}
        )
        readiness = VisiblePerfectClearReadinessEvaluator()

        self.assertEqual(readiness.score(one_piece, width=10, height=20), 3)
        self.assertEqual(readiness.score(two_pieces, width=10, height=20), 2)
        self.assertEqual(
            readiness.score(impossible_one_piece, width=10, height=20),
            0,
        )
        self.assertEqual(readiness.score(frozenset(), width=10, height=20), 0)

    def test_perfect_clear_readiness_weight_must_be_finite_and_nonnegative(self):
        for value in (-1.0, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "perfect_clear_readiness_weight",
                ):
                    VisiblePerfectClearReadyPlanner(
                        perfect_clear_readiness_weight=value
                    )

    def test_perfect_clear_readiness_is_added_to_board_score(self):
        locked = frozenset(
            (x, y)
            for y in (18, 19)
            for x in range(10)
            if x not in (4, 5)
        )
        planner = VisiblePerfectClearReadyPlanner(
            evaluator=_zero_board_evaluator(),
            readiness_weight=0.0,
            perfect_clear_readiness_weight=0.5,
            attack_weight=0.0,
        )

        self.assertEqual(planner.evaluator.score(locked, 10, 20), 1.5)

    def test_standard_cpu_uses_perfect_clear_ready_planner_by_default(self):
        strategy = StandardCpuStrategy(standard_cpu_profile("easy"))
        self.assertIsInstance(strategy.planner, VisiblePerfectClearReadyPlanner)
        self.assertIsInstance(strategy.planner, VisibleTSpinReadyPlanner)
        self.assertIsInstance(strategy.planner, VisibleAttackPlacementPlanner)
        self.assertEqual(strategy.planner.attack_weight, 2.0)
        self.assertEqual(strategy.planner.readiness_weight, 0.75)
        self.assertEqual(strategy.planner.perfect_clear_readiness_weight, 0.5)

    def test_versus_modes_change_attack_priority(self):
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("normal"))

        defense = strategy._attack_weight_for_mode("defense")
        neutral = strategy._attack_weight_for_mode("neutral")
        pressure = strategy._attack_weight_for_mode("pressure")

        self.assertLess(defense, neutral)
        self.assertLess(neutral, pressure)
        self.assertEqual((defense, neutral, pressure), (1.0, 2.0, 4.0))

    def test_versus_modes_change_t_spin_readiness_priority(self):
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("normal"))

        defense = strategy._t_spin_readiness_weight_for_mode("defense")
        neutral = strategy._t_spin_readiness_weight_for_mode("neutral")
        pressure = strategy._t_spin_readiness_weight_for_mode("pressure")

        self.assertEqual((defense, neutral, pressure), (0.25, 0.75, 1.25))


    def test_versus_modes_change_perfect_clear_readiness_priority(self):
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("normal"))

        defense = strategy._perfect_clear_readiness_weight_for_mode("defense")
        neutral = strategy._perfect_clear_readiness_weight_for_mode("neutral")
        pressure = strategy._perfect_clear_readiness_weight_for_mode("pressure")

        self.assertEqual((defense, neutral, pressure), (0.0, 0.5, 1.0))


if __name__ == "__main__":
    unittest.main()
