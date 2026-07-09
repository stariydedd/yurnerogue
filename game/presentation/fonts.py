import pygame


class Fonts:
    """Держит все шрифты игры, создаётся один раз после pygame.font.init()."""

    def __init__(self):
        self.ui = pygame.font.SysFont("consolas", 20)
        self.small = pygame.font.SysFont("consolas", 15)
        self.title = pygame.font.SysFont("consolas", 48, bold=True)
