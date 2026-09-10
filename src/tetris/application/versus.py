from dataclasses import dataclass
from .attack import cancel_attack
from .command import Command
from .tick_engine import TickEngine
@dataclass
class PlayerResult:
    incoming_garbage: int=0
    outgoing_attack: int=0
    defeated: bool=False
class VersusSession:
    def __init__(self,games):
        if len(games)!=2: raise ValueError("versus requires exactly two players")
        self.games=games; self.results={player:PlayerResult() for player in games}; self.engine=TickEngine(games)
    def submit(self,command: Command): self.engine.submit(command)
    def advance(self):
        self.engine.advance()
        players=list(self.games)
        for player in players:
            opponent=players[1] if player==players[0] else players[0]
            own=self.results[player]; other=self.results[opponent]
            incoming, outgoing=cancel_attack(own.incoming_garbage,own.outgoing_attack)
            own.incoming_garbage=incoming; other.outgoing_attack=outgoing
            own.defeated=self.games[player].game_over
    def queue_attack(self,player,amount):
        if player not in self.results or amount<0: raise ValueError("invalid attack")
        opponent=next(p for p in self.results if p!=player); self.results[opponent].incoming_garbage+=amount
