import pygame
from domain.businessLogic import build_grid_map, compute_visibility, item_stat_label
from domain.consts import COLS, ROWS, SYM_DOOR, SYM_WALL

from presentation.colors import (
    BLACK,
    GOLD,
    HILITE,
    HINT_COLOR,
    MSG_COLOR,
    OPPONENT_COLORS,
    PANEL_BG,
    TILE_COLORS,
    WHITE,
)
from presentation.config import GRID_H, GRID_W, PANEL_H, SCREEN_H, SCREEN_W, TILE_SIZE


def _blit(screen, font, text, pos, color):
    """Рисует одну строку текста в заданной точке (левый верхний угол)."""
    screen.blit(font.render(text, True, color), pos)


def _center_text(screen, font, text, y, color):
    """Рисует строку текста, отцентрированную по ширине экрана."""
    surf = font.render(text, True, color)
    rect = surf.get_rect(centerx=SCREEN_W // 2, y=y)
    screen.blit(surf, rect)


def _draw_glyph(screen, font, x, y, ch, color):
    """Рисует символ, отцентрированный внутри клетки (x, y)."""
    surf = font.render(ch, True, color)
    rect = surf.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2))
    screen.blit(surf, rect)


def _dim_background(screen):
    """Затемняет игровое поле полупрозрачным слоем (для диалогов поверх карты)."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))


def draw_map(screen, fonts, session):
    """Отрисовывает уровень с учётом тумана войны (без статус-панели)."""
    rooms = session.get_rooms()
    passages = session.get_passages()
    player = session.get_player()
    level_exit = session.get_exit()
    opponents = session.get_opponents()
    visible_opponents = [op for op in opponents if op.is_alive() and op.is_visible]

    grid = build_grid_map(rooms, passages, player, level_exit, visible_opponents)
    base_grid = build_grid_map(rooms, passages, player, level_exit)
    fully_visible, wall_only = compute_visibility(session, base_grid)

    screen.fill(BLACK, (0, 0, GRID_W, GRID_H))

    for y in range(ROWS):
        row = grid[y]
        for x in range(COLS):
            visible = (x, y) in fully_visible
            dimmed = (not visible) and (x, y) in wall_only and row[x] in (SYM_WALL, SYM_DOOR)
            if not visible and not dimmed:
                continue
            color = TILE_COLORS.get(row[x], BLACK)
            if dimmed:
                color = tuple(c // 3 for c in color)
            pygame.draw.rect(screen, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    for room in rooms:
        if room is None:
            continue
        for item in room.items:
            if (item.crd.x, item.crd.y) in fully_visible:
                _draw_glyph(screen, fonts.glyph, item.crd.x, item.crd.y, "!", GOLD)

    if (level_exit.x, level_exit.y) in fully_visible:
        _draw_glyph(screen, fonts.glyph, level_exit.x, level_exit.y, ">", (120, 255, 120))

    for opponent in visible_opponents:
        if (opponent.crd.x, opponent.crd.y) not in fully_visible:
            continue
        sym, _ = opponent.get_visual_representation()
        color = OPPONENT_COLORS.get(opponent.type, WHITE)
        _draw_glyph(screen, fonts.glyph, opponent.crd.x, opponent.crd.y, sym, color)

    _draw_glyph(screen, fonts.glyph, player.crd.x, player.crd.y, "@", GOLD)


def draw_status_panel(screen, fonts, session):
    """Рисует нижнюю статус-панель: HP, характеристики, уровень, золото, оружие, сообщение."""
    player = session.get_player()
    weapon_name = f"{player.weapon.name} [+{player.weapon.strength_effect} STR]" if player.weapon else "Bare hands"
    status = (
        f"HP:{player.health}/{player.max_health}  STR:{player.strength}  AGI:{player.agility}  "
        f"LVL:{session.level_num}  GOLD:{player.treasures}  WPN:{weapon_name}"
    )
    pygame.draw.rect(screen, PANEL_BG, (0, GRID_H, SCREEN_W, PANEL_H))
    _blit(screen, fonts.ui, status, (10, GRID_H + 6), WHITE)
    if session.message:
        _blit(screen, fonts.ui, session.message, (10, GRID_H + 30), MSG_COLOR)
    binds = "[WASD/Arrows] Move  [H] Weapon  [J] Food  [K] Elixir  [E] Scroll  [Q] Quit"
    _blit(screen, fonts.ui, binds, (10, GRID_H + 54), HINT_COLOR)


def draw_playing(screen, fonts, session):
    """Полный кадр игрового процесса: карта + статус-панель."""
    draw_map(screen, fonts, session)
    draw_status_panel(screen, fonts, session)


def draw_item_menu_overlay(screen, fonts, items, allow_zero):
    """Рисует список предметов для выбора поверх нижней части карты."""
    lines = []
    if allow_zero:
        lines.append("0: Bare hands")
    for i, item in enumerate(items):
        lines.append(f"{i + 1}: {item.name}{item_stat_label(item)}")
    lines.append("ESC: cancel")

    box_h = 10 + len(lines) * 22
    box_y = GRID_H - box_h
    pygame.draw.rect(screen, (10, 10, 10), (0, box_y, SCREEN_W, box_h))
    pygame.draw.rect(screen, (90, 90, 90), (0, box_y, SCREEN_W, box_h), 1)
    for i, line in enumerate(lines):
        _blit(screen, fonts.ui, line, (10, box_y + 6 + i * 22), WHITE)


def _draw_dialog_box(screen, fonts, title, options, selected):
    """Рисует затемнение и центральное диалоговое окно с опциями."""
    _dim_background(screen)
    box_w, box_h = 420, 50 + len(options) * 36
    box_x = (SCREEN_W - box_w) // 2
    box_y = (SCREEN_H - box_h) // 2
    pygame.draw.rect(screen, (25, 25, 25), (box_x, box_y, box_w, box_h))
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), 2)
    _center_text(screen, fonts.ui, title, box_y + 12, WHITE)
    for i, (label, _) in enumerate(options):
        color = HILITE if i == selected else WHITE
        _center_text(screen, fonts.ui, label, box_y + 46 + i * 36, color)


def draw_quit_dialog(screen, fonts, options, selected):
    """Диалог подтверждения выхода из игры."""
    _draw_dialog_box(screen, fonts, "Quit game?", options, selected)


def draw_main_menu(screen, fonts, options, selected, message=""):
    """Главное меню со списком опций и, опционально, транзитным сообщением снизу."""
    screen.fill(BLACK)
    _center_text(screen, fonts.title, "ROGUE", SCREEN_H // 3, GOLD)
    for i, (label, _) in enumerate(options):
        color = HILITE if i == selected else WHITE
        _center_text(screen, fonts.ui, label, SCREEN_H // 3 + 70 + i * 40, color)
    if message:
        _center_text(screen, fonts.ui, message, SCREEN_H - 40, MSG_COLOR)


def draw_leaderboard_screen(screen, fonts, records, source=""):
    """Экран таблицы рекордов. records=None — глобальный топ ещё грузится."""
    screen.fill(BLACK)
    _center_text(screen, fonts.title, "HIGH SCORES", 30, GOLD)
    if source:
        _center_text(screen, fonts.ui, source, 84, HINT_COLOR)
    header = (
        f"{'#':>3}  {'NAME':<16}  {'GOLD':>6}  {'LVL':>4}  {'KILLS':>5}  {'FOOD':>4}  "
        f"{'ELIX':>4}  {'SCRL':>4}  {'ATK':>5}  {'HIT':>5}  {'MOVE':>6}"
    )
    if records is None:
        _center_text(screen, fonts.ui, "Loading global leaderboard...", 140, WHITE)
    elif not records:
        _center_text(screen, fonts.ui, "No records yet.", 140, WHITE)
    else:
        _center_text(screen, fonts.ui, header, 110, (170, 170, 170))
        for i, r in enumerate(records):
            name = str(r.get("player_name", "-"))[:16]
            line = (
                f"{i + 1:>3}  {name:<16}  {r['treasures']:>6}  {r['level']:>4}  {r['enemies_killed']:>5}  "
                f"{r['food_used']:>4}  {r['elixirs_used']:>4}  {r['scrolls_read']:>4}  "
                f"{r['attacks_made']:>5}  {r['hits_taken']:>5}  {r['tiles_moved']:>6}"
            )
            _center_text(screen, fonts.ui, line, 140 + i * 26, WHITE)
    _center_text(screen, fonts.ui, "Press any key to return...", SCREEN_H - 40, HINT_COLOR)


def draw_name_entry(screen, fonts, name_input):
    """Экран ввода имени игрока перед новой игрой."""
    screen.fill(BLACK)
    _center_text(screen, fonts.title, "ENTER YOUR NAME", SCREEN_H // 3, GOLD)
    box_w, box_h = 420, 44
    box_x = (SCREEN_W - box_w) // 2
    box_y = SCREEN_H // 3 + 80
    pygame.draw.rect(screen, (25, 25, 25), (box_x, box_y, box_w, box_h))
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), 2)
    _blit(screen, fonts.ui, name_input + "_", (box_x + 12, box_y + 10), WHITE)
    _center_text(screen, fonts.ui, "Enter: start  Esc: back  (empty = anonymous)",
                 box_y + box_h + 24, HINT_COLOR)


def draw_end_screen(screen, fonts, message, submit_status=""):
    """Экран смерти или победы со статусом отправки результата на сервер."""
    screen.fill(BLACK)
    _center_text(screen, fonts.title, message, SCREEN_H // 2 - 40, GOLD)
    if submit_status:
        _center_text(screen, fonts.ui, submit_status, SCREEN_H // 2 + 20, MSG_COLOR)
    _center_text(screen, fonts.ui, "Press Enter to exit.", SCREEN_H // 2 + 56, HINT_COLOR)
