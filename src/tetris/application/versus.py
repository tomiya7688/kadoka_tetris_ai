from dataclasses import dataclass

from .attack import attack_for_event, cancel_attack
from .command import Command
from .tick_engine import TickEngine


@dataclass
class PlayerResult:
    incoming_garbage: int = 0
    outgoing_attack: int = 0
    cancelled_garbage: int = 0
    lines_cleared: int = 0
    t_spins: int = 0
    perfect_clears: int = 0
    max_combo: int = 0
    defeated: bool = False


class VersusSession:
    def __init__(self, games):
        if len(games) != 2:
            raise ValueError("versus requires exactly two players")
        self.games = games
        self.results = {player: PlayerResult() for player in games}
        self.engine = TickEngine(games)
        self._seen_lock_ids = {
            player: game.pieces_locked
            for player, game in games.items()
        }

    def submit(self, command: Command):
        self.engine.submit(command)

    def advance(self):
        self.engine.advance()
        for player, game in self.games.items():
            event = game.last_lock_event
            if event is None or event.lock_id <= self._seen_lock_ids[player]:
                continue
            self._seen_lock_ids[player] = event.lock_id
            result = self.results[player]
            result.lines_cleared += event.lines
            result.t_spins += int(event.t_spin)
            result.perfect_clears += int(event.perfect_clear)
            result.max_combo = max(result.max_combo, event.combo)
            attack = attack_for_event(event)
            if attack:
                self.queue_attack(player, attack)

        player_a, player_b = list(self.games)
        incoming_a = self.results[player_a].incoming_garbage
        incoming_b = self.results[player_b].incoming_garbage
        remaining_a, remaining_b = cancel_attack(incoming_a, incoming_b)
        cancelled = min(incoming_a, incoming_b)
        self.results[player_a].incoming_garbage = remaining_a
        self.results[player_b].incoming_garbage = remaining_b
        if cancelled:
            self.results[player_a].cancelled_garbage += cancelled
            self.results[player_b].cancelled_garbage += cancelled

        for player in (player_a, player_b):
            self.results[player].defeated = self.games[player].game_over

    def queue_attack(self, player, amount):
        if (
            player not in self.results
            or not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount < 0
        ):
            raise ValueError("invalid attack")
        opponent = next(candidate for candidate in self.results if candidate != player)
        self.results[player].outgoing_attack += amount
        self.results[opponent].incoming_garbage += amount
