"""Build player-visible board observations from the game engine."""

from tetris.core import GameState

from .board_observation import BoardObservation, Cell


class VisibleBoardObserver:
    """Expose only cells that are currently inside the visible field."""

    def observe(self, state: GameState) -> BoardObservation:
        board = state.board
        visible_height = board.height - board.hidden_rows
        locked_cells = self._locked_cells(state)
        active_cells = self._active_cells(state)
        return BoardObservation(
            width=board.width,
            height=visible_height,
            locked_cells=locked_cells,
            active_cells=active_cells,
        )

    def _locked_cells(self, state: GameState) -> frozenset[Cell]:
        hidden_rows = state.board.hidden_rows
        return frozenset(
            (x, y - hidden_rows)
            for x, y in state.board.cells()
            if y >= hidden_rows
        )

    def _active_cells(self, state: GameState) -> frozenset[Cell]:
        active = state.active
        if active is None:
            return frozenset()

        hidden_rows = state.board.hidden_rows
        visible_height = state.board.height - hidden_rows
        cells = []
        for local_x, local_y in active.cells():
            x = active.x + local_x
            y = active.y + local_y - hidden_rows
            if 0 <= x < state.board.width and 0 <= y < visible_height:
                cells.append((x, y))
        return frozenset(cells)
