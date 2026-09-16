import unittest

from tetris.core import ActivePiece, GameState, PieceType
from tetris.cpu import VisiblePlacementPlanner
from tetris.observation import VisiblePlayerObserver


class ReachablePlacementSearchTests(unittest.TestCase):
    def test_piece_geometry_matches_rules_engine_active_piece(self):
        planner = VisiblePlacementPlanner(search_depth=1)

        for piece in PieceType:
            for rotation in range(4):
                self.assertEqual(
                    planner._piece_cells(piece, rotation),
                    tuple(ActivePiece(piece, 0, 0, rotation).cells()),
                )

    def test_o_piece_can_reach_both_visible_walls(self):
        planner = VisiblePlacementPlanner(search_depth=1)

        placements = planner._reachable_placements(
            frozenset(),
            PieceType.O,
            width=10,
            height=20,
        )

        xs = {placement.x for placement in placements if placement.rotation == 0}
        self.assertIn(-1, xs)
        self.assertIn(7, xs)

    def test_invalid_positive_visible_spawn_offset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "spawn_y"):
            VisiblePlacementPlanner(search_depth=1, spawn_y=1)

    def test_planned_actions_replay_successfully_on_real_game_state(self):
        observer = VisiblePlayerObserver()
        planner = VisiblePlacementPlanner(search_depth=1)

        for seed in (3, 19):
            game = GameState(seed=seed)
            for _ in range(15):
                if game.game_over:
                    break
                before = game.pieces_locked
                move = planner.choose(observer.observe(game))

                for action in move.actions:
                    if action == "move_left":
                        self.assertTrue(game.move(-1), (seed, move, action))
                    elif action == "move_right":
                        self.assertTrue(game.move(1), (seed, move, action))
                    elif action == "rotate_cw":
                        self.assertTrue(game.rotate(1), (seed, move, action))
                    elif action == "rotate_ccw":
                        self.assertTrue(game.rotate(-1), (seed, move, action))
                    elif action == "soft_drop":
                        self.assertTrue(game.move(0, 1), (seed, move, action))
                    elif action == "hold":
                        self.assertTrue(game.hold_piece(), (seed, move, action))
                    elif action == "hard_drop":
                        game.hard_drop()
                    else:
                        self.fail(f"unexpected semantic action: {action}")

                self.assertEqual(game.pieces_locked, before + 1)

    def test_reachable_search_can_move_after_descending(self):
        planner = VisiblePlacementPlanner(search_depth=1, spawn_y=0)
        # A roof over columns 0-1 forces an O piece to descend on the right before
        # sliding left into the lower cavity. A pure final-column hard drop cannot
        # reach this placement.
        locked = frozenset({(0, 2), (1, 2), (2, 4), (3, 4)})

        placements = planner._reachable_placements(
            locked,
            PieceType.O,
            width=4,
            height=6,
        )

        tucked = [
            placement
            for placement in placements
            if "soft_drop" in placement.actions
            and any(
                action in {"move_left", "move_right"}
                for action in placement.actions[
                    placement.actions.index("soft_drop") + 1 :
                ]
            )
        ]
        self.assertTrue(tucked)


if __name__ == "__main__":
    unittest.main()
