import random
from settings import W, H


class Background:
    STEP = 10

    def __init__(self, pg, sc):
        self.sc = sc
        self.surface = pg.Surface((W, H))
        for x in range(0, W, self.STEP):
            for y in range(0, H, self.STEP):
                color_component = random.randint(230, 240)
                color = (color_component,) * 3
                pg.draw.rect(self.surface, color, (x, y, self.STEP, self.STEP))

    def draw(self):
        self.sc.blit(self.surface, (0, 0))
