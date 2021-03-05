import random
import pygame as pg
from settings import W, H, TITLE, COLOR_LABEL_1, COLOR_LABEL_2, CMP_SIDE, PLAYER_SIDE, CMP_MODE, PLAYER_MODE, END_MODE
from classes import Background, Pool, PoolPainter, Group, ScorePane, Ai, MsgPane


def main(cmp_color_label, player_color_label):
    # Инициализируем окно
    pg.init()
    sc = pg.display.set_mode((W, H))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()

    background = Background(pg, sc)
    pool = Pool()
    pool_painter = PoolPainter(pg, pool, sc, cmp_color_label, player_color_label)
    group = Group(pool_painter)
    cmp_score_pane = ScorePane(CMP_SIDE, pg, sc)
    player_score_pane = ScorePane(PLAYER_SIDE, pg, sc)
    mgs_pane = MsgPane(pg, sc)
    ai = Ai(pool)

    mode = PLAYER_MODE

    def apply_action(act, next_mode, group_clear):
        if not action:
            return

        nonlocal mode
        pool.apply_action(act)
        cmp_score_pane.refresh_pane(pool.player_balls_count)
        player_score_pane.refresh_pane(pool.cmp_balls_count)
        if group_clear:
            group.clear()
        pool_painter.refresh_pool()
        winner = pool.get_winner_side()
        if winner:
            mgs_pane.set_msg({PLAYER_SIDE: 'Вы победили!', CMP_SIDE: 'Вы проиграли...'}[winner])
            mode = END_MODE
        else:
            mode = next_mode

    def cancel_action():
        if not pool.actions:
            return

        nonlocal mode
        pool.cancel_action()
        cmp_score_pane.refresh_pane(pool.player_balls_count)
        player_score_pane.refresh_pane(pool.cmp_balls_count)
        group.clear()
        pool_painter.refresh_pool()
        mgs_pane.clear_msg()
        mode = PLAYER_MODE

    while True:

        # Секция расчета и применения следующего хода
        if not pool_painter.has_animate and mode == CMP_MODE:
            action = ai.next_action()
            apply_action(action, PLAYER_MODE, False)

        # Секция взаимодействия с пользователем
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            if event.type == pg.MOUSEMOTION:
                pool_painter.set_cursor_pos(event.pos)

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    cancel_action()

            # Блокируем возможность кнопок мышки до завершения анимаций и операций по расчету хода
            if pool_painter.has_animate or mode != PLAYER_MODE:
                continue

            if event.type == pg.MOUSEBUTTONDOWN and event.button == pg.BUTTON_LEFT:
                group.click(event.pos)

            if event.type == pg.MOUSEBUTTONDOWN and event.button == pg.BUTTON_RIGHT:
                action = group.create_action(event.pos)
                apply_action(action, CMP_MODE, True)

        # Секция команд отрисовки
        background.draw()
        cmp_score_pane.draw()
        player_score_pane.draw()
        pool_painter.draw()
        mgs_pane.draw()
        pg.display.update()
        clock.tick(30)


if __name__ == '__main__':
    color_labels = [COLOR_LABEL_1, COLOR_LABEL_2]
    random.shuffle(color_labels)
    main(*color_labels)
