import random
from settings import CMP_SIDE, PLAYER_SIDE


class Ai:
    DEPTH = 2

    def __init__(self, pool):
        self.pool = pool
        self.count = 0

    def next_action(self):
        actions = self.pool.create_actions(CMP_SIDE)

        # Свой первый ход компьютер выбирает случайным образом
        if len(self.pool.actions) == 1:
            return random.choice(actions)

        self.count = 0

        rate_actions = []
        for action in actions:
            rate = self.rate(action, CMP_SIDE, self.DEPTH)
            rate_actions.append((rate, action))

        print('Изначально доступно ходов:', len(rate_actions))
        print('Отсмотрено позиций:', self.count)

        max_rate = max(rate_actions, key=lambda x: x[0])[0]

        print('Максимальный рейтинг среди ходов:', max_rate)

        rate_actions = list(filter(lambda x: x[0] == max_rate, rate_actions))

        print('Ходов с максимальным рейтингом:', len(rate_actions))
        for e in rate_actions:
            print(e)
        print()

        rate_action = random.choice(rate_actions)

        return rate_action[1]

    def rate(self, action, up_side, d):
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
                rate = self.rate(_action, PLAYER_SIDE, d - 1)
                if rate < min_rate:
                    min_rate = rate

            self.pool.cancel_action()
            return min_rate

        if up_side == PLAYER_SIDE:
            self.pool.apply_action(action)
            actions = self.pool.create_actions(CMP_SIDE)
            max_rate = (-1) * self.pool.MAX_RATE * 1000
            for _action in actions:
                rate = self.rate(_action, CMP_SIDE, d - 1)
                if rate > max_rate:
                    max_rate = rate

            self.pool.cancel_action()
            return max_rate
