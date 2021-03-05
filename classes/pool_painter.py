import os
from copy import deepcopy
from math import pi, cos, sin
from settings import W, H, RADIUS, BORDER, CMP_SIDE, PLAYER_SIDE
from .pool import Pool


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
    CELL_GROUP_COLOR = (173, 255, 47)
    BALL_SCALE_FACTOR = 1.3

    SMOOTH_FACTOR = 0.15
    SMOOTH_DEPTH = 1

    TRANSPARENT_COLOR = (127,) * 3

    BALL_SIZE = int(BALL_SCALE_FACTOR * RADIUS * cos(pi / 6))

    class MoveAnimation:
        """ Класс для создания анимаций перемещения шариков """

        STEP_COUNT = 8

        def __init__(self, pool_painter, start_pos, end_pos, side, callback):
            self.pool_painter = pool_painter
            x1, y1 = start_pos
            x2, y2 = end_pos
            dx, dy = (x2 - x1) / self.STEP_COUNT, (y2 - y1) / self.STEP_COUNT
            self.steps = [(x1 + dx * index, y1 + dy * index) for index in range(self.STEP_COUNT)]
            self.steps.append(end_pos)
            self.ball_surface = pool_painter.create_ball_surface(side)
            self.callback = callback

        def animate(self):
            x, y = self.steps.pop(0)
            x, y = int(x - self.pool_painter.BALL_SIZE // 2), int(y - self.pool_painter.BALL_SIZE // 2)
            self.pool_painter.balls_surface.blit(self.ball_surface, (x, y))

            if not self.steps:
                self.callback()

        def has_animate(self):
            return len(self.steps) > 0

    class ScaleAnimation:
        """ Класс для создания анимаций появления и исчезновения шариков """

        STEP_COUNT = 8

        REMOVE_TYPE = 'remove'
        CREATE_TYPE = 'create'

        def __init__(self, pool_painter, pos, side, animation_type, callback=None):
            self.pool_painter = pool_painter
            self.pos = pos
            self.ball_surface = pool_painter.create_ball_surface(side)
            self.callback = callback
            self.steps = [
                pool_painter.BALL_SIZE * (1 - (1 / self.STEP_COUNT) * index) for index in range(1, self.STEP_COUNT)
            ]
            if animation_type == self.CREATE_TYPE:
                self.steps.reverse()

        def animate(self):
            if not self.steps:
                return

            step = self.steps.pop(0)
            self.ball_surface = self.pool_painter.pg.transform.scale(self.ball_surface, (int(step),) * 2)
            x, y = self.pos
            x, y = x - self.ball_surface.get_width() // 2, y - self.ball_surface.get_height() // 2
            self.pool_painter.balls_surface.blit(self.ball_surface, (x, y))

            if not self.steps and self.callback:
                self.callback()

        def has_animate(self):
            return len(self.steps) > 0

    def __init__(self, pg, pool, sc, cmp_color_label, player_color_label):
        self.pg = pg
        self.pool = pool
        self.sc = sc
        self.cmp_color_label = cmp_color_label
        self.player_color_label = player_color_label

        # Готовим списки ячеек и их координат
        self.cells = deepcopy(pool.cells)
        self.cells_coord = self._create_cell_coords()

        # Загружаем спрайты с красными и синими шариками
        self.cmp_ball_surface = self.create_ball_surface(CMP_SIDE)
        self.player_ball_surface = self.create_ball_surface(PLAYER_SIDE)

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

        # Ключи выделенной группы
        self.group = set()

        # Список анимаций
        self.animations = []

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

    def create_ball_surface(self, side):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        images_dir = os.path.join(base_dir, 'images')
        if side == CMP_SIDE:
            surface = self.pg.image.load(os.path.join(images_dir, f'ball_{self.cmp_color_label}.png'))
        if side == PLAYER_SIDE:
            surface = self.pg.image.load(os.path.join(images_dir, f'ball_{self.player_color_label}.png'))
        surface = self.pg.transform.scale(surface, (self.BALL_SIZE,) * 2)
        return surface

    def get_key_at_dot(self, dot):
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
        key = self.get_key_at_dot(pos)
        if key != self.key_cell_at_cursor:
            self.key_cell_at_cursor = key
            self.redraw_cells_flag = True

    def set_group(self, group):
        tmp_group = set(group)
        if tmp_group != self.group:
            self.group = tmp_group
            self.redraw_cells_flag = True

    def refresh_pool(self):
        """ Метод обновляет текущий вид доски на экране в соотвтетствие с последним ходом в пуле """

        def create_move_animation(start_key, end_key, side_key, callback_key):
            _start_pos = self.cells_coord[start_key]['x0'], self.cells_coord[start_key]['y0']
            _end_pos = self.cells_coord[end_key]['x0'], self.cells_coord[end_key]['y0']
            _side = self.cells[side_key]['content']
            _callback = create_animation_callback(callback_key, _side)
            return self.MoveAnimation(self, _start_pos, _end_pos, _side, _callback)

        def create_animation_callback(key, _side):
            def inner():
                self.cells[key]['content'] = _side

            return inner

        last_action_description = self.pool.get_last_action_description()
        if not last_action_description:
            return

        action_type = last_action_description['type']
        action = last_action_description['action']

        # Анимируем обычный ход
        if action_type == Pool.APPLY_TYPE:
            for old_key, next_key in action:
                if next_key:
                    # Создаем анимацию перемещения шарика
                    move_animation = create_move_animation(old_key, next_key, old_key, next_key)
                    self.animations.append(move_animation)
                else:
                    # Создаем анимацию удаления шарика
                    pos = self.cells_coord[old_key]['x0'], self.cells_coord[old_key]['y0']
                    side = self.cells[old_key]['content']
                    self.animations.append(self.ScaleAnimation(self, pos, side, self.ScaleAnimation.REMOVE_TYPE))

                self.cells[old_key]['content'] = None

        # Анимируем откат
        if action_type == Pool.CANCEL_TYPE:
            for index, (old_key, next_key) in enumerate(reversed(action)):
                if index == 0:
                    other_side = {CMP_SIDE: PLAYER_SIDE, PLAYER_SIDE: CMP_SIDE}[self.cells[next_key]['content']]
                if next_key:
                    # Создаем анимацию перемещения шарика
                    move_animation = create_move_animation(next_key, old_key, next_key, old_key)
                    self.animations.append(move_animation)
                else:
                    # Создаем анимацию появления шарика
                    pos = self.cells_coord[old_key]['x0'], self.cells_coord[old_key]['y0']
                    callback = create_animation_callback(old_key, other_side)
                    self.animations.append(
                        self.ScaleAnimation(self, pos, other_side, self.ScaleAnimation.CREATE_TYPE, callback=callback)
                    )

                if next_key:
                    self.cells[next_key]['content'] = None

        self.redraw_balls_flag = True

    @property
    def has_animate(self):
        return len(self.animations) > 0

    def draw(self):
        # Отрисовываем гексы
        if self.redraw_cells_flag:
            self.cells_surface.fill(self.TRANSPARENT_COLOR)
            for key, cell_coord in self.cells_coord.items():
                coords = cell_coord['coords']
                color = self.CELL_BACKGROUND_COLOR

                if key == self.key_cell_at_cursor:
                    color = self.CELL_AT_CURSOR_COLOR
                if key in self.group:
                    color = self.CELL_GROUP_COLOR

                self.pg.draw.polygon(self.cells_surface, color, coords)
                self.pg.draw.polygon(self.cells_surface, self.CELL_BORDER_COLOR, coords, 1)

            self.redraw_cells_flag = False

        # Отрисовываем шарики
        if self.redraw_balls_flag:
            self.balls_surface.fill(self.TRANSPARENT_COLOR)
            for key, cell in self.cells.items():
                ball = cell['content']
                if not ball:
                    continue

                ball_surface = None
                if ball == CMP_SIDE:
                    ball_surface = self.cmp_ball_surface
                if ball == PLAYER_SIDE:
                    ball_surface = self.player_ball_surface

                ball_w, ball_h = ball_surface.get_width(), ball_surface.get_height()
                x, y = self.cells_coord[key]['x0'], self.cells_coord[key]['y0']
                self.balls_surface.blit(ball_surface, (x - ball_w // 2, y - ball_h // 2))

            if self.animations:
                for animation in self.animations:
                    animation.animate()
                self.animations = list(filter(lambda val: val.has_animate(), self.animations))

            self.redraw_balls_flag = False or len(self.animations) > 0

            # Объединяем поверхности
        self.sc.blit(self.cells_surface, (0, 0))
        self.sc.blit(self.balls_surface, (0, 0))
