from tetris.ai import PlacementPlanner
from tetris.core import GameState
from .command import Command
from .versus import VersusSession
class AIMatchRunner:
    def __init__(self,seed_a=1,seed_b=2):
        self.session=VersusSession({0:GameState(seed_a),1:GameState(seed_b)}); self.planners={0:PlacementPlanner(),1:PlacementPlanner()}; self.sequences={0:0,1:0}
    def step(self):
        tick=self.session.engine.tick
        for player,game in self.session.games.items():
            if game.game_over: continue
            plan=self.planners[player].choose(game)
            for action in plan.actions:
                self.session.submit(Command(player,tick,self.sequences[player],action)); self.sequences[player]+=1; tick+=1
        self.session.advance()
    def run(self,max_steps=100):
        if max_steps<0: raise ValueError('max_steps must be nonnegative')
        for _ in range(max_steps):
            if any(result.defeated for result in self.session.results.values()): break
            self.step()
        return self.session.results
