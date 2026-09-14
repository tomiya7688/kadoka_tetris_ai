"""Minimal interactive Pygame application adapter."""

from tetris.application import Command, TickEngine
from tetris.core import GameState

from .keyboard_bindings import KeyboardBindings
from .pygame_view import PygameView


class PygameApp:
    """Connect Pygame events to the shared semantic command path."""

    def __init__(
        self,
        seed: int | None = None,
        fps: int = 60,
        bindings: KeyboardBindings | None = None,
        player: int = 0,
    ):
        if fps <= 0:
            raise ValueError("fps must be greater than zero")
        self.bindings = bindings or KeyboardBindings.default()
        if player not in self.bindings.players:
            raise ValueError(f"unknown player: {player}")
        self.seed = seed
        self.fps = fps
        self.player = player

    def run(self) -> int:
        import pygame

        game = GameState(seed=self.seed)
        engine = TickEngine({self.player: game})
        view = PygameView()
        view.open(game.board.width, game.board.height - game.board.hidden_rows)
        clock = pygame.time.Clock()
        sequence = 0

        try:
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        continue
                    if event.type != pygame.KEYDOWN:
                        continue

                    action = self.bindings.action_for_key(
                        self.player,
                        pygame.key.name(event.key),
                    )
                    if action is None:
                        continue

                    engine.submit(
                        Command(self.player, engine.tick, sequence, action)
                    )
                    sequence += 1

                engine.advance()
                view.draw_state(game)
                clock.tick(self.fps)
        finally:
            view.close()

        return 0
