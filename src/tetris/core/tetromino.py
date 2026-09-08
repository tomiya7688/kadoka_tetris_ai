from dataclasses import dataclass
from enum import Enum
from typing import Tuple
class PieceType(str, Enum):
    I="I"; O="O"; T="T"; S="S"; Z="Z"; J="J"; L="L"
@dataclass(frozen=True)
class Tetromino:
    kind: PieceType
    cells: Tuple[Tuple[int,int], ...]
SHAPES={PieceType.I:((0,1),(1,1),(2,1),(3,1)),PieceType.O:((1,0),(2,0),(1,1),(2,1)),PieceType.T:((1,0),(0,1),(1,1),(2,1)),PieceType.S:((1,0),(2,0),(0,1),(1,1)),PieceType.Z:((0,0),(1,0),(1,1),(2,1)),PieceType.J:((0,0),(0,1),(1,1),(2,1)),PieceType.L:((2,0),(0,1),(1,1),(2,1))}
def make_tetromino(kind: PieceType)->Tetromino: return Tetromino(kind,SHAPES[kind])
