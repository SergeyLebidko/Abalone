import itertools
from settings import CMP_SIDE, PLAYER_SIDE


class Pool:
    DELTA_KEYS = [(0, 1, 1), (1, 0, 1), (1, -1, 0), (0, -1, -1), (-1, 0, -1), (-1, 1, 0)]
    SHORT_DELTA_KEYS = DELTA_KEYS[:3]

    LINE_PATTERNS = ['**#r', '***##r', '***##e', '***#e', '**#e', '***e', '**e']
    LINE_PATTERNS_SET = set(LINE_PATTERNS)

    OTHER_SIDE_DICT = {CMP_SIDE: PLAYER_SIDE, PLAYER_SIDE: CMP_SIDE}

    APPLY_TYPE = 'apply'
    CANCEL_TYPE = 'cancel'

    MAX_RATE = 1000000000

    def __init__(self):
        self.actions = []
        self.last_action_description = None
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

        # Готовим список паттернов для проверки наличия выталкивающих ходов
        self.drop_patterns = []
        for a, b, c in self.cells.keys():
            if (abs(a) + abs(b) + abs(c)) != 8:
                continue
            for size in [3, 5]:
                for da, db, dc in self.DELTA_KEYS:
                    pattern = [(a + index * da, b + index * db, c + index * dc) for index in range(size)]
                    if all([key in self.cells.keys() for key in pattern]):
                        self.drop_patterns.append(pattern)

    def create_actions(self, side):
        line_actions = self._create_line_actions(side)
        shift_actions = self._create_shift_actions(side)
        return line_actions + shift_actions

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

    def get_rating(self):
        # Первый этап оценки рейтинга - оценка количества шариков
        cmp_count, player_count = self._balls_count()
        if cmp_count < 9:
            return (-1) * self.MAX_RATE
        if player_count < 9:
            return self.MAX_RATE
        cmp_count_rate = (cmp_count ** 2) * 1900
        player_count_rate = (player_count ** 2) * 1900

        # Второй этап оценки рейтинга - оценка близости шариков к центру доски и стороне противника
        cmp_pos_rate = 0
        player_pos_rate = 0
        full_cells = self._get_side_cells()
        for (a, b, c), cell in full_cells.items():
            content = cell['content']
            if content == PLAYER_SIDE:
                player_pos_rate += (8 - abs(a) + abs(b) + abs(c)) * 2
                player_pos_rate += a * 8
            if content == CMP_SIDE:
                cmp_pos_rate += (8 - abs(a) + abs(b) + abs(c)) * 2
                cmp_pos_rate += (-1) * a * 8

        # Третий этап - оценка прикрытий
        cmp_cover_rate = 0
        player_cover_rate = 0
        for (a, b, c), cell in full_cells.items():
            side = cell['content']
            for da, db, dc in self.SHORT_DELTA_KEYS:
                # Проверяем первую соседнюю ячейку
                n_key = a + da, b + db, c + dc
                n_cell = full_cells.get(n_key)
                if n_cell and n_cell['content'] == side:
                    score = 1
                else:
                    continue

                n_key = a + 2 * da, b + 2 * db, c + 2 * dc
                n_cell = full_cells.get(n_key)
                if n_cell and n_cell['content'] == side:
                    score += 2

                if side == CMP_SIDE:
                    cmp_cover_rate += score
                if side == PLAYER_SIDE:
                    player_cover_rate += score

        # Четвертый этап - проверка наличия выталкивающих ходов
        cmp_drop_rate = 0
        player_drop_rate = 0
        for pattern in self.drop_patterns:
            side = self.cells[pattern[0]]['content']
            if not side:
                continue
            other_side = self.OTHER_SIDE_DICT[side]
            if len(pattern) == 3:
                etalon = [side, other_side, other_side]
            else:
                etalon = [side, side, other_side, other_side, other_side]
            for index, key in enumerate(pattern[1:], 1):
                content = self.cells[key]['content']
                if content != etalon[index]:
                    break
            else:
                if side == CMP_SIDE:
                    player_drop_rate += 600
                if side == PLAYER_SIDE:
                    cmp_drop_rate += 600

        cmp_rate = cmp_count_rate + cmp_pos_rate + cmp_cover_rate + cmp_drop_rate
        player_rate = player_count_rate + player_pos_rate + player_cover_rate + player_drop_rate
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
                for a, b, c in cells_side:
                    for direction, (da, db, dc) in enumerate(self.SHORT_DELTA_KEYS):
                        group_keys = [(a, b, c), (a + da, b + db, c + dc)]
                        if count == 3:
                            group_keys.append((a + 2 * da, b + 2 * db, c + 2 * dc))

                        for group_key in group_keys:
                            key_cell = self.cells.get(group_key)
                            if not key_cell or key_cell['content']:
                                break
                        else:
                            groups.append({
                                'directions': [direction, direction + 3],
                                'keys': group_keys
                            })

                # Проверяем каждую группу на возможность сдвига. Если она есть - фиксируем соответствующие операции
                for group in groups:
                    directions = group['directions']
                    keys = group['keys']

                    for direction, (da, db, dc) in enumerate(self.DELTA_KEYS):
                        if direction in directions:
                            continue

                        action = []
                        for a, b, c in keys:
                            na = a + da,
                            nb = b + db
                            nc = c + dc
                            n_cell = self.cells.get((na, nb, nc))
                            if not n_cell or n_cell['content']:
                                break
                            action.append(((a, b, c), (na, nb, nc)))
                        else:
                            result.append(action)

        return result

    def _create_line_actions(self, side):
        cells_side = self._get_side_cells(side)
        other_side = self.OTHER_SIDE_DICT[side]

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

                if pattern in self.LINE_PATTERNS_SET:
                    groups.append((pattern, group_keys))

        # Сортируем группы по важности хода
        groups.sort(key=lambda x: self.LINE_PATTERNS.index(x[0]))

        # Строим итоговый список ходов
        result = []
        for group in groups:
            actions = []
            keys = group[1]
            for index in range(len(keys) - 1, 0, -1):
                actions.append((keys[index - 1], keys[index]))
            result.append(actions)

        return result

    def _get_side_cells(self, side=None):
        if side:
            return {key: cell for key, cell in self.cells.items() if cell['content'] == side}
        else:
            return {key: cell for key, cell in self.cells.items() if cell['content']}
