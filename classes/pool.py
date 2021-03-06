import itertools
from settings import CMP_SIDE, PLAYER_SIDE


class Pool:
    DELTA_KEYS = [(0, 1, 1), (1, 0, 1), (1, -1, 0), (0, -1, -1), (-1, 0, -1), (-1, 1, 0)]

    LINE_PATTERNS = ['***##r', '**#r', '***##e', '***#e', '**#e', '***e', '**e']

    APPLY_TYPE = 'apply'
    CANCEL_TYPE = 'cancel'

    MIN_RATE = -1000000

    def __init__(self):
        self.actions = []
        self.last_action_description = None
        self.cells = {
            (0, 0, 0): {
                'content': None,
                'around': [None] * 6
            }
        }

        # Списки ходов, доступных комипьютеру и игроку
        self.avl_cmp_actions = []
        self.avl_player_actions = []

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
        if side == CMP_SIDE and self.avl_cmp_actions:
            return self.avl_cmp_actions
        if side == PLAYER_SIDE and self.avl_player_actions:
            return self.avl_player_actions

        avl_actions = self._create_line_actions(side) + self._create_shift_actions(side)
        if side == CMP_SIDE:
            self.avl_cmp_actions = avl_actions
        if side == PLAYER_SIDE:
            self.avl_player_actions = avl_actions

        return avl_actions

    def apply_action(self, action):
        self.actions.append(action)
        self.last_action_description = {
            'type': self.APPLY_TYPE,
            'action': action
        }
        for old_key, next_key in action:
            old_cell = self.cells[old_key]
            side = old_cell['content']
            old_cell['content'] = None
            if not next_key:
                continue

            next_cell = self.cells[next_key]
            next_cell['content'] = side

        # После применения хода - сбрасываем списки доступных ходов, так как они больше не актуальны
        self.avl_player_actions = []
        self.avl_cmp_actions = []

    def cancel_action(self):
        action = self.actions.pop()
        self.last_action_description = {
            'type': self.CANCEL_TYPE,
            'action': action
        }
        for index, (old_key, next_key) in enumerate(reversed(action)):
            if index == 0:
                other_side = {CMP_SIDE: PLAYER_SIDE, PLAYER_SIDE: CMP_SIDE}[self.cells[next_key]['content']]

            if next_key:
                side = self.cells[next_key]['content']
                self.cells[next_key]['content'] = None
                self.cells[old_key]['content'] = side
            else:
                self.cells[old_key]['content'] = other_side

        # После отката хода сбрасываем списки доступных ходов, так как они больше не актуальны
        self.avl_player_actions = []
        self.avl_cmp_actions = []

    def get_rating(self):
        # Первый этап оценки рейтинга - оценка количества шариков
        cmp_count, player_count = self._balls_count()
        cmp_rate = cmp_count ** 2 if cmp_count > 8 else self.MIN_RATE
        player_rate = player_count ** 2 if player_count > 8 else self.MIN_RATE

        total_rate = cmp_rate - player_rate
        return total_rate

    def get_last_action_description(self):
        if self.last_action_description:
            return self.last_action_description
        return None

    def get_winner_side(self):
        cmp_count, player_count = self._balls_count()
        if cmp_count < 9:
            return PLAYER_SIDE
        if player_count < 9:
            return CMP_SIDE
        return None

    @property
    def cmp_balls_count(self):
        count, _ = self._balls_count()
        return count

    @property
    def player_balls_count(self):
        _, count = self._balls_count()
        return count

    def _balls_count(self):
        cmp_count = 0
        player_count = 0
        for _, cell in self.cells.items():
            if cell['content'] == CMP_SIDE:
                cmp_count += 1
            if cell['content'] == PLAYER_SIDE:
                player_count += 1

        return cmp_count, player_count

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