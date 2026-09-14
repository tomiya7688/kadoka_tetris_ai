"""Optional Pygame view; the rules engine remains GUI-independent."""

from tetris.core import Board, GameState


class PygameView:
    def __init__(self, cell_size: int = 24):
        self.cell_size = cell_size
        self._pygame = None
        self.screen = None

    def open(self, width: int = 10, height: int = 20) -> None:
        import pygame

        self._pygame = pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (width * self.cell_size, height * self.cell_size)
        )
        pygame.display.set_caption("Kadoka Tetris")

    def draw(self, board: Board) -> None:
        self._prepare_frame()
        self._draw_board_cells(board)
        self._finish_frame()

    def draw_state(self, state: GameState) -> None:
        self._prepare_frame()
        self._draw_board_cells(state.board)
        self._draw_active_piece(state)
        self._finish_frame()

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()

    def _prepare_frame(self) -> None:
        if self.screen is None:
            raise RuntimeError("view is not open")
        self.screen.fill((15, 15, 20))

    def _draw_board_cells(self, board: Board) -> None:
        for x, y in board.cells():
            self._draw_cell(x, y - board.hidden_rows, (80, 190, 220))

    def _draw_active_piece(self, state: GameState) -> None:
        if state.active is None:
            return
        for x, y in state.active.cells():
            draw_x = state.active.x + x
            draw_y = state.active.y + y - state.board.hidden_rows
            self._draw_cell(draw_x, draw_y, (220, 190, 80))

    def _draw_cell(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if y < 0:
            return
        self._pygame.draw.rect(
            self.screen,
            color,
            (
                x * self.cell_size,
                y * self.cell_size,
                self.cell_size - 1,
                self.cell_size - 1,
            ),
        )

    def _finish_frame(self) -> None:
        self._pygame.display.flip()
