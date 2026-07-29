"""Auflösung der Fair-Use-Limits: DB-Override (Admin) vor ENV-Vorgabe.

Kurzer Cache, damit nicht jeder Request die Tabelle liest.
"""

from __future__ import annotations

import time

from . import db
from .config import CONFIG, LIMIT_DEFS

_cache: dict[str, int] = {}
_cache_at: float = 0.0
_TTL_SECONDS = 15.0


async def _load() -> dict[str, int]:
    global _cache, _cache_at
    now = time.monotonic()
    if _cache and now - _cache_at < _TTL_SECONDS:
        return _cache
    values = dict(CONFIG.limit_env_defaults)
    try:
        rows = await db.fetch("SELECT key, value FROM app_settings")
        for row in rows:
            if row["key"] in LIMIT_DEFS:
                try:
                    values[row["key"]] = int(row["value"])
                except ValueError:
                    continue
    except Exception:  # noqa: BLE001 - Limits dürfen nie den Request killen
        pass
    _cache, _cache_at = values, now
    return values


async def limits() -> dict[str, int]:
    return dict(await _load())


async def limit(key: str) -> int:
    return (await _load())[key]


async def set_limit(key: str, value: int) -> None:
    global _cache_at
    if key not in LIMIT_DEFS:
        raise KeyError(key)
    if value < 0 or value > 1_000_000:
        raise ValueError("Wert außerhalb des zulässigen Bereichs")
    await db.execute(
        "INSERT INTO app_settings(key, value) VALUES($1, $2) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()",
        key,
        str(value),
    )
    _cache_at = 0.0
