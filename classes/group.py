from settings import PLAYER_SIDE, CMP_SIDE


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
