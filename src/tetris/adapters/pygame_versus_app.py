"""Playable two-board versus adapter using the shared semantic input path."""

from tetris.application import InputAction, InputRouter, VersusSession
from tetris.core import GameState
from tetris.cpu import VisibleVersusCpuController, VisibleVersusCpuStrategy

from .keyboard_bindings import KeyboardBindings
from .pygame_versus_view import PygameVersusView


class PygameVersusApp:
    """Run keyboard versus play with an optional visible-only CPU as player 2."""

    def __init__(
        self,
        seed_a: int | None = None,
        seed_b: int | None = None,
        garbage_seed: int = 0,
        fps: int = 60,
        bindings: KeyboardBindings | None = None,
        cpu_strategy: VisibleVersusCpuStrategy | None = None,
    ):
        if not isinstance(fps, int) or isinstance(fps, bool) or fps <= 0:
            raise ValueError("fps must be a positive integer")
        if not isinstance(garbage_seed, int) or isinstance(garbage_seed, bool):
            raise ValueError("garbage_seed must be an integer")
        self.seed_a = seed_a
        self.seed_b = seed_b
        self.garbage_seed = garbage_seed
        self.fps = fps
        self.bindings = bindings or KeyboardBindings.default()
        if set(self.bindings.players) != {0, 1}:
            raise ValueError("versus mode requires keyboard bindings for players 0 and 1")
        self.cpu_strategy = cpu_strategy

    def run(self) -> int:
        import pygame

        games = {
            0: GameState(seed=self.seed_a),
            1: GameState(seed=self.seed_b),
        }
        session = VersusSession(games, garbage_seed=self.garbage_seed)
        router = InputRouter(session.engine)
        view = PygameVersusView()
        cpu_controller = self._create_cpu_controller()

        try:
            sample = games[0]
            view.open(
                sample.board.width,
                sample.board.height - sample.board.hidden_rows,
            )
            clock = pygame.time.Clock()
            running = True
            while running:
                running = self._submit_keyboard_events(
                    pygame,
                    router,
                    cpu_player=cpu_controller.player if cpu_controller is not None else None,
                )
                self._submit_cpu_action(cpu_controller, session, router)
                session.advance()
                view.draw_states(
                    games,
                    {
                        player: session.results[player].incoming_garbage
                        for player in games
                    },
                )
                clock.tick(self.fps)
        finally:
            view.close()
        return 0

    def _create_cpu_controller(self) -> VisibleVersusCpuController | None:
        if self.cpu_strategy is None:
            return None
        return VisibleVersusCpuController(1, self.cpu_strategy)

    def _submit_keyboard_events(
        self,
        pygame,
        router: InputRouter,
        cpu_player: int | None,
    ) -> bool:
        running = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type != pygame.KEYDOWN:
                continue

            key_name = pygame.key.name(event.key)
            for player in sorted(self.bindings.players):
                if player == cpu_player:
                    continue
                action = self.bindings.action_for_key(player, key_name)
                if action is not None:
                    router.submit(InputAction(player, action))
        return running

    def _submit_cpu_action(
        self,
        cpu_controller: VisibleVersusCpuController | None,
        session: VersusSession,
        router: InputRouter,
    ) -> None:
        if cpu_controller is None or session.games[cpu_controller.player].game_over:
            return
        input_action = cpu_controller.choose_action(session)
        if input_action is not None:
            router.submit(input_action)
