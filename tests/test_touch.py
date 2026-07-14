"""Тесты тач-раскладки: геометрия панели и перевод касаний в клавишные события."""

import math

import pygame
import pytest
from presentation import config as cfg
from presentation.touch import REPEAT_DELAY, REPEAT_INTERVAL, TouchControls
from presentation.view import Game

_LAYOUT_KEYS = ("TOUCH_MODE", "SCREEN_W", "SCREEN_H", "PANEL_H", "CONTROLS_H",
                "GRID_W", "GRID_H", "VIEW_COLS", "VIEW_ROWS")


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield
    pygame.quit()


@pytest.fixture()
def touch_env():
    # apply_touch_layout мутирует модуль config — возвращаем десктопные
    # значения после теста, чтобы не влиять на другие модули тестов.
    saved = {k: getattr(cfg, k) for k in _LAYOUT_KEYS}
    cfg.apply_touch_layout(390, 844)
    yield
    for k, v in saved.items():
        setattr(cfg, k, v)


@pytest.fixture()
def touch_game(touch_env):
    game = Game(touch_mode=True)
    return game, TouchControls(game)


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode)


def finger_down(tc, pos, finger_id=1, now=0):
    event = pygame.event.Event(pygame.FINGERDOWN, x=pos[0] / cfg.SCREEN_W,
                               y=pos[1] / cfg.SCREEN_H, finger_id=finger_id)
    return tc.translate(event, now=now)


def finger_up(tc, finger_id=1):
    event = pygame.event.Event(pygame.FINGERUP, x=0, y=0, finger_id=finger_id)
    return tc.translate(event)


def test_touch_layout_dimensions(touch_env):
    assert cfg.SCREEN_W == 480
    assert cfg.GRID_H + cfg.PANEL_H + cfg.CONTROLS_H == cfg.SCREEN_H
    assert cfg.VIEW_COLS * 32 >= cfg.GRID_W
    assert cfg.VIEW_ROWS * 32 >= cfg.GRID_H


def test_controls_fit_inside_panel(touch_game):
    _, tc = touch_game
    panel = tc.panel_rect
    assert panel.bottom <= cfg.SCREEN_H
    for rect in tc.dpad_rects.values():
        assert panel.contains(rect)
    for bx, by in tc.button_centers.values():
        r = tc.button_radius
        assert panel.collidepoint(bx - r, by - r) and panel.collidepoint(bx + r, by + r)
    for rect in tc.pill_rects.values():
        assert panel.contains(rect)


def test_dpad_and_buttons_do_not_overlap(touch_game):
    _, tc = touch_game
    for rect in tc.dpad_rects.values():
        for bx, by in tc.button_centers.values():
            cx, cy = rect.center
            assert math.hypot(cx - bx, cy - by) > tc.button_radius + rect.width // 2


def test_dpad_press_emits_arrow_key(touch_game):
    game, tc = touch_game
    events = finger_down(tc, tc.dpad_rects["up"].center)
    assert [e.key for e in events] == [pygame.K_UP]


def test_item_buttons_emit_item_keys(touch_game):
    game, tc = touch_game
    expected = {"weapon": pygame.K_h, "food": pygame.K_j,
                "elixir": pygame.K_k, "scroll": pygame.K_e}
    for i, (name, wanted) in enumerate(expected.items()):
        events = finger_down(tc, tc.button_centers[name], finger_id=10 + i)
        assert [e.key for e in events] == [wanted]
        finger_up(tc, finger_id=10 + i)


def test_select_emits_enter(touch_game):
    game, tc = touch_game
    events = finger_down(tc, tc.pill_rects["select"].center)
    assert [e.key for e in events] == [pygame.K_RETURN]


def test_dpad_hub_emits_run_key(touch_game):
    game, tc = touch_game
    events = finger_down(tc, tc.dpad_center)
    assert [e.key for e in events] == [pygame.K_f]


def test_select_becomes_help_in_game(touch_game):
    game, tc = touch_game
    game.state = "PLAYING"
    events = finger_down(tc, tc.pill_rects["select"].center)
    assert [e.key for e in events] == [pygame.K_F1]


def test_help_tap_anywhere_returns(touch_game):
    # В справке панель скрыта — любой тап (даже мимо кнопок) закрывает экран.
    game, tc = touch_game
    game.state = "HELP"
    events = finger_down(tc, (cfg.SCREEN_W // 2, 10))
    assert [e.key for e in events] == [pygame.K_SPACE]


def test_menu_key_depends_on_state(touch_game):
    game, tc = touch_game
    events = finger_down(tc, tc.pill_rects["menu"].center, finger_id=1)
    assert [e.key for e in events] == [pygame.K_q]
    finger_up(tc, finger_id=1)
    game.state = "ITEM_MENU"
    events = finger_down(tc, tc.pill_rects["menu"].center, finger_id=2)
    assert [e.key for e in events] == [pygame.K_ESCAPE]


def test_dpad_hold_autorepeats(touch_game):
    game, tc = touch_game
    finger_down(tc, tc.dpad_rects["right"].center, now=1000)
    assert tc.tick(1000 + REPEAT_DELAY - 1) == []
    repeated = tc.tick(1000 + REPEAT_DELAY)
    assert [e.key for e in repeated] == [pygame.K_RIGHT]
    repeated = tc.tick(1000 + REPEAT_DELAY + REPEAT_INTERVAL)
    assert [e.key for e in repeated] == [pygame.K_RIGHT]
    finger_up(tc)
    assert tc.tick(1000 + REPEAT_DELAY + 2 * REPEAT_INTERVAL) == []


def test_tap_outside_controls_is_swallowed(touch_game):
    _, tc = touch_game
    assert finger_down(tc, (cfg.SCREEN_W // 2, 10)) == []


def test_keyboard_events_pass_through(touch_game):
    _, tc = touch_game
    assert tc.translate(key(pygame.K_w)) is None


def test_full_touch_game_start(touch_game):
    # START в меню (touch_mode вне браузера падает в NAME_ENTRY),
    # START ещё раз — анонимная игра; крестовиной можно ходить.
    game, tc = touch_game
    for e in finger_down(tc, tc.pill_rects["select"].center, finger_id=1):
        game.handle_event(e)
    finger_up(tc, finger_id=1)
    assert game.state == "NAME_ENTRY"
    for e in finger_down(tc, tc.pill_rects["select"].center, finger_id=2):
        game.handle_event(e)
    finger_up(tc, finger_id=2)
    assert game.state == "PLAYING"
    for e in finger_down(tc, tc.dpad_rects["down"].center, finger_id=3):
        game.handle_event(e)
    assert game.session is not None
