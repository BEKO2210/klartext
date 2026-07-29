"""Technische Fair-Use-Kontrolle.

Ausschließlich Serverschutz — keine Tarife, keine Bezahlung, keine gesperrten
Funktionen. Alle Benutzer haben dieselben Rechte und dieselben Limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import db, settings_store


class QuotaExceeded(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class Usage:
    jobs_hour: int
    jobs_day: int
    pages_day: int
    bytes_day: int
    active: int
    queued: int


async def current_usage(user_id: int) -> Usage:
    row = await db.fetchrow(
        """
        SELECT
          COALESCE((SELECT SUM(jobs)  FROM usage_events
                     WHERE user_id = $1 AND created_at > now() - interval '1 hour'), 0) AS jobs_hour,
          COALESCE((SELECT SUM(jobs)  FROM usage_events
                     WHERE user_id = $1 AND created_at > now() - interval '1 day'), 0)  AS jobs_day,
          COALESCE((SELECT SUM(pages) FROM usage_events
                     WHERE user_id = $1 AND created_at > now() - interval '1 day'), 0)  AS pages_day,
          COALESCE((SELECT SUM(bytes) FROM usage_events
                     WHERE user_id = $1 AND created_at > now() - interval '1 day'), 0)  AS bytes_day,
          (SELECT COUNT(*) FROM jobs WHERE user_id = $1 AND status = 'processing') AS active,
          (SELECT COUNT(*) FROM jobs WHERE user_id = $1 AND status = 'queued')     AS queued
        """,
        user_id,
    )
    return Usage(
        jobs_hour=int(row["jobs_hour"]),
        jobs_day=int(row["jobs_day"]),
        pages_day=int(row["pages_day"]),
        bytes_day=int(row["bytes_day"]),
        active=int(row["active"]),
        queued=int(row["queued"]),
    )


async def check_batch(user_id: int, file_count: int, total_bytes: int, est_pages: int) -> None:
    """Prüft einen kompletten Upload, bevor irgendetwas gespeichert wird."""
    lim = await settings_store.limits()
    use = await current_usage(user_id)

    if file_count > lim["max_files_per_upload"]:
        raise QuotaExceeded("too_many_files")
    if use.queued + file_count > lim["max_queued_jobs"]:
        raise QuotaExceeded("queue_full")
    if use.jobs_hour + file_count > lim["jobs_per_hour"]:
        raise QuotaExceeded("hourly_limit")
    if use.jobs_day + file_count > lim["jobs_per_day"]:
        raise QuotaExceeded("daily_limit")
    if use.pages_day + est_pages > lim["pages_per_day"]:
        raise QuotaExceeded("pages_limit")
    if use.bytes_day + total_bytes > lim["mb_per_day"] * 1024 * 1024:
        raise QuotaExceeded("volume_limit")

    global_queued = await db.fetchval("SELECT COUNT(*) FROM jobs WHERE status = 'queued'")
    if int(global_queued) + file_count > lim["global_queue_limit"]:
        raise QuotaExceeded("server_busy")


async def record(user_id: int, pages: int, size_bytes: int) -> None:
    await db.execute(
        "INSERT INTO usage_events(user_id, jobs, pages, bytes) VALUES($1, 1, $2, $3)",
        user_id,
        max(pages, 0),
        max(size_bytes, 0),
    )


async def prune() -> None:
    await db.execute("DELETE FROM usage_events WHERE created_at < now() - interval '30 days'")
