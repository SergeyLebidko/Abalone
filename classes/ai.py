import random
from settings import CMP_SIDE, PLAYER_SIDE


class Ai:
    DEPTH = 2

    def __init__(self, pool):
        self.pool = pool

    def next_action(self):
        self.count = 0
        actions = self.pool.create_actions(CMP_SIDE)
        rate_actions = []
        alpha = self.pool.MIN_RATE * 1000
        beta = self.pool.MIN_RATE * (-1000)
        for action in actions:
            rate = self.rate(action, CMP_SIDE, alpha, beta, self.DEPTH)
            if rate > alpha:
                alpha = rate
            rate_actions.append((rate, action))

        rate_actions = list(filter(lambda x: x[0] == alpha, rate_actions))

        rate_action = random.choice(rate_actions)
        return rate_action[1]

    def rate(self, action, up_side, alpha, beta, d):
        # Если достигнута максимальная глубина перебора
        if d == 0:
            self.pool.apply_action(action)
            rate = self.pool.get_rating()
            self.pool.cancel_action()
            return rate

        # Если на вышележащем уровне оцениваются ходы компьютера (из оценок ищется максимальная)
        if up_side == CMP_SIDE:
            self.pool.apply_action(action)
            actions = self.pool.create_actions(PLAYER_SIDE)
            min_rate = beta
            for _action in actions:
                rate = self.rate(_action, PLAYER_SIDE, alpha, min_rate, d - 1)
                if not (alpha <= rate <= beta):
                    break
                if rate < min_rate:
                    min_rate = rate

        # Если на вышележащем уровне оцениваются ходы игрока (из оценок выбирается минимальная)
        if up_side == PLAYER_SIDE:
            self.pool.apply_action(action)
            actions = self.pool.create_actions(CMP_SIDE)
            max_rate = alpha
            for _action in actions:
                rate = self.rate(_action, CMP_SIDE, max_rate, beta, d - 1)
                if not (alpha <= rate <= beta):
                    break
                if rate > max_rate:
                    max_rate = rate

        self.pool.cancel_action()
        return rate
