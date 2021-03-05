from settings import CMP_SIDE


class Ai:

    def __init__(self, pool):
        self.pool = pool

    def next_action(self):
        import random
        actions = self.pool.create_actions(CMP_SIDE)
        rate_actions = []
        for action in actions:
            rate = self.rate(action)
            rate_actions.append((rate, action))

        max_rate = max(rate_actions, key=lambda x: x[0])[0]
        rate_actions = list(filter(lambda x: x[0] == max_rate, rate_actions))

        rate_action = random.choice(rate_actions)
        return rate_action[1]

    def rate(self, action):
        self.pool.apply_action(action)
        rate = self.pool.get_rating()
        self.pool.cancel_action()
        return rate
