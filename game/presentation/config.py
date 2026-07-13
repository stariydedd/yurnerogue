from domain.consts import COLS, ROWS

# Исходные спрайты 16px, множитель 2 -> тайл 32px.
SPRITE_SCALE = 2
TILE_SIZE = 16 * SPRITE_SCALE

# Видимая область (камера следует за игроком), в тайлах.
VIEW_COLS = 40
VIEW_ROWS = 22
GRID_W = VIEW_COLS * TILE_SIZE
GRID_H = VIEW_ROWS * TILE_SIZE

# Полный размер карты уровня в пикселях.
MAP_W = COLS * TILE_SIZE
MAP_H = ROWS * TILE_SIZE

PANEL_H = 96
SCREEN_W = GRID_W
SCREEN_H = GRID_H + PANEL_H
FPS = 30
WINDOW_TITLE = "YurneROGUE"

# Скорость смены кадров idle-анимаций, мс на кадр.
ANIM_FRAME_MS = 160
