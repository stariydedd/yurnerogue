from domain.consts import SYM_CORRIDOR, SYM_DOOR, SYM_EMPTY, SYM_EXIT, SYM_ROOM_FLOOR, SYM_WALL
from domain.domain import OpponentType

BLACK = (0, 0, 0)
WHITE = (225, 225, 225)
GOLD = (212, 175, 55)
HILITE = (255, 215, 0)
PANEL_BG = (18, 18, 18)
MSG_COLOR = (255, 200, 120)
HINT_COLOR = (140, 140, 140)

TILE_COLORS = {
    SYM_WALL: (70, 70, 75),
    SYM_ROOM_FLOOR: (55, 50, 45),
    SYM_CORRIDOR: (40, 38, 35),
    SYM_DOOR: (110, 80, 40),
    SYM_EXIT: (40, 70, 40),
    SYM_EMPTY: BLACK,
}

OPPONENT_COLORS = {
    OpponentType.ZOMBIE: (60, 200, 60),
    OpponentType.VAMPIRE: (220, 60, 60),
    OpponentType.GHOST: (230, 230, 230),
    OpponentType.OGRE: (230, 200, 60),
    OpponentType.SNAKE: (230, 230, 230),
}
