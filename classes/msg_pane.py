from settings import W, H


class MsgPane:
    TEXT_COLOR = (255,) * 3

    def __init__(self, pg, sc):
        self.pg = pg
        self.sc = sc
        self.msg = None
        self.back_surface = pg.Surface((W, H))
        self.back_surface.set_alpha(100)
        self.text_surface = None

    def set_msg(self, msg):
        self.msg = msg
        font = self.pg.font.Font(None, 72)
        self.text_surface = font.render(msg, True, self.TEXT_COLOR)

    def clear_msg(self):
        self.msg = None

    def draw(self):
        if not self.msg:
            return

        self.sc.blit(self.back_surface, (0, 0))
        self.sc.blit(
            self.text_surface,
            (W // 2 - self.text_surface.get_width() // 2, H // 2 - self.text_surface.get_height() // 2)
        )
