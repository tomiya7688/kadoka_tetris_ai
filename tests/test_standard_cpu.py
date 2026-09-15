import unittest

from tetris.application import InputRouter, TickEngine
from tetris.core import GameState, PieceType
from tetris.cpu import (
    STANDARD_CPU_PROFILES,
    StandardCpuProfile,
    StandardCpuStrategy,
    VisibleBoardEvaluator,
    VisibleCpuController,
    VisiblePlacementPlanner,
    VisiblePlannedMove,
)
from tetris.observation import BoardObservation, PlayerObservation


class FixedPlanner:
    def __init__(self, actions):
        self.actions = tuple(actions)
        self.calls = 0

    def choose(self, observation):
        self.calls += 1
        return VisiblePlannedMove(
            rotation=0,
            x=0,
            score=0.0,
            actions=self.actions,
        )


class StandardCpuTests(unittest.TestCase):
    def test_profiles_change_search_strength_and_speed(self):
        easy = STANDARD_CPU_PROFILES["easy"]
        normal = STANDARD_CPU_PROFILES["normal"]
        hard = STANDARD_CPU_PROFILES["hard"]

        self.assertLess(easy.search_depth, normal.search_depth)
        self.assertLess(normal.search_depth, hard.search_depth)
        self.assertGreater(easy.action_interval_ticks, normal.action_interval_ticks)
        self.assertGreater(normal.action_interval_ticks, hard.action_interval_ticks)

    def test_evaluator_penalizes_buried_holes(self):
        evaluator = VisibleBoardEvaluator()
        flat = frozenset({(0, 3), (0, 4), (1, 3), (1, 4)})
        buried_hole = frozenset({(0, 2), (0, 4), (1, 3), (1, 4)})

        self.assertGreater(
            evaluator.score(flat, width=2, height=5),
            evaluator.score(buried_hole, width=2, height=5),
        )

    def test_planner_returns_shared_semantic_action_plan(self):
        observation = PlayerObservation(
            board=BoardObservation(
                width=10,
                height=20,
                locked_cells=frozenset(),
                active_cells=frozenset(),
            ),
            current_piece=PieceType.T,
            hold_piece=None,
            next_pieces=(PieceType.I, PieceType.O),
        )
        move = VisiblePlacementPlanner(search_depth=2).choose(observation)

        self.assertTrue(move.actions)
        self.assertEqual(move.actions[-1], "hard_drop")
        self.assertTrue(
            set(move.actions)
            <= {"move_left", "move_right", "rotate_cw", "rotate_ccw", "hard_drop"}
        )

    def test_strategy_uses_action_interval_without_replanning(self):
        profile = StandardCpuProfile(
            name="test",
            search_depth=1,
            action_interval_ticks=3,
        )
        planner = FixedPlanner(("move_left", "hard_drop"))
        strategy = StandardCpuStrategy(profile, planner=planner)
        observation = PlayerObservation(
            board=BoardObservation(10, 20, frozenset(), frozenset()),
            current_piece=PieceType.O,
            hold_piece=None,
            next_pieces=(),
        )

        self.assertEqual(strategy.choose(observation), "move_left")
        self.assertIsNone(strategy.choose(observation))
        self.assertIsNone(strategy.choose(observation))
        self.assertEqual(strategy.choose(observation), "hard_drop")
        self.assertEqual(planner.calls, 1)

    def test_easy_cpu_can_place_a_piece_through_shared_input_router(self):
        game = GameState(seed=23)
        engine = TickEngine({0: game})
        router = InputRouter(engine)
        strategy = StandardCpuStrategy(STANDARD_CPU_PROFILES["easy"])
        controller = VisibleCpuController(0, strategy)

        for _ in range(80):
            action = controller.choose_action(game)
            if action is not None:
                router.submit(action)
            engine.advance()
            if game.board.cells():
                break

        self.assertTrue(list(game.board.cells()))


if __name__ == "__main__":
    unittest.main()
