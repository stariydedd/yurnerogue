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
CONTROLS_H = 0  # высота панели тач-кнопок; 0 = десктопная раскладка
TOUCH_MODE = False
SCREEN_W = GRID_W
SCREEN_H = GRID_H + PANEL_H
FPS = 30
WINDOW_TITLE = "YurneROGUE"


def apply_touch_layout(window_w, window_h):
    """Переключает раскладку в портретную «консоль»: карта, статус, тач-кнопки.

    Внутренняя ширина фиксированная, высота повторяет пропорции окна телефона
    (канвас растянут CSS на весь экран, поэтому совпадение пропорций избавляет
    от искажения). ui.py и touch.py читают эти значения через атрибуты модуля.
    """
    global TOUCH_MODE, SCREEN_W, SCREEN_H, PANEL_H, CONTROLS_H
    global VIEW_COLS, VIEW_ROWS, GRID_W, GRID_H
    TOUCH_MODE = True
    SCREEN_W = 480
    ratio = window_h / max(1, window_w)
    SCREEN_H = int(SCREEN_W * min(max(ratio, 1.6), 2.3))
    # Панель статуса выше десктопной: оружию — своя строка, сообщению — две.
    PANEL_H = 164
    CONTROLS_H = max(264, int(SCREEN_H * 0.30))
    GRID_W = SCREEN_W
    GRID_H = SCREEN_H - PANEL_H - CONTROLS_H
    VIEW_COLS = -(-GRID_W // TILE_SIZE)
    VIEW_ROWS = -(-GRID_H // TILE_SIZE)

# Скорость смены кадров idle-анимаций, мс на кадр.
ANIM_FRAME_MS = 160
