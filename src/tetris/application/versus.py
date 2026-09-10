from dataclasses import dataclass
from .attack import cancel_attack
from .command import Command
from .tick_engine import TickEngine
@dataclass
class PlayerResult:
    incoming_garbage:int=0
    outgoing_attack:int=0
    defeated:bool=False
class VersusSession:
    def __init__(self,games):
        if len(games)!=2: raise ValueError('versus requires exactly two players')
        self.games=games; self.results={p:PlayerResult() for p in games}; self.engine=TickEngine(games)
    def submit(self,command:Command): self.engine.submit(command)
    def advance(self):
        self.engine.advance(); a,b=list(self.games)
        ia,ib=self.results[a].incoming_garbage,self.results[b].incoming_garbage
        self.results[a].incoming_garbage,self.results[b].incoming_garbage=cancel_attack(ia,ib)[0],cancel_attack(ib,ia)[0]
        for p in (a,b): self.results[p].defeated=self.games[p].game_over
    def queue_attack(self,player,amount):
        if player not in self.results or amount<0: raise ValueError('invalid attack')
        opponent=next(p for p in self.results if p!=player); self.results[opponent].incoming_garbage+=amount
