import json
from pathlib import Path

from domain.consts import MAX_LEVELS
from domain.domain import Coord, ItemSubType, ItemType, Opponent, OpponentType, Room, Session, Subject

SAVE_FILE = Path(__file__).parent / "save.json"
LEADERBOARD_FILE = Path(__file__).parent / "leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10


def _item_to_dict(item):
    """Сериализует предмет (Subject) в словарь для сохранения в JSON."""
    return {
        "type":              item.type.value if item.type else None,
        "sub_type":          item.sub_type.value if item.sub_type else None,
        "health_effect":     item.health_effect,
        "max_health_effect": item.max_health_effect,
        "agility_effect":    item.agility_effect,
        "strength_effect":   item.strength_effect,
        "cost":              item.cost,
        "name":              item.name,
        "crd_x":             item.crd.x,
        "crd_y":             item.crd.y,
    }


def _dict_to_item(d):
    """Восстанавливает предмет (Subject) из словаря, загруженного из JSON."""
    item = Subject(
        subject_type=ItemType(d["type"]) if d["type"] else None,
        sub_type=ItemSubType(d["sub_type"]) if d["sub_type"] else None,
        health_effect=d["health_effect"],
        max_health_effect=d["max_health_effect"],
        agility_effect=d["agility_effect"],
        strength_effect=d["strength_effect"],
        cost=d["cost"],
        name=d["name"],
    )
    item.crd = Coord(d.get("crd_x", 0), d.get("crd_y", 0))
    return item


def _opponent_to_dict(op):
    """Сериализует врага (Opponent) в словарь для сохранения в JSON."""
    return {
        "type":                 op.type.value,
        "health":               op.health,
        "agility":              op.agility,
        "strength":             op.strength,
        "hostility":            op.hostility,
        "is_chasing":           op.is_chasing,
        "crd_x":                op.crd.x,
        "crd_y":                op.crd.y,
        "ogre_cooldown":        op.ogre_cooldown,
        "vampire_first_strike": op.vampire_first_strike,
        "last_direction":       list(op.last_direction) if op.last_direction else None,
    }


def _dict_to_opponent(d):
    """Восстанавливает врага (Opponent) из словаря, загруженного из JSON."""
    op = Opponent(
        opponent_type=OpponentType(d["type"]),
        health=d["health"],
        agility=d["agility"],
        strength=d["strength"],
        hostility=d["hostility"],
    )
    op.is_chasing = d["is_chasing"]
    op.crd = Coord(d["crd_x"], d["crd_y"])
    op.ogre_cooldown = d["ogre_cooldown"]
    op.vampire_first_strike = d["vampire_first_strike"]
    op.last_direction = tuple(d["last_direction"]) if d["last_direction"] else None
    return op


def _room_to_dict(room):
    """Сериализует комнату (Room) в словарь для сохранения в JSON, либо None."""
    if room is None:
        return None
    return {
        "x":       room.crd.x,
        "y":       room.crd.y,
        "width":   room.width,
        "height":  room.height,
        "items":   [_item_to_dict(it) for it in room.items],
        "enemies": [_opponent_to_dict(op) for op in room.enemies],
    }


def _dict_to_room(d):
    """Восстанавливает комнату (Room) из словаря, загруженного из JSON, либо None."""
    if d is None:
        return None
    room = Room(d["x"], d["y"], d["width"], d["height"])
    room.items = [_dict_to_item(it) for it in d["items"]]
    room.enemies = [_dict_to_opponent(op) for op in d["enemies"]]
    return room


def delete_save():
    """Очищает файл сохранения (вызывается при смерти или победе)."""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(None, f)
    except FileNotFoundError:
        pass


def save_game(session):
    """Сохраняет карту, игрока и статистику в save.json."""
    person = session.get_player()
    data = {
        "level_num":     session.level_num,
        "visited_rooms": list(session.visited_rooms),
        "stats":         session.stats,
        "level": {
            "start_room_idx": session.level.start_room_idx,
            "exit_x":         session.level.exit_crd.x,
            "exit_y":         session.level.exit_crd.y,
            "passages":       session.level.passages,
            "rooms":          [_room_to_dict(r) for r in session.level.rooms],
        },
        "player": {
            "crd_x":          person.crd.x,
            "crd_y":          person.crd.y,
            "health":         person.health,
            "max_health":     person.max_health,
            "strength":       person.strength,
            "agility":        person.agility,
            "treasures":      person.treasures,
            "active_effects": person.active_effects,
            "weapon":         _item_to_dict(person.weapon) if person.weapon else None,
            "backpack":       [_item_to_dict(it) for it in person.backpack.items],
        },
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_game():
    """
    Загружает save.json и возвращает готовую Session.
    Карта, враги, предметы на полу и состояние игрока восстанавливаются из файла.
    Возвращает None если файла нет.
    """
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    if data is None:
        return None

    session = Session(level=data["level_num"])
    session.visited_rooms = set(data.get("visited_rooms", []))
    session.stats = data["stats"]

    ld = data["level"]
    session.level.start_room_idx = ld["start_room_idx"]
    session.level.exit_crd = Coord(ld["exit_x"], ld["exit_y"])
    session.level.passages = ld["passages"]
    session.level.rooms = [_dict_to_room(r) for r in ld["rooms"]]

    person = session.get_player()
    pd = data["player"]
    person.crd         = Coord(pd["crd_x"], pd["crd_y"])
    person.health         = pd["health"]
    person.max_health     = pd["max_health"]
    person.strength       = pd["strength"]
    person.agility        = pd["agility"]
    person.treasures      = pd["treasures"]
    person.active_effects = pd["active_effects"]
    person.weapon         = _dict_to_item(pd["weapon"]) if pd["weapon"] else None
    person.backpack.items = [_dict_to_item(it) for it in pd["backpack"]]

    return session


def save_run(session):
    """Добавляет результат прохождения в таблицу рекордов."""
    try:
        with open(LEADERBOARD_FILE, encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        records = []

    person = session.get_player()
    records.append({
        "treasures":      person.treasures,
        "level":          min(session.level_num, MAX_LEVELS),
        "enemies_killed": session.stats["enemies_killed"],
        "food_used":      session.stats["food_used"],
        "elixirs_used":   session.stats["elixirs_used"],
        "scrolls_read":   session.stats["scrolls_read"],
        "attacks_made":   session.stats["attacks_made"],
        "hits_taken":     session.stats["hits_taken"],
        "tiles_moved":    session.stats["tiles_moved"],
    })

    records.sort(key=lambda r: (r["treasures"], r["level"]), reverse=True)
    records = records[:MAX_LEADERBOARD_ENTRIES]

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)


def load_leaderboard():
    """Загружает таблицу рекордов. Возвращает список или [] если файла нет."""
    try:
        with open(LEADERBOARD_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
