"""Optional Pygame view; the rules engine remains GUI-independent."""
from tetris.core import Board
class PygameView:
    def __init__(self, cell_size=24):
        self.cell_size=cell_size; self._pygame=None; self.screen=None
    def open(self,width=10,height=20):
        import pygame
        self._pygame=pygame; pygame.init(); self.screen=pygame.display.set_mode((width*self.cell_size,height*self.cell_size)); pygame.display.set_caption("Kadoka Tetris")
    def draw(self,board: Board):
        if self.screen is None: raise RuntimeError("view is not open")
        pg=self._pygame; self.screen.fill((15,15,20))
        for x,y in board.cells():
            pg.draw.rect(self.screen,(80,190,220),(x*self.cell_size,(y-board.hidden_rows)*self.cell_size,self.cell_size-1,self.cell_size-1))
        pg.display.flip()
    def close(self):
        if self._pygame is not None: self._pygame.quit()
