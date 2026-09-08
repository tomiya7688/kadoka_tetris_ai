import random
from typing import Optional
from .tetromino import PieceType
class SevenBag:
    def __init__(self, seed: Optional[int]=None): self._r=random.Random(seed); self._q=[]
    def __iter__(self): return self
    def __next__(self):
        if not self._q: self._q=list(PieceType); self._r.shuffle(self._q)
        return self._q.pop()
