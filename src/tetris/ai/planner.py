from dataclasses import dataclass
from tetris.core import Board, GameState, Tetromino
from .heuristic import HeuristicEvaluator
@dataclass(frozen=True)
class PlannedMove:
    rotation: int
    x: int
    score: float
    actions: tuple[str,...]
class PlacementPlanner:
    def __init__(self,evaluator=None): self.evaluator=evaluator or HeuristicEvaluator()
    def choose(self,state: GameState) -> PlannedMove:
        piece=state.active; best=None
        for rotation in range(4):
            cells=piece.cells()
            candidate_cells=cells
            for _ in range(rotation):
                candidate_cells=tuple((-y,x) for x,y in candidate_cells); mx=min(x for x,y in candidate_cells); my=min(y for x,y in candidate_cells); candidate_cells=tuple((x-mx,y-my) for x,y in candidate_cells)
            max_x=state.board.width-max(x for x,y in candidate_cells)-1
            for x in range(-min(x for x,y in candidate_cells),max_x+1):
                y=0
                while state.board.can_place(Tetromino(piece.kind,candidate_cells),(x,y+1)): y+=1
                if not state.board.can_place(Tetromino(piece.kind,candidate_cells),(x,y)): continue
                board=Board(state.board.width,state.board.height-state.board.hidden_rows,state.board.hidden_rows)
                for bx,by in state.board.cells(): board._cells[by][bx]=True
                board.lock(Tetromino(piece.kind,candidate_cells),(x,y)); cleared=board.clear_full_rows(); score=self.evaluator.score(board,cleared)
                actions=(('rotate_cw',)*rotation)+(('move_left',)*max(0,piece.x-x) if x<piece.x else ('move_right',)*(x-piece.x))+('hard_drop',)
                move=PlannedMove(rotation,x,score,actions)
                if best is None or move.score>best.score: best=move
        if best is None: raise ValueError('no legal placement')
        return best
