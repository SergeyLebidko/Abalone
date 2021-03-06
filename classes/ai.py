import random
from settings import CMP_SIDE, PLAYER_SIDE


class Ai:
    DEPTH = 3

    def __init__(self, pool):
        self.pool = pool
        self.count = 0

    def next_action(self):
        actions = self.pool.create_actions(CMP_SIDE)

        # Свой первый ход компьютер выбирает случайным образом
        if len(self.pool.actions) == 1:
            return random.choice(actions)

        # Обнуляем счетчик просмотра позиций
        self.count = 0

        rate_actions = []
        alpha = -self.pool.MAX_RATE
        beta = self.pool.MAX_RATE
        for action in actions:
            rate = self.rate(action, CMP_SIDE, alpha, beta, self.DEPTH)
            if rate > alpha:
                alpha = rate
            rate_actions.append((rate, action))
            # Если какой-то ход дает победу - сразу же останавливаем поиски
            if rate == self.pool.MAX_RATE:
                break

        rate_actions = list(filter(lambda x: x[0] == alpha, rate_actions))
        rate_action = random.choice(rate_actions)

        print('Отсмотрено позиций:', self.count)
        return rate_action[1]

    def rate(self, action, up_side, alpha, beta, d):
        # Если достигнута максимальная глубина перебора
        if d == 0:
            self.pool.apply_action(action)
            rate = self.pool.get_rating()
            self.count += 1
            self.pool.cancel_action()
            return rate

        if up_side == CMP_SIDE:
            self.pool.apply_action(action)
            actions = self.pool.create_actions(PLAYER_SIDE)
            min_rate = self.pool.MAX_RATE * 1000
            for _action in actions:
                rate = self.rate(_action, PLAYER_SIDE, alpha, min_rate, d - 1)
                if rate < min_rate:
                    min_rate = rate
                if not (alpha <= min_rate <= beta):
                    break

            self.pool.cancel_action()
            return min_rate

        if up_side == PLAYER_SIDE:
            self.pool.apply_action(action)
            actions = self.pool.create_actions(CMP_SIDE)
            max_rate = (-1) * self.pool.MAX_RATE * 1000
            for _action in actions:
                rate = self.rate(_action, CMP_SIDE, max_rate, beta, d - 1)
                if rate > max_rate:
                    max_rate = rate
                if not (alpha <= max_rate <= beta):
                    break

            self.pool.cancel_action()
            return max_rate
