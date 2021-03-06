import random
from settings import CMP_SIDE, PLAYER_SIDE, LOW_DEPTH, MID_DEPTH, DEEP_DEPTH, DEBUG
from datetime import datetime


class Ai:
    TOTAL_VIEW_LIMIT = 500000
    CURRENT_COUNT_LIMIT = 200

    def __init__(self, pool):
        self.pool = pool
        self.total_view_position_count = 0
        self.current_count = 0

    def action_generator(self):
        actions = self.pool.create_actions(CMP_SIDE)

        # Свой первый ход компьютер выбирает случайным образом
        if len(self.pool.actions) == 1:
            yield random.choice(actions)

        # Обнуляем счетчик просмотра позиций и фиксируем время
        self.total_view_position_count = 0
        self.current_count = 0
        time_start = datetime.now()

        # В зависимости от количества ходов в партии выбираем глубину просчета
        depth = DEEP_DEPTH
        actions_count = len(self.pool.actions)
        if actions_count <= 5:
            depth = LOW_DEPTH
        if 6 <= actions_count <= 17:
            depth = MID_DEPTH

        rate_actions = []
        alpha = -self.pool.MAX_RATE
        beta = self.pool.MAX_RATE
        for action in actions:
            rate_generator = self.rate(action, CMP_SIDE, alpha, beta, depth)
            while True:
                rate = next(rate_generator)
                if rate is None:
                    yield None
                    continue
                break
            if rate > alpha:
                alpha = rate
            rate_actions.append((rate, action))
            # Если какой-то ход дает победу - сразу же останавливаем поиски
            if rate == self.pool.MAX_RATE:
                break

        rate_actions = list(filter(lambda x: x[0] == alpha, rate_actions))
        rate_action = random.choice(rate_actions)

        # Выводим статистику работы
        if DEBUG:
            time_end = datetime.now()
            time_passed = time_end - time_start
            total_mcs = time_passed.microseconds + time_passed.seconds * 1000000
            msg = 'Просмотрено позиций: {count:>6} время: {time_passed:>15} мкс/позицию: {mcs}'.format(
                count=self.total_view_position_count,
                time_passed=str(time_passed),
                mcs=round(total_mcs / self.total_view_position_count, 2)
            )
            print(msg)

        yield rate_action[1]

    def rate(self, action, up_side, alpha, beta, d):
        # Если достигнута максимальная глубина перебора
        if d == 0:
            self.pool.apply_action(action)
            rate = self.pool.get_rating()
            self.total_view_position_count += 1
            self.current_count += 1
            self.pool.cancel_action()
            yield rate

        if up_side == CMP_SIDE:
            self.pool.apply_action(action)

            # Если в результате применения хода победил компьютер, то дальнейший просмотр ходов не имеет смысла
            # В такой ситуации сразу же присваиваем ходу наивысший рейтинг и возвращаем его
            winner = self.pool.get_winner_side()
            if winner == CMP_SIDE:
                self.total_view_position_count += 1
                self.current_count += 1
                self.pool.cancel_action()
                yield self.pool.MAX_RATE

            actions = self.pool.create_actions(PLAYER_SIDE)
            min_rate = self.pool.MAX_RATE * 1000
            for _action in actions:
                rate_generator = self.rate(_action, PLAYER_SIDE, alpha, min_rate, d - 1)
                rate = None
                while rate is None:
                    rate = next(rate_generator)
                    if rate is None:
                        yield None
                if self.current_count == self.CURRENT_COUNT_LIMIT:
                    yield None
                    self.current_count = 0

                if rate < min_rate:
                    min_rate = rate
                if not (alpha <= min_rate <= beta) or self.total_view_position_count > self.TOTAL_VIEW_LIMIT:
                    break

            self.pool.cancel_action()
            yield min_rate

        if up_side == PLAYER_SIDE:
            self.pool.apply_action(action)

            # Если в результате применения хода победил игрок, то дальнейший просмотр ходов не имеет смысла
            # В такой ситуации сразу же присваиваем ходу самый низкий рейтинг и возвращаем его
            winner = self.pool.get_winner_side()
            if winner == PLAYER_SIDE:
                self.total_view_position_count += 1
                self.current_count += 1
                self.pool.cancel_action()
                yield (-1) * self.pool.MAX_RATE

            actions = self.pool.create_actions(CMP_SIDE)
            max_rate = (-1) * self.pool.MAX_RATE * 1000
            for _action in actions:
                rate_generator = self.rate(_action, CMP_SIDE, max_rate, beta, d - 1)
                rate = None
                while rate is None:
                    rate = next(rate_generator)
                    if rate is None:
                        yield None
                if self.current_count == self.CURRENT_COUNT_LIMIT:
                    yield None
                    self.current_count = 0

                if rate > max_rate:
                    max_rate = rate
                if not (alpha <= max_rate <= beta) or self.total_view_position_count > self.TOTAL_VIEW_LIMIT:
                    break

            self.pool.cancel_action()
            yield max_rate
