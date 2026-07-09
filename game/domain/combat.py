import random

from domain.consts import *
from domain.domain import *


def check_hit(attacker_agility, defender_agility):
    """Проверяет попадание: формула из ловкости атакующего и цели"""
    chance = INITIAL_HIT_CHANCE + (attacker_agility - defender_agility - STANDART_AGILITY) * AGILITY_FACTOR
    return random.randint(0, 99) < max(0, min(100, int(chance)))


def calculate_loot(opponent):
    """Вычисляет количество сокровищ, выпадающих из поверженного врага"""
    return int(opponent.agility * 0.2 + opponent.health * 0.5 + opponent.strength * 0.5) + random.randint(0, 19)


def player_attacks_opponent(person, opponent):
    """Атака игрока по противнику. Возвращает нанесённый урон или -1 при промахе."""
    if opponent.type == OpponentType.VAMPIRE and opponent.vampire_first_strike:
        opponent.vampire_first_strike = False
        return -1

    if not check_hit(person.agility, opponent.agility):
        return -1

    if person.weapon:
        damage = max(0, int(person.weapon.strength_effect * (person.strength + STRENGTH_ADDITION) / 100))
    else:
        damage = max(0, int(INITIAL_DAMAGE + (person.strength - STANDART_STRENGTH) * STRENGTH_FACTOR))

    opponent.take_damage(damage)
    if not opponent.is_alive():
        person.receive_treasure(calculate_loot(opponent))

    return damage


def opponent_attacks_player(opponent, person):
    """Атака противника по игроку. Возвращает нанесённый урон или -1 при промахе."""
    if opponent.type != OpponentType.OGRE:
        if not check_hit(opponent.agility, person.agility):
            return -1

    if opponent.type == OpponentType.VAMPIRE:
        damage = max(1, person.max_health // MAX_HP_PART)
        person.max_health -= damage
        if person.health > person.max_health:
            person.health = person.max_health
        return damage

    if opponent.type == OpponentType.OGRE:
        if opponent.ogre_cooldown:
            opponent.ogre_cooldown = False
            return 0
        opponent.ogre_cooldown = True
        damage = max(0, int((opponent.strength - STANDART_STRENGTH) * STRENGTH_FACTOR))
    else:
        damage = max(0, int(INITIAL_DAMAGE + (opponent.strength - STANDART_STRENGTH) * STRENGTH_FACTOR))
    person.take_damage(damage)

    if opponent.type == OpponentType.SNAKE and random.randint(0, 99) < SLEEP_CHANCE:
        person.special_state = {"sleeping": True, "turns": 1}

    return damage


def _in_contact(opponent, person):
    """Проверяет, находится ли враг в клетке, соседней с игроком (с учётом диагонали змея)."""
    dx = abs(opponent.crd.x - person.crd.x)
    dy = abs(opponent.crd.y - person.crd.y)
    if dx + dy <= 1:
        return True
    if opponent.type == OpponentType.SNAKE and dx == 1 and dy == 1:
        return True
    return False


def process_enemy_turns(session):
    """Все живые враги делают ход: двигаются и атакуют игрока при контакте"""
    person = session.get_player()
    rooms = session.get_rooms()
    passages = session.get_passages()
    living = [op for op in session.get_opponents() if op.is_alive()]

    for opponent in living:
        if _in_contact(opponent, person):
            if opponent.type == OpponentType.GHOST:
                opponent.is_chasing = True
            damage = opponent_attacks_player(opponent, person)
            if damage > 0:
                session.stats["hits_taken"] += 1
            name = opponent_display_name(opponent.type)
            if damage == -1:
                session.set_message(f"The {name} missed you.")
            elif damage == 0:
                session.set_message(f"The {name} is preparing to strike...")
            elif opponent.type == OpponentType.VAMPIRE:
                session.set_message(f"The {name} drained your max HP by {damage}!")
            else:
                msg = f"The {name} hit you for {damage} dmg."
                if person.special_state.get("sleeping"):
                    msg += " You fall asleep!"
                session.set_message(msg)
        else:
            opponent.move(person.crd, rooms, passages, living)

    if person.special_state.get("sleeping"):
        turns_left = person.special_state.get("turns", 0) - 1
        if turns_left <= 0:
            person.special_state = {}
        else:
            person.special_state["turns"] = turns_left

    person.tick_effects()

    for opponent in living:
        if opponent.type == OpponentType.GHOST and not opponent.is_chasing:
            opponent.is_visible = random.randint(0, 99) < CHANCE_GHOST_VISIBLE
        else:
            opponent.is_visible = True
