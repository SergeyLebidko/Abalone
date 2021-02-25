import itertools
import pygame as pg
from math import pi, sqrt, sin, cos

W, H = 1200, 900
TITLE = 'Abalone'
BACKGROUND_COLOR = (240, 240, 240)

RADIUS = 60
BORDER = 6
NORMAL = RADIUS * cos(pi / 6)

DIRECTIONS = [((2 * cos((pi / 3) * d) * NORMAL), (-2 * sin((pi / 3) * d) * NORMAL)) for d in range(6)]


def create_hexagon_coords(x0, y0):
    alpha = pi / 6
    delta_alpha = pi / 3
    coords = []
    for _ in range(6):
        coords.append(
            (
                x0 + (RADIUS - BORDER / 2) * cos(alpha),
                y0 - (RADIUS - BORDER / 2) * sin(alpha)
            )
        )
        alpha += delta_alpha
    return smooth(coords, 1)


def smooth(coords, depth=1):
    """Функция сглаживает края гекса"""
    if depth == 0:
        return coords

    smooth_coords = []
    for index in range(len(coords)):
        x0, y0 = coords[index]
        try:
            x1, y1 = coords[index - 1]
        except IndexError:
            x1, y1 = coords[-1]
        try:
            x2, y2 = coords[index + 1]
        except IndexError:
            x2, y2 = coords[0]

        vector1 = 0.15 * (x1 - x0), 0.15 * (y1 - y0)
        vector2 = 0.15 * (x2 - x0), 0.15 * (y2 - y0)

        xa, ya = x0 + vector1[0], y0 + vector1[1]
        xb, yb = x0 + vector2[0], y0 + vector2[1]

        xc, yc = (xa + xb) / 2, (ya + yb) / 2
        xd, yd = (x0 + xc) / 2, (y0 + yc) / 2

        smooth_coords.extend([(xa, ya), (xd, yd), (xb, yb)])

    return smooth(smooth_coords, depth - 1)


def normalize_value(value):
    if value < 0:
        return -1
    elif value > 0:
        return 1
    return value


class Cell:
    CELL_BACKGROUND_COLOR = (220, 220, 220)

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.coords = create_hexagon_coords(x, y)
        self.around_cells = [None] * 6

    def __contains__(self, item):
        x_item, y_item = item
        tmp_coords = self.coords + [self.coords[0]]
        for (x1, y1), (x2, y2) in ((tmp_coords[index], tmp_coords[index + 1]) for index in range(len(tmp_coords) - 1)):
            a, b, c = y2 - y1, x1 - x2, y1 * (x2 - x1) - x1 * (y2 - y1)
            dot_val = normalize_value(a * x_item + b * y_item + c)
            if dot_val == 0:
                return True

            center_val = normalize_value(a * self.x + b * self.y + c)
            if dot_val != center_val:
                return False

        return True

    def draw(self, sc):
        pg.draw.polygon(sc, self.CELL_BACKGROUND_COLOR, self.coords)


class Pool:

    def __init__(self):
        x0, y0 = W // 2, H // 2
        self.cells = [Cell(x0, y0)]

        # Генерируем ячейки
        for path in itertools.combinations_with_replacement('012345', 4):
            x, y = x0, y0
            for step in path:
                step = int(step)
                dx, dy = DIRECTIONS[step]
                x, y = x + dx, y + dy

            for cell in self.cells:
                if (x, y) in cell:
                    break
            else:
                self.cells.append(Cell(x, y))

        # Для каждой ячейки указываем смежные ей по различным направлениям
        for cell in self.cells:
            for direction, (dx, dy) in enumerate(DIRECTIONS):
                for target_cell in self.cells:
                    if target_cell is cell:
                        continue
                    if (cell.x + dx, cell.y + dy) in target_cell:
                        cell.around_cells[direction] = target_cell
                        break

    def draw(self, sc):
        for cell in self.cells:
            cell.draw(sc)


def main():
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    pool = Pool()

    while True:

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        sc.fill(BACKGROUND_COLOR)
        pool.draw(sc)
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    main()
