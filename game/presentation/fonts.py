from pathlib import Path

import pygame

FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "PressStart2P.ttf"


class Fonts:
    """Шрифты игры. Пиксельный Press Start 2P лежит в ассетах, поэтому выглядит
    одинаково на десктопе и в браузере (SysFont в WASM недоступен)."""

    def __init__(self):
        path = str(FONT_PATH)
        self.title = pygame.font.Font(path, 40)
        self.menu = pygame.font.Font(path, 18)
        self.ui = pygame.font.Font(path, 14)
        self.compact = pygame.font.Font(path, 12)  # длинные строки на узком экране
        self.small = pygame.font.Font(path, 10)
