import random
import itertools
from copy import deepcopy
from math import pi, sin, cos
from settings import W, H, RADIUS, BORDER, CMP_SIDE, PLAYER_SIDE


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


class Pool:
    DELTA_KEYS = [(0, 1, 1), (1, 0, 1), (1, -1, 0), (0, -1, -1), (-1, 0, -1), (-1, 1, 0)]

    def __init__(self):
        self.cells = {
            (0, 0, 0): {
                'content': None,
                'around': [None] * 6
            }
        }

        # Генерируем ячейки
        for path in itertools.combinations_with_replacement('012345', 4):
            a, b, c = (0,) * 3
            for step in path:
                step = int(step)
                da, db, dc = self.DELTA_KEYS[step]
                a, b, c = a + da, b + db, c + dc

            if (a, b, c) not in self.cells:
                self.cells[(a, b, c)] = {
                    'content': None,
                    'around': [None] * 6
                }

        # Для каждой ячейки указываем смежные ей по различным направлениям
        for (a, b, c), cell in self.cells.items():
            for direction, (da, db, dc) in enumerate(self.DELTA_KEYS):
                a, b, c = a + da, b + db, c + dc
                if (a, b, c) in self.cells:
                    cell['around'][direction] = (a, b, c)

        # Расставляем шарики по ячейкам
        cmp_cell_keys = self._get_cmp_init_data()
        player_cell_keys = self._get_player_init_data()
        ball_key = 0
        for key, cell in self.cells.items():
            if key in cmp_cell_keys:
                cell['content'] = dict(side=CMP_SIDE, key=ball_key)
            if key in player_cell_keys:
                cell['content'] = dict(side=PLAYER_SIDE, key=ball_key)
            ball_key += 1

    @staticmethod
    def _get_cmp_init_data():
        result = []
        for a in range(-4, 5):
            for b in range(-4, 5):
                for c in range(-4, 5):
                    if a == 4 or a == 3 or (a == 2 and b in [0, -1, -2]):
                        result.append((a, b, c))
        return result

    @staticmethod
    def _get_player_init_data():
        result = []
        for a in range(-4, 5):
            for b in range(-4, 5):
                for c in range(-4, 5):
                    if a == -4 or a == -3 or (a == -2 and b in [0, 1, 2]):
                        result.append((a, b, c))
        return result


class PoolPainter:
    DIRECTIONS = []
    for d in range(6):
        DIRECTIONS.append(
            (
                (2 * cos((pi / 3) * d) * (RADIUS * cos(pi / 6))),
                (-2 * sin((pi / 3) * d) * (RADIUS * cos(pi / 6)))
            )
        )

    CELL_BACKGROUND_COLOR = (210,) * 3
    CELL_BORDER_COLOR = (150,) * 3
    CELL_AT_CURSOR_COLOR = (230,) * 3
    BALL_SCALE_FACTOR = 1.3

    SMOOTH_FACTOR = 0.15
    SMOOTH_DEPTH = 1

    TRANSPARENT_COLOR = (127,) * 3

    def __init__(self, pg, pool, sc, cmp_color_label, player_color_label):
        self.pg = pg
        self.pool = pool
        self.sc = sc

        # Готовим списки ячеек и их координат
        self.cells = deepcopy(pool.cells)
        self.cells_coord = self._create_cell_coords()

        # Загружаем спрайты с красными и синими шариками
        self.ball_size = int(self.BALL_SCALE_FACTOR * RADIUS * cos(pi / 6))

        self.cmp_ball_surface = pg.image.load(f'ball_{cmp_color_label}.png')
        self.cmp_ball_surface = pg.transform.scale(self.cmp_ball_surface, (self.ball_size,) * 2)

        self.player_ball_surface = pg.image.load(f'ball_{player_color_label}.png')
        self.player_ball_surface = pg.transform.scale(self.player_ball_surface, (self.ball_size,) * 2)

        # Готовим поверхности для отрисовки ячеек и шариков
        self.cells_surface = pg.Surface((W, H))
        self.cells_surface.set_colorkey(self.TRANSPARENT_COLOR)
        self.cells_surface.fill(self.TRANSPARENT_COLOR)

        self.balls_surface = pg.Surface((W, H))
        self.balls_surface.set_colorkey(self.TRANSPARENT_COLOR)
        self.balls_surface.fill(self.TRANSPARENT_COLOR)

        # Флаги необходимости перерисовки
        self.redraw_cells_flag = True
        self.redraw_balls_flag = True

        # Ключ ячейки под курсором
        self.key_cell_at_cursor = None

    def _create_cell_coords(self):
        """Метод создает координаты ячеек игрового поля по их ключам"""

        result = {}
        for key, cell in self.cells.items():
            center = self._create_hexagon_center(key)
            coords = self._create_hexagon_coords(center)
            result[key] = {
                'x0': center[0],
                'y0': center[1],
                'coords': coords
            }

        return result

    def _create_hexagon_center(self, key):
        """Метод возвращает координаты центра гекса по переданному ключу"""

        a, b, _ = key
        x0, y0 = W // 2, H // 2

        dx, dy = self.DIRECTIONS[1]
        x0 += (dx * a)
        y0 += (dy * a)

        dx, dy = self.DIRECTIONS[0]
        x0 += (dx * b)
        y0 += (dy * b)

        return x0, y0

    def _create_hexagon_coords(self, center):
        """Метод возвращает координаты точек отрезков-сторон гекса по координатам его центра"""

        x0, y0 = center
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
        return self._smooth(coords, self.SMOOTH_DEPTH)

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

    def _cell_at_dot(self, dot):
        """
        Метод возвращает ключ ячейки, в которую попадает переданная точка.
        Если переданная точка не попадает ни в одну ячейку - возвращает None
        """

        x, y = dot
        for key, cell_coord in self.cells_coord.items():
            x0 = cell_coord['x0']
            y0 = cell_coord['y0']
            coords = cell_coord['coords']
            tmp_coords = coords + [coords[0]]
            len_tmp_coords = len(tmp_coords)
            for (x1, y1), (x2, y2) in ((tmp_coords[i], tmp_coords[i + 1]) for i in range(len_tmp_coords - 1)):
                factor_a, factor_b, factor_c = y2 - y1, x1 - x2, y1 * (x2 - x1) - x1 * (y2 - y1)
                dot_val = self._normalize_value(factor_a * x + factor_b * y + factor_c)
                if dot_val == 0:
                    return key

                center_val = self._normalize_value(factor_a * x0 + factor_b * y0 + factor_c)
                if dot_val != center_val:
                    break

            else:
                return key

        return None

    def set_cursor_pos(self, pos):
        """ Метод устанавливает координаты курсора (для выделения ячейки под курсором)"""

        key = self._cell_at_dot(pos)
        if key != self.key_cell_at_cursor:
            self.key_cell_at_cursor = key
            self.redraw_cells_flag = True

    def draw(self):
        # Отрисовываем гексы
        if self.redraw_cells_flag:
            self.cells_surface.fill(self.TRANSPARENT_COLOR)
            for key, cell_coord in self.cells_coord.items():
                coords = cell_coord['coords']
                if key == self.key_cell_at_cursor:
                    self.pg.draw.polygon(self.cells_surface, self.CELL_AT_CURSOR_COLOR, coords)
                else:
                    self.pg.draw.polygon(self.cells_surface, self.CELL_BACKGROUND_COLOR, coords)
                self.pg.draw.polygon(self.cells_surface, self.CELL_BORDER_COLOR, coords, 1)

            self.redraw_cells_flag = False

        # Отрисовываем шарики
        if self.redraw_balls_flag:
            self.balls_surface.fill(self.TRANSPARENT_COLOR)
            for key, cell in self.cells.items():
                ball = cell['content']
                if not ball:
                    continue

                side = ball['side']
                ball_surface = None
                if side == CMP_SIDE:
                    ball_surface = self.cmp_ball_surface
                if side == PLAYER_SIDE:
                    ball_surface = self.player_ball_surface

                ball_w, ball_h = ball_surface.get_width(), ball_surface.get_height()
                x, y = self.cells_coord[key]['x0'], self.cells_coord[key]['y0']
                self.balls_surface.blit(ball_surface, (x - ball_w // 2, y - ball_h // 2))

            self.redraw_balls_flag = False

        # Объединяем поверхности
        self.sc.blit(self.cells_surface, (0, 0))
        self.sc.blit(self.balls_surface, (0, 0))
