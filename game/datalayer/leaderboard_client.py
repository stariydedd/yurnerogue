"""HTTP-клиент глобального лидерборда.

Работает в двух средах:
- desktop: urllib в отдельном потоке (не блокирует кадр);
- браузер (pygbag/WASM): aio.fetch.RequestHandler из рантайма pygbag,
  который ходит через JS fetch. Его JS-обёртка при сетевой ошибке ждёт
  ответа бесконечно, поэтому все вызовы обёрнуты в wait_for с таймаутом.
"""

import asyncio
import json
import os
import sys
from urllib.parse import urlencode

from domain.consts import MAX_LEVELS

TIMEOUT_SECONDS = 10

IS_EMSCRIPTEN = sys.platform == "emscripten"


def _emscripten_api_base():
    """В проде игра и API живут на одном домене за nginx — базовый URL пустой
    (относительные пути). При локальном тесте в браузере (pygbag-сервер на
    нестандартном порту) API ищем на localhost:8000."""
    try:
        import platform
        port = str(platform.window.location.port)
        if port in ("", "80", "443"):
            return ""
        return "http://localhost:8000"
    except Exception:
        return ""


if IS_EMSCRIPTEN:
    API_BASE = _emscripten_api_base()
else:
    API_BASE = os.environ.get("ROGUE_API", "http://localhost:8000")


if IS_EMSCRIPTEN:
    from aio.fetch import RequestHandler

    _handler = RequestHandler()
    _handler.debug = False

    async def _get(path, params):
        return await _handler.get(API_BASE + path, params)

    async def _post(path, payload):
        return await _handler.post(API_BASE + path, payload)
else:
    import urllib.request

    def _sync_request(url, body=None):
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read().decode()

    async def _get(path, params):
        url = API_BASE + path + ("?" + urlencode(params) if params else "")
        return await asyncio.to_thread(_sync_request, url)

    async def _post(path, payload):
        body = json.dumps(payload).encode()
        return await asyncio.to_thread(_sync_request, API_BASE + path, body)


def run_payload(session, player_name):
    """Собирает тело POST /api/runs из завершившейся сессии.

    Вызывается синхронно в момент смерти/победы, чтобы отправка не зависела
    от дальнейшей судьбы объекта session.
    """
    person = session.get_player()
    return {
        "player_name": player_name or "anonymous",
        "treasures": person.treasures,
        "level": min(session.level_num, MAX_LEVELS),
        "enemies_killed": session.stats["enemies_killed"],
        "food_used": session.stats["food_used"],
        "elixirs_used": session.stats["elixirs_used"],
        "scrolls_read": session.stats["scrolls_read"],
        "attacks_made": session.stats["attacks_made"],
        "hits_taken": session.stats["hits_taken"],
        "tiles_moved": session.stats["tiles_moved"],
    }


async def submit_run(payload):
    """Отправляет результат забега. Возвращает созданную запись или None при ошибке."""
    try:
        raw = await asyncio.wait_for(_post("/api/runs", payload), TIMEOUT_SECONDS)
        data = json.loads(raw)
        return data if isinstance(data, dict) and "id" in data else None
    except Exception:
        return None


async def fetch_leaderboard(limit=10):
    """Забирает глобальный топ. Возвращает список записей или None при ошибке."""
    try:
        raw = await asyncio.wait_for(_get("/api/leaderboard", {"limit": limit}), TIMEOUT_SECONDS)
        data = json.loads(raw)
        return data if isinstance(data, list) else None
    except Exception:
        return None
