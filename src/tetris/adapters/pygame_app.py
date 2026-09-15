"""Minimal interactive Pygame application adapter."""

from tetris.application import InputAction, InputRouter, TickEngine
from tetris.core import GameState
from tetris.cpu import VisibleCpuController, VisibleCpuStrategy

from .jsonl_api_server import JsonlApiServer
from .keyboard_bindings import KeyboardBindings
from .pygame_view import PygameView


class PygameApp:
    """Connect keyboard, API, or built-in CPU input to one semantic path."""

    def __init__(
        self,
        seed: int | None = None,
        fps: int = 60,
        bindings: KeyboardBindings | None = None,
        player: int = 0,
        api_port: int | None = None,
        cpu_strategy: VisibleCpuStrategy | None = None,
    ):
        if not isinstance(fps, int) or isinstance(fps, bool) or fps <= 0:
            raise ValueError("fps must be a positive integer")
        if api_port is not None and (
            not isinstance(api_port, int)
            or isinstance(api_port, bool)
            or api_port < 1
            or api_port > 65535
        ):
            raise ValueError("api_port must be between 1 and 65535")
        if api_port is not None and cpu_strategy is not None:
            raise ValueError("API input and built-in CPU cannot control the same player")

        self.bindings = bindings or KeyboardBindings.default()
        if player not in self.bindings.players:
            raise ValueError(f"unknown player: {player}")
        self.seed = seed
        self.fps = fps
        self.player = player
        self.api_port = api_port
        self.cpu_strategy = cpu_strategy

    def run(self) -> int:
        import pygame

        game = GameState(seed=self.seed)
        engine = TickEngine({self.player: game})
        router = InputRouter(engine)
        view = PygameView()
        api_server: JsonlApiServer | None = None
        cpu_controller = self._create_cpu_controller()

        try:
            view.open(game.board.width, game.board.height - game.board.hidden_rows)
            api_server = self._start_api_server()
            clock = pygame.time.Clock()

            running = True
            while running:
                running = self._submit_keyboard_events(
                    pygame,
                    router,
                    accept_actions=cpu_controller is None,
                )
                self._submit_api_actions(api_server, router)
                self._submit_cpu_action(cpu_controller, game, router)
                engine.advance()
                view.draw_state(game)
                clock.tick(self.fps)
        finally:
            if api_server is not None:
                api_server.close()
            view.close()

        return 0

    def _create_cpu_controller(self) -> VisibleCpuController | None:
        if self.cpu_strategy is None:
            return None
        return VisibleCpuController(self.player, self.cpu_strategy)

    def _start_api_server(self) -> JsonlApiServer | None:
        if self.api_port is None:
            return None
        server = JsonlApiServer(self.api_port, {self.player})
        server.start()
        return server

    def _submit_keyboard_events(
        self,
        pygame,
        router: InputRouter,
        accept_actions: bool = True,
    ) -> bool:
        running = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type != pygame.KEYDOWN or not accept_actions:
                continue

            action = self.bindings.action_for_key(
                self.player,
                pygame.key.name(event.key),
            )
            if action is None:
                continue
            router.submit(InputAction(self.player, action))
        return running

    def _submit_api_actions(
        self,
        api_server: JsonlApiServer | None,
        router: InputRouter,
    ) -> None:
        if api_server is None:
            return
        for input_action in api_server.drain():
            router.submit(input_action)

    def _submit_cpu_action(
        self,
        cpu_controller: VisibleCpuController | None,
        game: GameState,
        router: InputRouter,
    ) -> None:
        if cpu_controller is None:
            return
        input_action = cpu_controller.choose_action(game)
        if input_action is not None:
            router.submit(input_action)
