import pygame as pg

W, H = 1200, 900
TITLE = 'Abalone'
BACKGROUND_COLOR = (240, 240, 240)


def main():
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    while True:

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        sc.fill(BACKGROUND_COLOR)
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    main()
