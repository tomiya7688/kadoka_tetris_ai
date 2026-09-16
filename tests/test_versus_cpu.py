import unittest

from tetris.application import VersusSession
from tetris.core import GameState, PieceType
from tetris.cpu import (
    VersusStandardCpuStrategy,
    VisibleVersusCpuController,
    standard_cpu_profile,
)
from tetris.observation import (
    BoardObservation,
    PlayerObservation,
    VersusPlayerObservation,
)


def _player_observation(
    locked_cells=frozenset(),
    current_piece=PieceType.T,
) -> PlayerObservation:
    return PlayerObservation(
        board=BoardObservation(
            width=10,
            height=20,
            locked_cells=frozenset(locked_cells),
            active_cells=frozenset(),
        ),
        current_piece=current_piece,
        hold_piece=None,
        next_pieces=(PieceType.I, PieceType.O, PieceType.S),
    )


def _versus_observation(
    own=None,
    opponent=None,
    incoming=0,
    opponent_incoming=0,
) -> VersusPlayerObservation:
    return VersusPlayerObservation(
        own=own or _player_observation(),
        opponent=opponent or _player_observation(),
        incoming_garbage=incoming,
        opponent_incoming_garbage=opponent_incoming,
    )


class VersusStandardCpuTests(unittest.TestCase):
    def test_neutral_mode_on_safe_boards(self):
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("hard"))

        action = strategy.choose(_versus_observation())

        self.assertIsNotNone(action)
        self.assertEqual(strategy.last_mode, "neutral")

    def test_incoming_garbage_selects_defense(self):
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("hard"))

        action = strategy.choose(_versus_observation(incoming=3))

        self.assertIsNotNone(action)
        self.assertEqual(strategy.last_mode, "defense")

    def test_high_opponent_selects_pressure(self):
        opponent = _player_observation(locked_cells={(0, 6)})
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("hard"))

        action = strategy.choose(_versus_observation(opponent=opponent))

        self.assertIsNotNone(action)
        self.assertEqual(strategy.last_mode, "pressure")

    def test_defense_has_priority_over_pressure(self):
        opponent = _player_observation(locked_cells={(0, 6)})
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("hard"))

        strategy.choose(
            _versus_observation(
                opponent=opponent,
                incoming=4,
                opponent_incoming=5,
            )
        )

        self.assertEqual(strategy.last_mode, "defense")

    def test_mode_weights_change_only_expected_direction(self):
        strategy = VersusStandardCpuStrategy(standard_cpu_profile("normal"))
        neutral = strategy._weights_for_mode("neutral")
        defense = strategy._weights_for_mode("defense")
        pressure = strategy._weights_for_mode("pressure")

        self.assertLess(defense.holes, neutral.holes)
        self.assertLess(defense.max_height, neutral.max_height)
        self.assertGreater(pressure.cleared_lines, neutral.cleared_lines)
        self.assertGreater(pressure.max_height, neutral.max_height)
        self.assertEqual(pressure.holes, neutral.holes)

    def test_controller_builds_visible_versus_observation(self):
        class RecordingStrategy:
            def __init__(self):
                self.observation = None

            def choose(self, observation):
                self.observation = observation
                return "hard_drop"

        session = VersusSession({0: GameState(1), 1: GameState(2)}, garbage_seed=3)
        session.queue_attack(0, 2)
        strategy = RecordingStrategy()
        controller = VisibleVersusCpuController(1, strategy)

        action = controller.choose_action(session)

        self.assertEqual(action.player, 1)
        self.assertEqual(action.action, "hard_drop")
        self.assertIsInstance(strategy.observation, VersusPlayerObservation)
        self.assertEqual(strategy.observation.incoming_garbage, 2)
        self.assertFalse(hasattr(strategy.observation, "games"))
        self.assertFalse(hasattr(strategy.observation, "results"))
        self.assertFalse(hasattr(strategy.observation.own, "last_lock_event"))


if __name__ == "__main__":
    unittest.main()
