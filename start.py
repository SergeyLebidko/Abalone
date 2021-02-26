import random
import pygame as pg
from settings import W, H, TITLE, COLOR_LABEL_1, COLOR_LABEL_2
from classes import Background, Pool, PoolPainter


def main(cmp_color_label, player_color_label):
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    background = Background(pg)
    pool = Pool()
    pool_painter = PoolPainter(pg, pool, sc, cmp_color_label, player_color_label)

    while True:

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        background.draw(sc)
        pool_painter.draw()
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    color_labels = [COLOR_LABEL_1, COLOR_LABEL_2]
    random.shuffle(color_labels)
    main(*color_labels)
