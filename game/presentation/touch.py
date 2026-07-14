"""Экранные тач-кнопки в стиле ретро-консоли (портретная раскладка).

Слева крестовина (в центре — бег), справа ромб из четырёх кнопок предметов,
внизу MENU и SELECT (в игре — HELP, в списке предметов — USE).
Касания транслируются в обычные KEYDOWN-события, которые уже понимает конечный
автомат Game.handle_event, — игровая логика о сенсорном вводе не знает.
"""
import math
from pathlib import Path

import pygame

from presentation import config as cfg
from presentation.colors import HILITE, WHITE

# Автоповтор зажатой крестовины, мс: первый повтор после задержки, дальше чаще.
REPEAT_DELAY = 260
REPEAT_INTERVAL = 150

DPAD_KEYS = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
}

# Ромб как на геймпаде: (контрол, клавиша, роль спрайта на кнопке).
ITEM_BUTTONS = {
    "weapon": (pygame.K_h, "sword"),   # верх
    "food": (pygame.K_j, "food"),      # лево
    "elixir": (pygame.K_k, "elixir"),  # право
    "scroll": (pygame.K_e, "scroll"),  # низ
}

# Состояния, где кнопка MENU означает «отмена», а не «выход в меню».
_ESCAPE_STATES = ("ITEM_MENU", "QUIT_DIALOG", "NAME_ENTRY")

_PANEL_BG = (18, 18, 20)
_BTN_BASE = (54, 54, 60)
_BTN_PRESSED = (104, 104, 116)
_BTN_EDGE = (10, 10, 12)
_ARROW = (150, 150, 160)


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0)


class TouchControls:
    """Раскладка, хит-тест и отрисовка тач-кнопок.

    translate() возвращает None для не-указательных событий (их обрабатывает
    игра как обычно) и список синтезированных KEYDOWN для касаний.
    tick() генерирует автоповтор зажатой крестовины.
    """

    def __init__(self, game):
        self.game = game
        self._fingers = {}  # id указателя -> имя контрола
        self._repeat = None  # (имя dpad-контрола, время следующего повтора)
        self._build_layout()

    def _build_layout(self):
        y0 = cfg.GRID_H + cfg.PANEL_H
        ch = cfg.CONTROLS_H
        self.panel_rect = pygame.Rect(0, y0, cfg.SCREEN_W, ch)

        cell = 52
        cx, cy = 110, y0 + int(ch * 0.40)
        self.dpad_center = (cx, cy)
        self.dpad_rects = {
            "up": pygame.Rect(cx - cell // 2, cy - cell // 2 - cell, cell, cell),
            "down": pygame.Rect(cx - cell // 2, cy + cell // 2, cell, cell),
            "left": pygame.Rect(cx - cell // 2 - cell, cy - cell // 2, cell, cell),
            "right": pygame.Rect(cx + cell // 2, cy - cell // 2, cell, cell),
        }
        self.dpad_hub = pygame.Rect(cx - cell // 2, cy - cell // 2, cell, cell)

        self.button_radius = 34
        bx, by = cfg.SCREEN_W - 110, cy
        off = 56
        self.button_centers = {
            "weapon": (bx, by - off),
            "food": (bx - off, by),
            "elixir": (bx + off, by),
            "scroll": (bx, by + off),
        }

        pill_w, pill_h = 96, 36
        py = y0 + ch - 52
        self.pill_rects = {
            "menu": pygame.Rect(cfg.SCREEN_W // 2 - 8 - pill_w, py - pill_h // 2, pill_w, pill_h),
            "select": pygame.Rect(cfg.SCREEN_W // 2 + 8, py - pill_h // 2, pill_w, pill_h),
        }

    # --- хит-тест и трансляция событий ---

    def _control_at(self, pos):
        for name, rect in self.dpad_rects.items():
            if rect.inflate(12, 12).collidepoint(pos):
                return name
        if self.dpad_hub.collidepoint(pos):
            return "run"
        for name, (bx, by) in self.button_centers.items():
            if math.hypot(pos[0] - bx, pos[1] - by) <= self.button_radius + 8:
                return name
        for name, rect in self.pill_rects.items():
            if rect.inflate(12, 12).collidepoint(pos):
                return name
        return None

    def _key_for(self, control):
        if control in DPAD_KEYS:
            return DPAD_KEYS[control]
        if control in ITEM_BUTTONS:
            return ITEM_BUTTONS[control][0]
        if control == "run":
            return pygame.K_f
        if control == "select":
            # В игре Enter не нужен — кнопка превращается в HELP (F1).
            return pygame.K_F1 if self.game.state == "PLAYING" else pygame.K_RETURN
        # MENU контекстная: в диалогах — отмена, иначе — выход в меню/пропуск.
        return pygame.K_ESCAPE if self.game.state in _ESCAPE_STATES else pygame.K_q

    def translate(self, event, now=None):
        """Переводит событие указателя в KEYDOWN-события; None = не указатель."""
        if now is None:
            now = pygame.time.get_ticks()
        if event.type == pygame.FINGERDOWN:
            # В справке панель кнопок скрыта — выход по тапу в любом месте.
            if self.game.state == "HELP":
                return [_key_event(pygame.K_SPACE)]
            pos = (event.x * cfg.SCREEN_W, event.y * cfg.SCREEN_H)
            return self._press(("finger", event.finger_id), pos, now)
        if event.type == pygame.FINGERUP:
            self._release(("finger", event.finger_id))
            return []
        if event.type == pygame.FINGERMOTION:
            pos = (event.x * cfg.SCREEN_W, event.y * cfg.SCREEN_H)
            return self._drag(("finger", event.finger_id), pos, now)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            # Синтезированные из тача мышиные события пропускаем — иначе дубль.
            if getattr(event, "touch", False) or event.button != 1:
                return []
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game.state == "HELP":
                    return [_key_event(pygame.K_SPACE)]
                return self._press(("mouse", 0), event.pos, now)
            self._release(("mouse", 0))
            return []
        if event.type == pygame.MOUSEMOTION:
            return []
        return None

    def _press(self, pointer, pos, now):
        control = self._control_at(pos)
        if control is None:
            return []
        self._fingers[pointer] = control
        if control in DPAD_KEYS:
            self._repeat = (control, now + REPEAT_DELAY)
        return [_key_event(self._key_for(control))]

    def _release(self, pointer):
        control = self._fingers.pop(pointer, None)
        if self._repeat and control == self._repeat[0] and control not in self._fingers.values():
            self._repeat = None

    def _drag(self, pointer, pos, now):
        old = self._fingers.get(pointer)
        if old is None:
            return []
        new = self._control_at(pos)
        if new == old:
            return []
        self._release(pointer)
        # Палец переполз на соседнее направление крестовины — переключаемся;
        # случайное сползание на кнопку предмета намеренно игнорируется.
        if new in DPAD_KEYS:
            return self._press(pointer, pos, now)
        return []

    def tick(self, now):
        """Автоповтор зажатой крестовины; вызывается каждый кадр."""
        if not self._repeat or now < self._repeat[1]:
            return []
        control = self._repeat[0]
        self._repeat = (control, now + REPEAT_INTERVAL)
        return [_key_event(DPAD_KEYS[control])]

    # --- отрисовка ---

    def _pressed(self, control):
        return control in self._fingers.values()

    def draw(self, screen, fonts, sprites):
        # Справке отдаётся весь экран: панель не рисуется, выход — тап.
        if self.game.state == "HELP":
            return
        screen.fill(_PANEL_BG, self.panel_rect)
        pygame.draw.line(screen, (48, 48, 54), self.panel_rect.topleft, self.panel_rect.topright, 2)

        # Крестовина: цельный крест + стрелки; в центре — кнопка бега.
        for name, rect in self.dpad_rects.items():
            color = _BTN_PRESSED if self._pressed(name) else _BTN_BASE
            pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, _BTN_BASE, self.dpad_hub)
        for name, rect in self.dpad_rects.items():
            pygame.draw.rect(screen, _BTN_EDGE, rect, 2, border_radius=6)
            self._draw_arrow(screen, name, rect)
        hub_color = _BTN_PRESSED if self._pressed("run") else (40, 40, 46)
        pygame.draw.circle(screen, hub_color, self.dpad_center, 22)
        pygame.draw.circle(screen, _BTN_EDGE, self.dpad_center, 22, 2)
        self._draw_runner(screen, self.dpad_center)

        # Ромб предметов: круглая кнопка со спрайтом предмета.
        for name, (bx, by) in self.button_centers.items():
            color = _BTN_PRESSED if self._pressed(name) else _BTN_BASE
            pygame.draw.circle(screen, color, (bx, by), self.button_radius)
            pygame.draw.circle(screen, _BTN_EDGE, (bx, by), self.button_radius, 3)
            frame = sprites.sprite(ITEM_BUTTONS[name][1])
            # Спрайт вписывается в кнопку с обеих сторон: мелкие фляжки
            # растягиваются, высокий меч ужимается.
            limit = self.button_radius * 2 - 22
            ratio = min(limit / frame.get_width(), limit / frame.get_height())
            frame = pygame.transform.scale_by(frame, ratio)
            screen.blit(frame, frame.get_rect(center=(bx, by)))

        for name, rect in self.pill_rects.items():
            color = _BTN_PRESSED if self._pressed(name) else _BTN_BASE
            pygame.draw.rect(screen, color, rect, border_radius=pill_radius(rect))
            pygame.draw.rect(screen, _BTN_EDGE, rect, 2, border_radius=pill_radius(rect))
            text = name.upper()
            if name == "select":
                # Подпись следует контексту: в игре — справка, в списке
                # предметов — использование выбранного.
                if self.game.state == "PLAYING":
                    text = "HELP"
                elif self.game.state == "ITEM_MENU":
                    text = "USE"
            label = fonts.small.render(text, True, HILITE if name == "select" else WHITE)
            screen.blit(label, label.get_rect(center=rect.center))

    def _draw_runner(self, screen, center):
        """Пиктограмма бегуна (кнопка в центре крестовины): белый силуэт из
        assets/ui_run.png, ужатый со сглаживанием под размер кнопки."""
        icon = getattr(self, "_runner_icon", None)
        if icon is None:
            path = Path(__file__).parent.parent / "assets" / "ui_run.png"
            icon = pygame.transform.smoothscale(pygame.image.load(str(path)).convert_alpha(), (34, 34))
            self._runner_icon = icon
        screen.blit(icon, icon.get_rect(center=center))

    @staticmethod
    def _draw_arrow(screen, direction, rect):
        cx, cy = rect.center
        s = 10
        points = {
            "up": [(cx, cy - s), (cx - s, cy + s // 2), (cx + s, cy + s // 2)],
            "down": [(cx, cy + s), (cx - s, cy - s // 2), (cx + s, cy - s // 2)],
            "left": [(cx - s, cy), (cx + s // 2, cy - s), (cx + s // 2, cy + s)],
            "right": [(cx + s, cy), (cx - s // 2, cy - s), (cx - s // 2, cy + s)],
        }
        pygame.draw.polygon(screen, _ARROW, points[direction])


def pill_radius(rect):
    return rect.height // 2
