"""Доступ к браузерному окружению (pygbag/WASM).

На десктопе все функции возвращают безопасные заглушки, поэтому вызывающий
код не проверяет платформу сам. Переменная окружения ROGUE_TOUCH=1 форсит
тач-раскладку в нативном запуске — для отладки без телефона.
"""
import os
import sys


def is_web():
    return sys.platform == "emscripten"


def _window():
    # В pygbag модуль platform подменён и содержит объект window браузера.
    import platform
    return platform.window


def is_touch_device():
    """True, когда основной способ ввода — тач-экран (телефон, планшет).

    pointer: coarse не срабатывает на ноутбуках с тач-экраном, где основной
    ввод всё равно мышь; maxTouchPoints — запасной вариант для старых браузеров.
    """
    if os.environ.get("ROGUE_TOUCH") == "1":
        return True
    if not is_web():
        return False
    win = _window()
    try:
        return bool(win.matchMedia("(pointer: coarse)").matches)
    except Exception:
        pass
    try:
        return int(win.navigator.maxTouchPoints) > 0
    except Exception:
        return False


def window_size():
    """Размер окна браузера в CSS-пикселях; вне браузера — пропорции телефона."""
    if is_web():
        try:
            win = _window()
            return int(win.innerWidth), int(win.innerHeight)
        except Exception:
            pass
    return 390, 844


def prompt_text(message, default=""):
    """Системный prompt() браузера. None — отмена или окружение без prompt."""
    if not is_web():
        return None
    try:
        result = _window().prompt(message, default)
    except Exception:
        return None
    return None if result is None else str(result)
