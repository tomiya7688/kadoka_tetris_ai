from dataclasses import dataclass
from .tetromino import PieceType, SHAPES
@dataclass
class ActivePiece:
    kind: PieceType
    x: int=3
    y: int=0
    rotation: int=0
    def cells(self):
        cells=SHAPES[self.kind]
        for _ in range(self.rotation % 4):
            cells=tuple((-y,x) for x,y in cells)
            min_x=min(x for x,y in cells); min_y=min(y for x,y in cells)
            cells=tuple((x-min_x,y-min_y) for x,y in cells)
        return cells
