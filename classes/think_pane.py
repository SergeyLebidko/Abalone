from datetime import datetime
from settings import W, H


class ThinkPane:
    COLORS = [(255, 69, 0), (0, 255, 0), (30, 144, 255), (255, 255, 0)]
    SQUARE_SIZE = 20
    ALPHA = 150

    def __init__(self, pg, sc):
        self.pg = pg
        self.sc = sc
        self.surface = pg.Surface((W, H))
        self.surface.set_colorkey((0,) * 3)
        self.surface.set_alpha(self.ALPHA)
        self.show_flag = False
        self.t1 = datetime.now().second

    def show(self):
        self.show_flag = True

    def hide(self):
        self.show_flag = False

    def draw(self):
        if not self.show_flag:
            return

        self.pg.draw.rect(
            self.surface,
            (0,) * 3,
            (W // 2 - self.SQUARE_SIZE, H // 2 - self.SQUARE_SIZE, self.SQUARE_SIZE * 2, self.SQUARE_SIZE * 2)
        )

        color_index = 0
        for x in range(W // 2 - self.SQUARE_SIZE, W // 2 + self.SQUARE_SIZE, self.SQUARE_SIZE):
            for y in range(H // 2 - self.SQUARE_SIZE, H // 2 + self.SQUARE_SIZE, self.SQUARE_SIZE):
                self.pg.draw.rect(self.surface, self.COLORS[color_index], (x, y, self.SQUARE_SIZE, self.SQUARE_SIZE))
                color_index += 1

        t2 = datetime.now().second
        if t2 != self.t1:
            self.COLORS = [self.COLORS[-1]] + self.COLORS[:-1]
            self.t1 = t2

        self.sc.blit(self.surface, (0, 0))
