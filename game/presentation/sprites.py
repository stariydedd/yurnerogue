from pathlib import Path

import pygame

ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Пиксели исходного тайлсета (16px) масштабируются в TILE_SIZE целым множителем,
# чтобы пиксель-арт оставался чётким.
SOURCE_TILE = 16


class SpriteStore:
    """Загружает атлас 0x72 DungeonTilesetII и раздаёт кадры спрайтов по имени.

    Формат tileset_coords.txt: `name x y w h frames` — кадры анимации лежат
    в атласе горизонтально с шагом w.
    """

    def __init__(self, scale):
        self.scale = scale
        sheet = pygame.image.load(str(ASSETS_DIR / "tileset.png")).convert_alpha()
        self.frames = {}
        for line in (ASSETS_DIR / "tileset_coords.txt").read_text().splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            name = parts[0]
            x, y, w, h, count = map(int, parts[1:6])
            frames = []
            for i in range(count):
                rect = pygame.Rect(x + i * w, y, w, h)
                if rect.right > sheet.get_width() or rect.bottom > sheet.get_height():
                    continue
                frame = sheet.subsurface(rect)
                frame = pygame.transform.scale(frame, (w * scale, h * scale))
                frames.append(frame)
            if frames:
                self.frames[name] = frames

    def frame(self, name, tick=0):
        """Возвращает кадр анимации по имени; tick перебирает кадры по кругу."""
        frames = self.frames[name]
        return frames[tick % len(frames)]

    def has(self, name):
        return name in self.frames
