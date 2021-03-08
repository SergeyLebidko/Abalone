from settings import W, H


class ThinkPane:
    COLORS = [(192,) * 3, (128,) * 3, (105,) * 3, (80,) * 3]
    SQUARE_SIZE = 30
    ALPHA = 150

    def __init__(self, pg, sc):
        self.pg = pg
        self.sc = sc
        self.surface = pg.Surface((W, H))
        self.surface.set_colorkey((0,) * 3)
        self.surface.set_alpha(self.ALPHA)
        self.show_flag = False
        self.counter = 0

    def show(self):
        self.show_flag = True
        self.counter = 0

    def hide(self):
        self.show_flag = False

    def draw(self):
        if not self.show_flag:
            return

        self.pg.draw.rect(self.surface, (0,) * 3, (10, 10, self.SQUARE_SIZE * 2, self.SQUARE_SIZE * 2))

        color_index = 0
        for x in range(10, 10 + 2 * self.SQUARE_SIZE, self.SQUARE_SIZE):
            for y in range(10, 10 + 2 * self.SQUARE_SIZE, self.SQUARE_SIZE):
                self.pg.draw.rect(self.surface, self.COLORS[color_index], (x, y, self.SQUARE_SIZE, self.SQUARE_SIZE))
                color_index += 1

        self.counter += 1
        if self.counter == 5:
            self.COLORS = [self.COLORS[-1]] + self.COLORS[:-1]
            self.counter = 0

        self.sc.blit(self.surface, (0, 0))
