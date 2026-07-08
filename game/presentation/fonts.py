import pygame

from presentation.config import TILE_SIZE


class Fonts:
    """Держит все шрифты игры, создаётся один раз после pygame.font.init()."""

    def __init__(self):
        self.glyph = pygame.font.SysFont("consolas", TILE_SIZE + 2, bold=True)
        self.ui = pygame.font.SysFont("consolas", 20)
        self.title = pygame.font.SysFont("consolas", 48, bold=True)
