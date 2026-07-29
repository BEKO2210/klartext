"""Datenbankzugriff (asyncpg). Alle Abfragen sind parametrisiert."""

from __future__ import annotations

import asyncio
import logging
import pathlib

import asyncpg

from .config import CONFIG

log = logging.getLogger("klartext.db")

_pool: asyncpg.Pool | None = None
MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "migrations"


async def connect(retries: int = 30) -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    last: Exception | None = None
    for attempt in range(retries):
        try:
            _pool = await asyncpg.create_pool(
                dsn=CONFIG.db_dsn,
                min_size=CONFIG.db_pool_min,
                max_size=CONFIG.db_pool_max,
                command_timeout=30,
            )
            return _pool
        except Exception as exc:  # noqa: BLE001 - Startphase, Datenbank kommt evtl. später
            last = exc
            await asyncio.sleep(min(2 + attempt, 5))
    raise RuntimeError("Datenbankverbindung nicht möglich") from last


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Datenbank-Pool nicht initialisiert")
    return _pool


async def migrate() -> None:
    """Führt alle noch nicht angewendeten .sql-Dateien in Reihenfolge aus."""
    async with pool().acquire() as con:
        await con.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        done = {r["name"] for r in await con.fetch("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in done:
                continue
            log.info("Migration wird angewendet: %s", path.name)
            async with con.transaction():
                await con.execute(path.read_text(encoding="utf-8"))
                await con.execute("INSERT INTO schema_migrations(name) VALUES($1)", path.name)


async def fetch(query: str, *args):
    async with pool().acquire() as con:
        return await con.fetch(query, *args)


async def fetchrow(query: str, *args):
    async with pool().acquire() as con:
        return await con.fetchrow(query, *args)


async def fetchval(query: str, *args):
    async with pool().acquire() as con:
        return await con.fetchval(query, *args)


async def execute(query: str, *args) -> str:
    async with pool().acquire() as con:
        return await con.execute(query, *args)
