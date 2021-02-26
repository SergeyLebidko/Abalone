import pygame as pg
from settings import W, H, TITLE
from classes import Pool, Background, Ball


def main():
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    background = Background(pg)
    pool = Pool(pg)

    while True:

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        background.draw(sc)
        pool.draw(sc)
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    main()
