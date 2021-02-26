import random
import itertools
from math import pi, sin, cos
from settings import W, H, RADIUS, BORDER


class Background:
    STEP = 10

    def __init__(self, pg):
        self.surface = pg.Surface((W, H))
        for x in range(0, W, self.STEP):
            for y in range(0, H, self.STEP):
                color_component = random.randint(230, 240)
                color = (color_component,) * 3
                pg.draw.rect(self.surface, color, (x, y, self.STEP, self.STEP))

    def draw(self, sc):
        sc.blit(self.surface, (0, 0))


class Ball:

    def __init__(self, pg):
        self.cell = None
        self.surface = pg.image.load('ball.png')
        normal = RADIUS * cos(pi / 6)
        self.surface = pg.transform.scale(self.surface, (int(1.6 * normal), int(1.6 * normal)))

    def draw(self, sc):
        ball_w, ball_h = self.surface.get_width(), self.surface.get_height()
        sc.blit(self.surface, (self.cell.x0 - ball_w // 2, self.cell.y0 - ball_h // 2))


class Cell:
    CELL_BACKGROUND_COLOR = (210,) * 3
    CELL_BORDER_COLOR = (150,) * 3
    SMOOTH_FACTOR = 0.15
    SMOOTH_DEPTH = 1

    def __init__(self, pg, x, y, key):
        self.pg = pg
        self.key = key
        self.x0, self.y0 = x, y
        self.coords = self._create_hexagon_coords()
        self.coords = self._smooth(self.coords, self.SMOOTH_DEPTH)
        self.around_cells = [None] * 6
        self.ball = None

    def __contains__(self, dot):
        x_item, y_item = dot
        tmp_coords = self.coords + [self.coords[0]]
        for (x1, y1), (x2, y2) in ((tmp_coords[index], tmp_coords[index + 1]) for index in range(len(tmp_coords) - 1)):
            a, b, c = y2 - y1, x1 - x2, y1 * (x2 - x1) - x1 * (y2 - y1)
            dot_val = self._normalize_value(a * x_item + b * y_item + c)
            if dot_val == 0:
                return True

            center_val = self._normalize_value(a * self.x0 + b * self.y0 + c)
            if dot_val != center_val:
                return False

        return True

    def draw(self, sc):
        self.pg.draw.polygon(sc, self.CELL_BACKGROUND_COLOR, self.coords)
        self.pg.draw.polygon(sc, self.CELL_BORDER_COLOR, self.coords, 1)

    def _create_hexagon_coords(self):
        alpha = pi / 6
        delta_alpha = pi / 3
        coords = []
        for _ in range(6):
            coords.append(
                (
                    self.x0 + (RADIUS - BORDER / 2) * cos(alpha),
                    self.y0 - (RADIUS - BORDER / 2) * sin(alpha)
                )
            )
            alpha += delta_alpha
        return coords

    def _smooth(self, coords, depth):
        """Метод сглаживает края гекса"""
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

            vector1 = self.SMOOTH_FACTOR * (x1 - x0), self.SMOOTH_FACTOR * (y1 - y0)
            vector2 = self.SMOOTH_FACTOR * (x2 - x0), self.SMOOTH_FACTOR * (y2 - y0)

            xa, ya = x0 + vector1[0], y0 + vector1[1]
            xb, yb = x0 + vector2[0], y0 + vector2[1]

            xc, yc = (xa + xb) / 2, (ya + yb) / 2
            xd, yd = (x0 + xc) / 2, (y0 + yc) / 2

            smooth_coords.extend([(xa, ya), (xd, yd), (xb, yb)])

        return self._smooth(smooth_coords, depth - 1)

    @staticmethod
    def _normalize_value(value):
        if value < 0:
            return -1
        elif value > 0:
            return 1
        return value


class Pool:
    DIRECTIONS = []
    for d in range(6):
        DIRECTIONS.append(
            (
                (2 * cos((pi / 3) * d) * (RADIUS * cos(pi / 6))),
                (-2 * sin((pi / 3) * d) * (RADIUS * cos(pi / 6)))
            )
        )

    DELTA_KEYS = [(0, 1, 1), (1, 0, 1), (1, -1, 0), (0, -1, -1), (-1, 0, -1), (-1, 1, 0)]

    def __init__(self, pg):
        self.pg = pg
        x0, y0 = W // 2, H // 2
        self.cells = [Cell(pg, x0, y0, (0,) * 3)]
        self.balls = []

        # Генерируем ячейки
        for path in itertools.combinations_with_replacement('012345', 4):
            x, y = x0, y0
            a, b, c = (0,) * 3
            for step in path:
                step = int(step)
                dx, dy = self.DIRECTIONS[step]
                da, db, dc = self.DELTA_KEYS[step]
                x, y = x + dx, y + dy
                a, b, c = a + da, b + db, c + dc

            for cell in self.cells:
                if (a, b, c) == cell.key:
                    break
            else:
                self.cells.append(Cell(pg, x, y, (a, b, c)))

        # Для каждой ячейки указываем смежные ей по различным направлениям
        for cell in self.cells:
            for direction, (dx, dy) in enumerate(self.DIRECTIONS):
                for target_cell in self.cells:
                    if target_cell is cell:
                        continue
                    if (cell.x0 + dx, cell.y0 + dy) in target_cell:
                        cell.around_cells[direction] = target_cell
                        break

        # Расставляем шарики по ячейкам
        for cell in self.cells:
            a, b, _ = cell.key
            if a == -4 or a == -3 or (a == -2 and b in [0, 1, 2]):
                ball = Ball(self.pg)
                ball.cell = cell
                cell.ball = ball
                self.balls.append(ball)

    def draw(self, sc):
        for cell in self.cells:
            cell.draw(sc)
        for ball in self.balls:
            ball.draw(sc)
