from collections import defaultdict
from .command import Command
class TickEngine:
    def __init__(self,games): self.games=games; self.pending=defaultdict(list); self.tick=0; self._seen=set()
    def submit(self,command):
        if command.player not in self.games: raise ValueError("unknown player")
        if command.tick<self.tick: raise ValueError("command is in the past")
        key=(command.player,command.tick,command.sequence)
        if key in self._seen: raise ValueError("duplicate command")
        self._seen.add(key); self.pending[command.tick].append(command)
    def advance(self):
        for command in sorted(self.pending.pop(self.tick,[]),key=lambda c:(c.player,c.sequence)):
            game=self.games[command.player]
            if command.action=="move_left": game.move(-1)
            elif command.action=="move_right": game.move(1)
            elif command.action=="rotate_cw": game.rotate(1)
            elif command.action=="rotate_ccw": game.rotate(-1)
            elif command.action=="soft_drop": game.move(0,1)
            elif command.action=="hard_drop": game.hard_drop()
            elif command.action=="hold": game.hold_piece()
        self.tick+=1
