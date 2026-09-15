"""Two-player Pygame view exposing the same state allowed to versus observers."""

from tetris.core import GameState


class PygameVersusView:
    def __init__(
        self,
        cell_size: int = 20,
        side_panel_cells: int = 5,
        gap_cells: int = 2,
    ):
        self.cell_size = cell_size
        self.side_panel_width = side_panel_cells * cell_size
        self.gap_width = gap_cells * cell_size
        self._pygame = None
        self._font = None
        self.screen = None
        self._board_width = 0
        self._visible_height = 0
        self._player_width = 0

    def open(self, width: int = 10, height: int = 20) -> None:
        import pygame

        self._pygame = pygame
        self._board_width = width
        self._visible_height = height
        self._player_width = width * self.cell_size + self.side_panel_width * 2
        pygame.init()
        self._font = pygame.font.Font(None, max(17, self.cell_size))
        self.screen = pygame.display.set_mode(
            (
                self._player_width * 2 + self.gap_width,
                height * self.cell_size,
            )
        )
        pygame.display.set_caption("Kadoka Tetris - Versus")

    def draw_states(
        self,
        states: dict[int, GameState],
        incoming_garbage: dict[int, int],
    ) -> None:
        if len(states) != 2:
            raise ValueError("versus view requires exactly two states")
        if set(states) != set(incoming_garbage):
            raise ValueError("garbage meters must match displayed players")
        if self.screen is None:
            raise RuntimeError("view is not open")

        self.screen.fill((15, 15, 20))
        for index, player in enumerate(sorted(states)):
            origin_x = index * (self._player_width + self.gap_width)
            self._draw_player(
                player,
                states[player],
                incoming_garbage[player],
                origin_x,
            )
        self._pygame.display.flip()

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()

    def _draw_player(
        self,
        player: int,
        state: GameState,
        incoming_garbage: int,
        origin_x: int,
    ) -> None:
        board_x = origin_x + self.side_panel_width
        self._pygame.draw.rect(
            self.screen,
            (35, 35, 45),
            (
                board_x,
                0,
                self._board_width * self.cell_size,
                self._visible_height * self.cell_size,
            ),
        )
        self._draw_text(f"P{player + 1}", origin_x + 10, 8)

        for x, y in state.board.cells():
            self._draw_cell(
                board_x,
                x,
                y - state.board.hidden_rows,
                (80, 190, 220),
            )
        if state.active is not None:
            for local_x, local_y in state.active.cells():
                self._draw_cell(
                    board_x,
                    state.active.x + local_x,
                    state.active.y + local_y - state.board.hidden_rows,
                    (220, 190, 80),
                )

        active_name = state.active.kind.value if state.active is not None else "-"
        hold_name = state.hold.value if state.hold is not None else "-"
        self._draw_text("ACTIVE", origin_x + 10, 42)
        self._draw_text(active_name, origin_x + 10, 66)
        self._draw_text("HOLD", origin_x + 10, 100)
        self._draw_text(hold_name, origin_x + 10, 124)

        right_x = board_x + self._board_width * self.cell_size + 10
        self._draw_text("NEXT", right_x, 8)
        for index, piece in enumerate(state.next_pieces):
            self._draw_text(piece.value, right_x, 32 + index * 24)
        garbage_y = 32 + len(state.next_pieces) * 24 + 18
        self._draw_text("GARBAGE", right_x, garbage_y)
        self._draw_text(str(incoming_garbage), right_x, garbage_y + 24)
        if state.game_over:
            self._draw_text("KO", right_x, garbage_y + 58)

    def _draw_text(self, text: str, x: int, y: int) -> None:
        if self._font is None:
            raise RuntimeError("view is not open")
        surface = self._font.render(text, True, (225, 225, 235))
        self.screen.blit(surface, (x, y))

    def _draw_cell(
        self,
        board_x: int,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        if y < 0:
            return
        self._pygame.draw.rect(
            self.screen,
            color,
            (
                board_x + x * self.cell_size,
                y * self.cell_size,
                self.cell_size - 1,
                self.cell_size - 1,
            ),
        )
