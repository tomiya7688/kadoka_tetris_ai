"""Deterministic board features and a simple placement evaluator."""
from tetris.core import Board
class HeuristicEvaluator:
    def __init__(self, weights=None):
        self.weights={"lines":1.0,"holes":-2.0,"aggregate_height":-0.5,"bumpiness":-0.3}; self.weights.update(weights or {})
    def score(self, board: Board, cleared_lines=0) -> float:
        heights=[]; holes=0
        for x in range(board.width):
            ys=[y for xx,y in board.cells() if xx==x]
            top=min(ys) if ys else board.height
            heights.append(board.height-top)
            if ys:
                holes += sum(1 for y in range(top,board.height) if not board.occupied(x,y))
        bump=sum(abs(a-b) for a,b in zip(heights,heights[1:]))
        return (self.weights["lines"]*cleared_lines + self.weights["holes"]*holes + self.weights["aggregate_height"]*sum(heights) + self.weights["bumpiness"]*bump)
