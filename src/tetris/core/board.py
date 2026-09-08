from .tetromino import Tetromino
class Board:
    def __init__(self,width=10,visible_height=20,hidden_rows=2):
        if width<=0 or visible_height<=0 or hidden_rows<0: raise ValueError("invalid dimensions")
        self.width=width; self.height=visible_height+hidden_rows; self.hidden_rows=hidden_rows; self._cells=[[False]*width for _ in range(self.height)]
    def occupied(self,x,y): return self._cells[y][x]
    def can_place(self,piece,origin):
        ox,oy=origin
        for x,y in piece.cells:
            px,py=ox+x,oy+y
            if px<0 or px>=self.width or py<0 or py>=self.height or self._cells[py][px]: return False
        return True
    def lock(self,piece,origin):
        if not self.can_place(piece,origin): raise ValueError("piece cannot be locked")
        ox,oy=origin
        for x,y in piece.cells: self._cells[oy+y][ox+x]=True
    def clear_full_rows(self):
        keep=[r for r in self._cells if not all(r)]; n=self.height-len(keep); self._cells=[[False]*self.width for _ in range(n)]+keep; return n
    def cells(self): return ((x,y) for y,row in enumerate(self._cells) for x,v in enumerate(row) if v)


