import asyncio
import sys

import pygame
from presentation import ui
from presentation.config import FPS, SCREEN_H, SCREEN_W, SPRITE_SCALE, WINDOW_TITLE
from presentation.fonts import Fonts
from presentation.sprites import SpriteStore
from presentation.view import MAIN_MENU_OPTIONS, QUIT_OPTIONS, Game

IS_WEB = sys.platform == "emscripten"


def _fit_canvas_to_browser():
    """Вписывает канвас в окно браузера с сохранением пропорций.

    pygbag рисует канвас фиксированного размера; масштабируем его CSS-стилями,
    image-rendering: pixelated сохраняет чёткость пиксель-арта.
    """
    import platform as web

    try:
        win_w = int(web.window.innerWidth)
        win_h = int(web.window.innerHeight)
        scale = min(win_w / SCREEN_W, win_h / SCREEN_H)
        canvas = web.window.canvas
        canvas.style.width = f"{int(SCREEN_W * scale)}px"
        canvas.style.height = f"{int(SCREEN_H * scale)}px"
        canvas.style.imageRendering = "pixelated"
    except Exception:
        pass


async def main():
    """Точка входа. Асинхронный цикл — требование pygbag для WASM-сборки."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    fonts = Fonts()
    sprites = SpriteStore(SPRITE_SCALE)
    game = Game()

    frame = 0
    while not game.should_quit:
        if IS_WEB and frame % FPS == 0:  # раз в секунду, подхватывает ресайз окна
            _fit_canvas_to_browser()
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.should_quit = True
            else:
                game.handle_event(event)

        if game.state == "MAIN_MENU":
            ui.draw_main_menu(screen, fonts, sprites, MAIN_MENU_OPTIONS, game.menu_selected, game.menu_message)
        elif game.state == "NAME_ENTRY":
            ui.draw_name_entry(screen, fonts, sprites, game.name_input)
        elif game.state == "PLAYING":
            ui.draw_playing(screen, fonts, sprites, game.session)
        elif game.state == "ITEM_MENU":
            ui.draw_playing(screen, fonts, sprites, game.session)
            ui.draw_item_menu_overlay(screen, fonts, game.item_menu_items, game.item_menu_allow_zero)
        elif game.state == "QUIT_DIALOG":
            ui.draw_playing(screen, fonts, sprites, game.session)
            ui.draw_quit_dialog(screen, fonts, QUIT_OPTIONS, game.quit_selected)
        elif game.state == "LEADERBOARD":
            ui.draw_leaderboard_screen(screen, fonts, sprites, game.leaderboard_records, game.leaderboard_source)
        elif game.state == "DEATH":
            ui.draw_end_screen(screen, fonts, sprites, "YOU DIED", game.submit_status)
        elif game.state == "WIN":
            ui.draw_end_screen(screen, fonts, sprites, "YOU WIN!", game.submit_status)

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
