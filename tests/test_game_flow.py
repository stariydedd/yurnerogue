"""Тесты конечного автомата игры: pygame headless (SDL dummy), без сети."""

import asyncio

import pygame
import pytest
from presentation.view import Game


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield
    pygame.quit()


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode)


@pytest.fixture()
def playing_game():
    game = Game()
    game.handle_event(key(pygame.K_RETURN))  # New Game -> NAME_ENTRY
    game.handle_event(key(pygame.K_RETURN))  # пустое имя -> PLAYING
    return game


def test_new_game_flow_reaches_playing(playing_game):
    assert playing_game.state == "PLAYING"
    assert playing_game.session is not None


def test_new_game_seed_differs_despite_fixed_rng_state():
    # В WASM интерпретатор стартует с одинаковым состоянием RNG на каждой
    # загрузке страницы; start_new_game обязан пересеять генератор часами,
    # иначе первый уровень всегда один и тот же.
    import random

    seeds = []
    for _ in range(2):
        random.seed(42)  # имитация одинакового состояния после загрузки страницы
        game = Game()
        game.handle_event(key(pygame.K_RETURN))
        game.handle_event(key(pygame.K_RETURN))
        seeds.append(game.session.level.seed)
    assert seeds[0] != seeds[1]


def test_name_entry_typing_and_backspace():
    game = Game()
    game.handle_event(key(pygame.K_RETURN))
    assert game.state == "NAME_ENTRY"
    for ch in "hero":
        game.handle_event(key(0, unicode=ch))
    game.handle_event(key(pygame.K_BACKSPACE))
    assert game.name_input == "her"
    game.handle_event(key(pygame.K_RETURN))
    assert game.state == "PLAYING"
    assert game.player_name == "her"


def test_name_entry_escape_returns_to_menu():
    game = Game()
    game.handle_event(key(pygame.K_RETURN))
    game.handle_event(key(pygame.K_ESCAPE))
    assert game.state == "MAIN_MENU"


def test_movement_updates_stats(playing_game):
    # Игрок стартует внутри комнаты (минимум 4x3 пола), значит хотя бы одно из
    # четырёх направлений проходимо. Позицию сравнивать нельзя: W затем S
    # возвращает игрока в исходную клетку, хотя движение было.
    session = playing_game.session
    for k in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
        playing_game.handle_event(key(k))
    assert session.stats["tiles_moved"] > 0 or session.stats["attacks_made"] > 0


def test_item_menu_without_items_shows_message(playing_game):
    playing_game.handle_event(key(pygame.K_j))
    assert playing_game.state == "PLAYING"
    assert "No food" in playing_game.session.message


def test_item_menu_arrow_selection_uses_item(playing_game):
    # Выбор стрелками + Enter (путь тач-управления): вторая строка списка.
    from domain.domain import ItemType, Subject

    person = playing_game.session.get_player()
    for name in ("Bread", "Meat"):
        person.backpack.add_item(Subject(subject_type=ItemType.FOOD, health_effect=1, name=name))
    hp_before = person.health
    person.health = max(1, hp_before - 5)
    playing_game.handle_event(key(pygame.K_j))
    assert playing_game.state == "ITEM_MENU"
    playing_game.handle_event(key(pygame.K_DOWN))
    playing_game.handle_event(key(pygame.K_RETURN))
    assert playing_game.state == "PLAYING"
    assert "Meat" in playing_game.session.message
    assert all(it.name != "Meat" for it in person.backpack.items)


def test_run_moves_until_wall(playing_game):
    # Без врагов бег вправо должен довести до стены комнаты (или края тропы).
    from domain.businessLogic import can_move_to

    session = playing_game.session
    for room in session.get_rooms():
        if room is not None:
            room.enemies.clear()
            room.items.clear()
    person = session.get_player()
    # Ставим игрока к левому краю его комнаты — бег вправо детерминирован.
    player_room = next(
        r for r in session.get_rooms()
        if r is not None
        and r.crd.x <= person.crd.x < r.crd.x + r.width
        and r.crd.y <= person.crd.y < r.crd.y + r.height
    )
    person.crd.x = player_room.crd.x
    start_x = person.crd.x
    playing_game.handle_event(key(pygame.K_f))
    assert playing_game.pending_run
    playing_game.handle_event(key(pygame.K_d))
    assert not playing_game.pending_run
    assert person.crd.x > start_x  # пробежал больше одной клетки от старта
    # упёрся: правее либо стена, либо лестница
    nx, ny = person.crd.x + 1, person.crd.y
    exit_ahead = session.get_exit().x == nx and session.get_exit().y == ny
    assert exit_ahead or not can_move_to(nx, ny, session)


def test_corridor_turn_follows_single_continuation(playing_game):
    # На клетке коридора с единственным продолжением (не назад) бег поворачивает.
    import pytest as _pytest

    session = playing_game.session
    for room in session.get_rooms():
        if room is not None:
            room.enemies.clear()
    person = session.get_player()
    g = playing_game
    # ищем клетку тропы и направление входа, при котором прямо нельзя,
    # а продолжение ровно одно
    from domain.businessLogic import build_grid_map, can_move_to
    grid = build_grid_map(session.get_rooms(), session.get_passages(), person, session.get_exit())
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if not g._is_corridor_cell(x, y):
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                person.crd.x, person.crd.y = x, y
                if can_move_to(x + dx, y + dy, session):
                    continue  # прямо можно — поворот не нужен
                turn = g._corridor_turn(dx, dy)
                if turn is not None:
                    assert turn != (-dx, -dy)  # не разворот
                    tx, ty = x + turn[0], y + turn[1]
                    assert g._is_corridor_cell(tx, ty)
                    return
    _pytest.skip("на этой карте не нашлось подходящего поворота")


def test_run_stops_at_room_entrance(playing_game):
    # Бег по коридору завершается на первой клетке комнаты, а не насквозь.
    import pytest as _pytest
    from domain.businessLogic import build_grid_map
    from domain.consts import SYM_CORRIDOR, SYM_DOOR, SYM_ROOM_FLOOR

    session = playing_game.session
    for room in session.get_rooms():
        if room is not None:
            room.enemies.clear()
            room.items.clear()
    person = session.get_player()
    grid = build_grid_map(session.get_rooms(), session.get_passages(), person, session.get_exit())
    for y in range(len(grid)):
        for x in range(2, len(grid[0]) - 1):
            if (grid[y][x] == SYM_DOOR and grid[y][x + 1] == SYM_ROOM_FLOOR
                    and grid[y][x - 1] == SYM_CORRIDOR and grid[y][x - 2] == SYM_CORRIDOR):
                person.crd.x, person.crd.y = x - 2, y
                playing_game.handle_event(key(pygame.K_f))
                playing_game.handle_event(key(pygame.K_d))
                assert (person.crd.x, person.crd.y) == (x + 1, y)
                return
    _pytest.skip("на этой карте нет прямого захода в дверь слева")


def test_run_cancelled_by_non_direction_key(playing_game):
    person = playing_game.session.get_player()
    start = (person.crd.x, person.crd.y)
    playing_game.handle_event(key(pygame.K_f))
    playing_game.handle_event(key(pygame.K_j))  # не направление — отмена
    assert not playing_game.pending_run
    assert (person.crd.x, person.crd.y) == start


def test_quit_dialog_escape_resumes(playing_game):
    playing_game.handle_event(key(pygame.K_q))
    assert playing_game.state == "QUIT_DIALOG"
    playing_game.handle_event(key(pygame.K_ESCAPE))
    assert playing_game.state == "PLAYING"


def test_quit_dialog_confirm_returns_to_menu(playing_game):
    playing_game.handle_event(key(pygame.K_q))
    playing_game.handle_event(key(pygame.K_RETURN))  # "Return to Menu" (первая опция)
    assert playing_game.state == "MAIN_MENU"
    assert playing_game.session is None


def test_main_menu_options():
    from presentation.view import MAIN_MENU_OPTIONS
    assert [opt[1] for opt in MAIN_MENU_OPTIONS] == ["new", "scoreboard", "help"]


def test_help_from_menu_returns_to_menu():
    game = Game()
    game.handle_event(key(pygame.K_DOWN))
    game.handle_event(key(pygame.K_DOWN))  # выбор Help
    game.handle_event(key(pygame.K_RETURN))
    assert game.state == "HELP"
    game.handle_event(key(pygame.K_SPACE))
    assert game.state == "MAIN_MENU"


def test_help_from_game_returns_to_game(playing_game):
    playing_game.handle_event(key(pygame.K_F1))
    assert playing_game.state == "HELP"
    playing_game.handle_event(key(pygame.K_SPACE))
    assert playing_game.state == "PLAYING"


def test_death_screen_returns_to_menu(playing_game):
    # _finish_run планирует отправку счёта через asyncio; в игре цикл всегда
    # запущен под asyncio.run, поэтому подкладываем event loop и здесь.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        playing_game.session.get_player().health = 0
        playing_game._check_game_over()
        assert playing_game.state == "DEATH"
        playing_game.handle_event(key(pygame.K_RETURN))
        assert playing_game.state == "MAIN_MENU"
        assert playing_game.session is None
    finally:
        loop.close()
        asyncio.set_event_loop(None)
