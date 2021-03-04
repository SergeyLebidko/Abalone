import random
import pygame as pg
from settings import W, H, TITLE, COLOR_LABEL_1, COLOR_LABEL_2, CMP_SIDE, PLAYER_SIDE
from classes import Background, Pool, PoolPainter, Group, ScorePane


def main(cmp_color_label, player_color_label):
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    background = Background(pg)
    pool = Pool()
    pool_painter = PoolPainter(pg, pool, sc, cmp_color_label, player_color_label)
    group = Group(pool_painter)
    cmp_score_pane = ScorePane(CMP_SIDE, pg, sc)
    player_score_pane = ScorePane(PLAYER_SIDE, pg, sc)

    while True:

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            if event.type == pg.MOUSEMOTION:
                pool_painter.set_cursor_pos(event.pos)

            # Блокируем возможность кликов мышкой до завершения анимаций
            if pool_painter.has_animate:
                continue

            if event.type == pg.MOUSEBUTTONDOWN and event.button == pg.BUTTON_LEFT:
                group.click(event.pos)

            if event.type == pg.MOUSEBUTTONDOWN and event.button == pg.BUTTON_RIGHT:
                action = group.create_action(event.pos)
                if action:
                    pool.apply_action(action)
                    cmp_score_pane.refresh_pane(pool.player_balls_count)
                    player_score_pane.refresh_pane(pool.cmp_balls_count)
                    group.clear()
                    pool_painter.refresh_pool()

        background.draw(sc)
        cmp_score_pane.draw()
        player_score_pane.draw()
        pool_painter.draw()
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    color_labels = [COLOR_LABEL_1, COLOR_LABEL_2]
    random.shuffle(color_labels)
    main(*color_labels)
