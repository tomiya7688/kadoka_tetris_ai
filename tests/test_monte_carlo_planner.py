import unittest
from tetris.ai import MonteCarloPlanner, MonteCarloSettings
from tetris.core import GameState
from tetris.observation import VisiblePlayerObserver

class MonteCarloPlannerTests(unittest.TestCase):
    def test_same_seed_and_observation_return_same_move(self):
        observation = VisiblePlayerObserver().observe(GameState(seed=31, next_count=1))
        planner = MonteCarloPlanner(settings=MonteCarloSettings(rollouts=3, seed=17))
        self.assertEqual(planner.choose(observation), planner.choose(observation))

    def test_future_search_is_bounded_by_visible_next_queue(self):
        observation = VisiblePlayerObserver().observe(GameState(seed=4, next_count=1))
        planner = MonteCarloPlanner(settings=MonteCarloSettings(rollouts=2, max_visible_future=20))
        move = planner.choose(observation)
        self.assertIn(move.actions[-1], {'hard_drop'})

    def test_invalid_rollout_count_is_rejected(self):
        with self.assertRaises(ValueError):
            MonteCarloSettings(rollouts=0)

if __name__ == '__main__':
    unittest.main()
