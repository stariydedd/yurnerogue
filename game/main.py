import asyncio

import pygame
from presentation import config, ui, webenv
from presentation.config import FPS, SPRITE_SCALE, WINDOW_TITLE
from presentation.fonts import Fonts
from presentation.sprites import SpriteStore
from presentation.touch import TouchControls
from presentation.view import MAIN_MENU_OPTIONS, QUIT_OPTIONS, Game


async def main():
    """Точка входа. Асинхронный цикл — требование pygbag для WASM-сборки.

    Растягивание канваса на весь экран сделано в web/rogue.tmpl через CSS
    (правило #canvas с !important перебивает инлайн-стили pygbag).
    На тач-устройствах включается портретная раскладка «консоли»: карта
    сверху, панель экранных кнопок снизу; раскладка выбирается до создания
    окна, потому что меняет размеры внутренней поверхности."""
    touch_mode = webenv.is_touch_device()
    if touch_mode:
        config.apply_touch_layout(*webenv.window_size())

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    fonts = Fonts()
    sprites = SpriteStore(SPRITE_SCALE)
    game = Game(touch_mode=touch_mode)
    touch = TouchControls(game) if touch_mode else None

    while not game.should_quit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.should_quit = True
                continue
            # Тач-события переводятся в клавишные; None = не событие указателя.
            routed = touch.translate(event) if touch else None
            if routed is None:
                game.handle_event(event)
            else:
                for key_event in routed:
                    game.handle_event(key_event)
        if touch:
            for key_event in touch.tick(pygame.time.get_ticks()):
                game.handle_event(key_event)

        if game.state == "MAIN_MENU":
            ui.draw_main_menu(screen, fonts, sprites, MAIN_MENU_OPTIONS, game.menu_selected, game.menu_message)
        elif game.state == "NAME_ENTRY":
            ui.draw_name_entry(screen, fonts, sprites, game.name_input)
        elif game.state == "PLAYING":
            ui.draw_playing(screen, fonts, sprites, game.session)
        elif game.state == "ITEM_MENU":
            ui.draw_playing(screen, fonts, sprites, game.session)
            ui.draw_item_menu_overlay(screen, fonts, game.item_menu_items,
                                      game.item_menu_allow_zero, game.item_menu_selected)
        elif game.state == "QUIT_DIALOG":
            ui.draw_playing(screen, fonts, sprites, game.session)
            ui.draw_quit_dialog(screen, fonts, QUIT_OPTIONS, game.quit_selected)
        elif game.state == "LEADERBOARD":
            ui.draw_leaderboard_screen(screen, fonts, sprites, game.leaderboard_records, game.leaderboard_source)
        elif game.state == "HELP":
            ui.draw_help(screen, fonts, sprites)
        elif game.state == "DEATH":
            ui.draw_end_screen(screen, fonts, sprites, "YOU DIED", game.submit_status)
        elif game.state == "WIN":
            ui.draw_end_screen(screen, fonts, sprites, "YOU WIN!", game.submit_status)

        if touch:
            touch.draw(screen, fonts, sprites)

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
