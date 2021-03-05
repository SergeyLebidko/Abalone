import random
import itertools
from copy import deepcopy
from math import pi, sin, cos
from settings import W, H, RADIUS, BORDER, CMP_SIDE, PLAYER_SIDE


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


class Pool:
    DELTA_KEYS = [(0, 1, 1), (1, 0, 1), (1, -1, 0), (0, -1, -1), (-1, 0, -1), (-1, 1, 0)]

    LINE_PATTERNS = ['***##r', '**#r', '***##e', '***#e', '**#e', '***e', '**e']

    def __init__(self):
        self.actions = []
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
                _a, _b, _c = a + da, b + db, c + dc
                if (_a, _b, _c) in self.cells:
                    cell['around'][direction] = (_a, _b, _c)

        # Расставляем шарики по ячейкам
        cmp_cell_keys = self._get_cmp_init_data()
        player_cell_keys = self._get_player_init_data()
        for key, cell in self.cells.items():
            if key in cmp_cell_keys:
                cell['content'] = CMP_SIDE
            if key in player_cell_keys:
                cell['content'] = PLAYER_SIDE

    def create_actions(self, side):
        line_actions = self._create_line_actions(side)
        shift_actions = self._create_shift_actions(side)
        print(f'line: {len(line_actions)} shift: {len(shift_actions)} total: {len(line_actions) + len(shift_actions)}')
        return line_actions + shift_actions

    def apply_action(self, action):
        self.actions.append(action)
        for old_key, next_key in action:
            old_cell = self.cells[old_key]
            side = old_cell['content']
            old_cell['content'] = None
            if not next_key:
                continue

            next_cell = self.cells[next_key]
            next_cell['content'] = side

    @property
    def last_action(self):
        if self.actions:
            return self.actions[-1]
        return None

    def get_winner_side(self):
        cmp_count = 0
        player_count = 0
        for _, cell in self.cells.items():
            if cell['content'] == CMP_SIDE:
                cmp_count += 1
            if cell['content'] == PLAYER_SIDE:
                player_count += 1
        if cmp_count < 9:
            return PLAYER_SIDE
        if player_count < 9:
            return CMP_SIDE
        return None

    @property
    def cmp_balls_count(self):
        return self._balls_count(CMP_SIDE)

    @property
    def player_balls_count(self):
        return self._balls_count(PLAYER_SIDE)

    def _balls_count(self, side):
        result = 0
        for cell in self.cells.values():
            if cell['content'] == side:
                result += 1
        return result

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

    def _create_shift_actions(self, side):
        cells_side = self._get_side_cells(side)
        result = []

        # Внешний цикл - перебор длин цепочки
        for count in range(3, 0, -1):
            if count == 1:
                for key, cell in cells_side.items():
                    for n_key in cell['around']:
                        if not n_key or self.cells[n_key]['content']:
                            continue
                        result.append([(key, n_key)])
            else:
                # Создаем группы ячеек
                groups = []
                for key, cell in cells_side.items():
                    for direction in range(3):
                        group_keys = [key]
                        try:
                            for _ in range(count - 1):
                                n_key = cells_side[group_keys[-1]]['around'][direction]
                                if self.cells[n_key]['content'] != side:
                                    raise KeyError
                                group_keys.append(n_key)
                        except KeyError:
                            continue

                        groups.append({
                            'directions': [direction, direction + 3],
                            'keys': group_keys
                        })

                # Проверяем каждую группу на возможность сдвига. Если она есть - фиксируем соответствующие операции
                for group in groups:
                    directions = group['directions']
                    keys = group['keys']

                    for direction in range(6):
                        if direction in directions:
                            continue

                        action = []
                        for key in keys:
                            n_key = self.cells[key]['around'][direction]
                            if not n_key:
                                break
                            n_cell = self.cells[n_key]
                            if n_cell['content']:
                                break
                            action.append((key, n_key))
                        else:
                            result.append(action)

        return result

    def _create_line_actions(self, side):
        cells_side = self._get_side_cells(side)
        other_side = {CMP_SIDE: PLAYER_SIDE, PLAYER_SIDE: CMP_SIDE}[side]

        # Формируем группы ячеек и паттерны для них
        groups = []
        for direction in range(6):
            for key in cells_side:
                group_keys = [key]
                pattern = ''
                while True:
                    last_key = group_keys[-1]
                    if last_key is None:
                        pattern += 'r'
                        break
                    content = self.cells[last_key]['content']
                    if content == side:
                        pattern += '*'
                    elif content == other_side:
                        pattern += '#'
                    elif content is None:
                        pattern += 'e'
                        break

                    group_keys.append(self.cells[last_key]['around'][direction])

                if pattern in self.LINE_PATTERNS:
                    groups.append({
                        'pattern': pattern,
                        'keys': group_keys
                    })

        # Сортируем группы по важности хода
        groups.sort(key=lambda x: self.LINE_PATTERNS.index(x['pattern']))

        # Строим итоговый список ходов
        result = []
        for group in groups:
            actions = []
            keys = group['keys']
            for index in range(len(keys) - 1, 0, -1):
                actions.append((keys[index - 1], keys[index]))

            result.append(actions)

        return result

    def _get_side_cells(self, side):
        return {key: cell for key, cell in self.cells.items() if cell['content'] == side}


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

    class RemoveAnimation:
        """ Класс для создания анимаций удаления шариков """

        STEP_COUNT = 8

        def __init__(self, pool_painter, pos, side):
            self.pool_painter = pool_painter
            self.pos = pos
            self.ball_surface = pool_painter.create_ball_surface(side)
            self.steps = [
                pool_painter.BALL_SIZE * (1 - (1 / self.STEP_COUNT) * index) for index in range(self.STEP_COUNT)
            ]

        def animate(self):
            if not self.steps:
                return

            step = self.steps.pop(0)
            self.ball_surface = self.pool_painter.pg.transform.scale(self.ball_surface, (int(step),) * 2)
            x, y = self.pos
            x, y = x - self.ball_surface.get_width() // 2, y - self.ball_surface.get_height() // 2
            self.pool_painter.balls_surface.blit(self.ball_surface, (x, y))

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
        if side == CMP_SIDE:
            surface = self.pg.image.load(f'ball_{self.cmp_color_label}.png')
        if side == PLAYER_SIDE:
            surface = self.pg.image.load(f'ball_{self.player_color_label}.png')
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

        def create_move_animation_callback(key, _side):
            def inner():
                self.cells[key]['content'] = _side

            return inner

        action = self.pool.last_action
        if not action:
            return

        for old_key, next_key in action:
            if next_key:
                # Если следующий ключ существует, то создаем анимацию перемещения шарика
                start_pos = self.cells_coord[old_key]['x0'], self.cells_coord[old_key]['y0']
                end_pos = self.cells_coord[next_key]['x0'], self.cells_coord[next_key]['y0']
                side = self.cells[old_key]['content']
                callback = create_move_animation_callback(next_key, side)
                self.animations.append(self.MoveAnimation(self, start_pos, end_pos, side, callback))
            else:
                # Если следующего ключа нет, то создаем анимацию удаления шарика
                pos = self.cells_coord[old_key]['x0'], self.cells_coord[old_key]['y0']
                side = self.cells[old_key]['content']
                self.animations.append(self.RemoveAnimation(self, pos, side))

            self.cells[old_key]['content'] = None

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


class Group:

    def __init__(self, pool_painter):
        self.pool_painter = pool_painter
        self.group = []

    def click(self, pos):
        """ Метод добавляет в группу ячейку, на которую кликнул игрок. Координаты клика передаются в параметре pos """

        key = self.pool_painter.get_key_at_dot(pos)

        # Если игрок кликнул не на ячейке поля - очищаем группу
        if not key:
            self.clear()
            return

        # Если игрок кликнул на ячейке без ширика или на ячейке с вражеским шариком - очищаем группу
        ball = self.pool_painter.cells[key]['content']
        if not ball or ball != PLAYER_SIDE:
            self.clear()
            return

        # Блокируем возможность повторного добавления в группу уже имеющейся там ячейки
        if key in self.group:
            return

        # Проверяем нужна ли очистка группы (и выполняем её, если нужно) перед добавлением в ячейки
        if self.group:
            group_size = len(self.group)
            if group_size == 3:
                self.group = []
            else:
                tmp_group = self.group + [key]
                max_a = max(tmp_group, key=lambda value: value[0])[0]
                min_a = min(tmp_group, key=lambda value: value[0])[0]
                max_b = max(tmp_group, key=lambda value: value[1])[1]
                min_b = min(tmp_group, key=lambda value: value[1])[1]
                max_c = max(tmp_group, key=lambda value: value[2])[2]
                min_c = min(tmp_group, key=lambda value: value[2])[2]
                factor_a = abs(max_a - min_a)
                factor_b = abs(max_b - min_b)
                factor_c = abs(max_c - min_c)
                factors = [factor_a, factor_b, factor_c]
                factors.sort()
                if (group_size == 1 and factors != [0, 1, 1]) or (group_size == 2 and factors != [0, 2, 2]):
                    self.group = []

        # Добавляем ячейку в группу и уведомляем компонент отрисовки
        self.group.append(key)
        self.pool_painter.set_group(self.group)

    def create_action(self, pos):
        if not self.group:
            return None

        key = self.pool_painter.get_key_at_dot(pos)
        if not key:
            return None

        return self._create_shift_actions(key) or self._create_line_actions(key)

    def _create_shift_actions(self, key):
        """ Метод формирует и возвращает ход сдвига или возвращает None, если этого нельзя сделать """

        # Проверяем, пуста ли ячейка, в которую кликнул пользователь для перемещения группы
        cells = self.pool_painter.cells
        if cells[key]['content']:
            return None

        # Ищем направление движения для ячеек группы (оно должно определяться однозначно, иначе ход невозможен)
        direction = [
            direction for g_key in self.group for direction in range(6) if cells[g_key]['around'][direction] == key
        ]
        if not direction or len(direction) > 1:
            return None
        direction = direction[0]

        # Формируем конечный список ходов, при этом проверяем, чтобы каждая ячейка, в кторую двигается шарик была пуста
        result = []
        for g_key in self.group:
            group_cell = cells[g_key]
            n_key = group_cell['around'][direction]
            if not n_key or cells[n_key]['content']:
                return None
            result.append((g_key, n_key))

        return result

    def _create_line_actions(self, key):
        """ Метод формирует и возвращает линейный ход или возвращает None, если этого нельзя сделать """

        # Если длина цепочки равна 1, то линейный ход невозможен и ход считается ходом сдвига
        if len(self.group) == 1:
            return None

        # Блокируем попытку сдвинуть группой свой шарик
        cells = self.pool_painter.cells
        if cells[key]['content'] == PLAYER_SIDE:
            return None

        # Проверяем, находится ли ячейка, в которую кликнул пользователь на одной линии с группой
        tmp_group = self.group + [key]
        flag_a = all([g_key[0] == tmp_group[0][0] for g_key in tmp_group])
        flag_b = all([g_key[1] == tmp_group[0][1] for g_key in tmp_group])
        flag_c = all([g_key[2] == tmp_group[0][2] for g_key in tmp_group])
        if not (flag_a or flag_b or flag_c):
            return None

        # Проверяем, достижима ли ячейка, выбранная пользователем из ячеек группы. Если да, то фиксируем направление
        direction = [
            direction for g_key in self.group for direction in range(6) if cells[g_key]['around'][direction] == key
        ]
        if not direction:
            return None
        direction = direction[0]

        # Сортируем группу по удалению от выбранной пользователем ячейки
        self.group.sort(key=lambda x: - (abs(x[0] - key[0]) + abs(x[1] - key[1]) + abs(x[2] - key[2])))

        # Создаем сдвиги для ячеек группы
        result = []
        for g_key in self.group:
            group_cell = cells[g_key]
            n_key = group_cell['around'][direction]
            result.append((g_key, n_key))

        # Если группа толкает ячейки противника, то создаем сдвиги и для них
        if cells[key]['content'] == CMP_SIDE:
            s_key = key
            s_cell = cells[key]
            while True:
                n_key = s_cell['around'][direction]
                result.append((s_key, n_key))
                if len(result) > (2 * len(self.group) - 1):
                    return None
                if not n_key:
                    break
                n_cell = cells[n_key]
                if not n_cell['content']:
                    break
                if n_cell['content'] == PLAYER_SIDE:
                    return None

                s_key = n_key
                s_cell = n_cell

        # Реверсируем и возвращаем результат
        result.reverse()
        return result

    def clear(self):
        self.group = []
        self.pool_painter.set_group(self.group)


class Ai:

    def __init__(self, pool):
        self.pool = pool

    def next_action(self):
        import random
        actions = self.pool.create_actions(CMP_SIDE)
        action = random.choice(actions)
        return action


class ScorePane:
    SCORE_RADIUS = 15
    BORDER = 10
    SCORE_MARGIN = 8

    TRANSPARENT_COLOR = (0,) * 3
    SCORE_COLOR = (130,) * 3
    SCORE_BORDER_COLOR = (75,) * 3

    def __init__(self, side, pg, sc):
        self.score_count = 0
        self.side = side
        self.pg = pg
        self.sc = sc

        if side == CMP_SIDE:
            self.y_anchor = self.BORDER
        if side == PLAYER_SIDE:
            self.y_anchor = H - self.BORDER - 2 * self.SCORE_RADIUS
        self.x_anchor = W // 2 - (12 * self.SCORE_RADIUS + 5 * self.SCORE_MARGIN) // 2

        self.surface = pg.Surface((W, H))
        self.surface.set_colorkey(self.TRANSPARENT_COLOR)
        self.surface.fill(self.TRANSPARENT_COLOR)
        self.refresh_flag = True

    def refresh_pane(self, ball_count):
        next_score_count = 14 - ball_count
        if next_score_count > self.score_count:
            self.score_count = next_score_count
            self.refresh_flag = True

    def draw(self):
        if self.refresh_flag:
            self.surface.fill(self.TRANSPARENT_COLOR)

            x_center = self.x_anchor + self.SCORE_RADIUS
            y_center = self.y_anchor + self.SCORE_RADIUS
            for index in range(1, 7):
                if index <= self.score_count:
                    self.pg.draw.circle(self.surface, self.SCORE_COLOR, (x_center, y_center), self.SCORE_RADIUS)

                self.pg.draw.circle(self.surface, self.SCORE_BORDER_COLOR, (x_center, y_center), self.SCORE_RADIUS, 1)
                x_center += (2 * self.SCORE_RADIUS + self.SCORE_MARGIN)

            self.refresh_flag = False

        self.sc.blit(self.surface, (0, 0))


class MsgPane:
    TEXT_COLOR = (255,) * 3

    def __init__(self, pg, sc):
        self.pg = pg
        self.sc = sc
        self.msg = None
        self.back_surface = pg.Surface((W, H))
        self.back_surface.set_alpha(100)
        self.text_surface = None

    def set_msg(self, msg):
        self.msg = msg
        font = self.pg.font.Font(None, 72)
        self.text_surface = font.render(msg, True, self.TEXT_COLOR)

    def draw(self):
        if not self.msg:
            return

        self.sc.blit(self.back_surface, (0, 0))
        self.sc.blit(
            self.text_surface,
            (W // 2 - self.text_surface.get_width() // 2, H // 2 - self.text_surface.get_height() // 2)
        )
