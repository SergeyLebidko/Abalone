from settings import CMP_SIDE


class Ai:

    def __init__(self, pool):
        self.pool = pool

    def next_action(self):
        import random
        actions = self.pool.create_actions(CMP_SIDE)
        action = random.choice(actions)
        return action
