from settings import W, H, CMP_SIDE, PLAYER_SIDE


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
        if next_score_count != self.score_count:
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
