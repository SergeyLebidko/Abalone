import pygame as pg
from settings import W, H, TITLE, BACKGROUND_COLOR
from classes import Pool


def main():
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    pool = Pool(pg)

    while True:

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        sc.fill(BACKGROUND_COLOR)
        pool.draw(sc)
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    main()
