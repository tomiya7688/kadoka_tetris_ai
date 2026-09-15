"""Optional Pygame view; the rules engine remains GUI-independent."""

from tetris.core import Board, GameState


class PygameView:
    def __init__(self, cell_size: int = 24, side_panel_cells: int = 6):
        self.cell_size = cell_size
        self.side_panel_width = side_panel_cells * cell_size
        self._pygame = None
        self._font = None
        self.screen = None
        self._board_width = 0
        self._visible_height = 0

    def open(self, width: int = 10, height: int = 20) -> None:
        import pygame

        self._pygame = pygame
        self._board_width = width
        self._visible_height = height
        pygame.init()
        self._font = pygame.font.Font(None, max(18, self.cell_size))
        self.screen = pygame.display.set_mode(
            (
                width * self.cell_size + self.side_panel_width * 2,
                height * self.cell_size,
            )
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
        self._draw_visible_metadata(state)
        self._finish_frame()

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()

    def _prepare_frame(self) -> None:
        if self.screen is None:
            raise RuntimeError("view is not open")
        self.screen.fill((15, 15, 20))
        self._pygame.draw.rect(
            self.screen,
            (35, 35, 45),
            (
                self.side_panel_width,
                0,
                self._board_width * self.cell_size,
                self._visible_height * self.cell_size,
            ),
        )

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

    def _draw_visible_metadata(self, state: GameState) -> None:
        active_name = state.active.kind.value if state.active is not None else "-"
        hold_name = state.hold.value if state.hold is not None else "-"

        self._draw_text("ACTIVE", 12, 16)
        self._draw_text(active_name, 12, 44)
        self._draw_text("HOLD", 12, 88)
        self._draw_text(hold_name, 12, 116)

        right_x = self.side_panel_width + self._board_width * self.cell_size + 12
        self._draw_text("NEXT", right_x, 16)
        for index, piece in enumerate(state.next_pieces):
            self._draw_text(piece.value, right_x, 46 + index * 30)

    def _draw_text(self, text: str, x: int, y: int) -> None:
        if self._font is None:
            raise RuntimeError("view is not open")
        surface = self._font.render(text, True, (225, 225, 235))
        self.screen.blit(surface, (x, y))

    def _draw_cell(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if y < 0:
            return
        self._pygame.draw.rect(
            self.screen,
            color,
            (
                self.side_panel_width + x * self.cell_size,
                y * self.cell_size,
                self.cell_size - 1,
                self.cell_size - 1,
            ),
        )

    def _finish_frame(self) -> None:
        self._pygame.display.flip()
