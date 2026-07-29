"""Worker: holt Jobs aus der Warteschlange, lässt Docling konvertieren, räumt auf.

Die Warteschlange liegt in Postgres. Ein Job wird mit FOR UPDATE SKIP LOCKED
genau einem Worker zugeteilt — auch bei mehreren Worker-Prozessen.

Es werden nie Dokumentinhalte protokolliert, auch keine Dateinamen.
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal

from . import db, postprocess, quota, settings_store, storage
from .config import CONFIG
from .docling_client import ConversionError, DoclingClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("klartext.worker")

_stop = asyncio.Event()


async def _claim_job(con, max_active_per_user: int):
    """Reserviert genau einen wartenden Job.

    Aufträge von Benutzern, die bereits ihr Limit an gleichzeitig laufenden
    Konvertierungen ausschöpfen, werden übersprungen. Damit kann ein einzelnes
    Konto die Warteschlange nicht für alle anderen blockieren.
    """
    async with con.transaction():
        row = await con.fetchrow(
            "SELECT j.id, j.user_id, j.original_name, j.mime_type, j.size_bytes, "
            "       j.page_count "
            "FROM jobs j WHERE j.status = 'queued' "
            "  AND (SELECT COUNT(*) FROM jobs a "
            "        WHERE a.user_id = j.user_id AND a.status = 'processing') < $1 "
            "ORDER BY j.created_at "
            "FOR UPDATE OF j SKIP LOCKED LIMIT 1",
            max_active_per_user,
        )
        if row is None:
            return None
        await con.execute(
            "UPDATE jobs SET status = 'processing', started_at = now(), "
            "attempts = attempts + 1 WHERE id = $1",
            row["id"],
        )
        return row


async def _fail(job_id: int, code: str) -> None:
    await db.execute(
        "UPDATE jobs SET status = 'error', error_code = $2, finished_at = now(), "
        "duration_ms = (EXTRACT(EPOCH FROM (now() - started_at)) * 1000)::int "
        "WHERE id = $1",
        job_id,
        code,
    )


async def _process(client: DoclingClient, job) -> None:
    job_id = job["id"]
    source = await db.fetchrow(
        "SELECT storage_key FROM files WHERE job_id = $1 AND role = 'source'", job_id
    )
    if source is None:
        await _fail(job_id, "conversion_failed")
        return

    try:
        data = storage.read("source", source["storage_key"])
    except (OSError, ValueError):
        await _fail(job_id, "conversion_failed")
        return

    limits = await settings_store.limits()

    try:
        result = await client.convert(
            filename=job["original_name"],
            data=data,
            mime=job["mime_type"],
            max_pages=limits["max_pages"],
        )
    except ConversionError as exc:
        if exc.code == "engine_unreachable":
            # Nicht dem Benutzer anlasten: zurück in die Warteschlange.
            await db.execute(
                "UPDATE jobs SET status = 'queued', started_at = NULL WHERE id = $1", job_id
            )
            log.warning("Docling nicht erreichbar, Job zurück in die Warteschlange")
            await asyncio.sleep(5)
            return
        await _fail(job_id, exc.code)
        log.info("Job fehlgeschlagen (%s)", exc.code)
        return

    markdown = result["markdown"]
    struktur = result["json"]

    # --- Nachbearbeitung -------------------------------------------------
    # 1) Bilder aus der Struktur loesen und als eigene Dateien ablegen.
    bilder = postprocess.bilder_ausloesen(struktur if isinstance(struktur, dict) else {})
    markdown = postprocess.markdown_bilder_verweisen(markdown, bilder)

    # 2) Verweise aus der PDF retten — Docling exportiert nur den Text.
    links = []
    if job["mime_type"] == "application/pdf":
        links = postprocess.links_lesen(data)
        markdown = postprocess.markdown_links_anhaengen(markdown, links)

    # 3) Vorlage zu grob? Dann kann die Texterkennung Zeichen verwechseln.
    hinweis = postprocess.aufloesung_pruefen(
        data, job["mime_type"], struktur if isinstance(struktur, dict) else None
    )

    # 4) Rein mechanische Schreibweisen geradeziehen (Trennzeichen in Zahlen,
    #    fehlende Leerzeichen). Keine Rechtschreibkorrektur — Tippfehler der
    #    Vorlage bleiben stehen. Nur im Markdown, die JSON bleibt unangetastet.
    markdown, geglaettet = postprocess.schreibweisen_glaetten(markdown)

    # 5) Wiederkehrende Kopf-/Fusszeilen einmal sammeln statt je Seite wiederholen.
    #    Nur im Markdown; die JSON bleibt vollstaendig.
    elemente = []
    if job["mime_type"] == "application/pdf":
        elemente = postprocess.wiederkehrende_texte(data, markdown)
        markdown = postprocess.seitenelemente_zusammenfassen(markdown, elemente)

    md_key = storage.new_key()
    json_key = storage.new_key()
    md_bytes = markdown.encode("utf-8")
    json_bytes = json.dumps(struktur, ensure_ascii=False, indent=1).encode("utf-8")
    storage.write("result", md_key, md_bytes)
    storage.write("result", json_key, json_bytes)

    await db.execute(
        "INSERT INTO files(job_id, user_id, role, storage_key, size_bytes) "
        "VALUES($1, $2, 'markdown', $3, $4) ON CONFLICT (job_id, role) DO NOTHING",
        job_id,
        job["user_id"],
        md_key,
        len(md_bytes),
    )
    await db.execute(
        "INSERT INTO files(job_id, user_id, role, storage_key, size_bytes) "
        "VALUES($1, $2, 'json', $3, $4) ON CONFLICT (job_id, role) DO NOTHING",
        job_id,
        job["user_id"],
        json_key,
        len(json_bytes),
    )
    for bild in bilder:
        key = storage.new_key()
        storage.write("result", key, bild["data"])
        await db.execute(
            "INSERT INTO job_images(job_id, user_id, seq, page_no, storage_key, "
            "                       mime_type, size_bytes) "
            "VALUES($1, $2, $3, $4, $5, $6, $7) ON CONFLICT (job_id, seq) DO NOTHING",
            job_id, job["user_id"], bild["seq"], bild.get("page_no"),
            key, bild["mime"], len(bild["data"]),
        )

    await db.execute(
        "UPDATE jobs SET status = 'done', page_count = $2, finished_at = now(), "
        "image_count = $3, link_count = $4, quality_note = $5, "
        "duration_ms = (EXTRACT(EPOCH FROM (now() - started_at)) * 1000)::int "
        "WHERE id = $1",
        job_id,
        result["pages"],
        len(bilder),
        len(links),
        hinweis,
    )
    # Der Verbrauch wurde beim Einstellen mit der geschätzten Seitenzahl gebucht.
    # Hier wird nur noch die Differenz zur tatsächlichen Seitenzahl nachgetragen.
    delta = result["pages"] - int(job["page_count"] or 0)
    if delta:
        await db.execute(
            "INSERT INTO usage_events(user_id, jobs, pages, bytes) VALUES($1, 0, $2, 0)",
            job["user_id"],
            delta,
        )
    log.info("Job fertig: %s Seiten, %s Bilder, %s Verweise, %s Schreibweisen",
             result["pages"], len(bilder), len(links), geglaettet)


async def _worker_loop(index: int, client: DoclingClient) -> None:
    pool = db.pool()
    while not _stop.is_set():
        try:
            max_active = (await settings_store.limits())["max_active_jobs"]
            async with pool.acquire() as con:
                job = await _claim_job(con, max_active)
            if job is None:
                await asyncio.wait([asyncio.create_task(_stop.wait())],
                                   timeout=CONFIG.worker_poll_seconds)
                continue
            try:
                await _process(client, job)
            except Exception:  # noqa: BLE001
                # Ein unerwarteter Fehler darf den Auftrag nicht in 'processing'
                # stehen lassen — sonst haengt er bis zum Stale-Timeout.
                log.exception("Job konnte nicht verarbeitet werden")
                await _fail(job["id"], "engine_error")
        except Exception:  # noqa: BLE001 - ein Worker darf nie sterben
            log.exception("Worker %s: unerwarteter Fehler", index)
            await asyncio.sleep(3)


# Jung genug, um noch zu einem laufenden Auftrag zu gehoeren: nicht anfassen.
VERWAIST_AB_SEKUNDEN = 3600


async def _verwaiste_dateien_entfernen() -> None:
    bekannt: dict[str, set[str]] = {"source": set(), "result": set()}
    for row in await db.fetch("SELECT role, storage_key FROM files"):
        bekannt["source" if row["role"] == "source" else "result"].add(row["storage_key"])
    for row in await db.fetch("SELECT storage_key FROM job_images"):
        bekannt["result"].add(row["storage_key"])

    entfernt = 0
    for kind in ("source", "result"):
        for key in storage.alle_schluessel(kind):
            if key in bekannt[kind]:
                continue
            if storage.alter_sekunden(kind, key) < VERWAIST_AB_SEKUNDEN:
                continue
            storage.delete(kind, key)
            entfernt += 1
    if entfernt:
        log.info("Aufraeumen: %s verwaiste Dateien entfernt", entfernt)


async def _housekeeping() -> None:
    """Retention, verwaiste Jobs, alte Sessions und Zähler."""
    while not _stop.is_set():
        try:
            # Bilder eines abgelaufenen Auftrags zuerst — sie haengen an derselben Frist.
            alte_bilder = await db.fetch(
                "SELECT b.id, b.storage_key FROM job_images b "
                "JOIN jobs j ON j.id = b.job_id "
                "WHERE j.expires_at < now() AND j.purged_at IS NULL"
            )
            for row in alte_bilder:
                storage.delete("result", row["storage_key"])
            if alte_bilder:
                await db.execute("DELETE FROM job_images WHERE id = ANY($1::bigint[])",
                                 [r["id"] for r in alte_bilder])

            expired = await db.fetch(
                "SELECT f.id, f.role, f.storage_key FROM files f "
                "JOIN jobs j ON j.id = f.job_id "
                "WHERE j.expires_at < now() AND j.purged_at IS NULL"
            )
            for row in expired:
                storage.delete(
                    "source" if row["role"] == "source" else "result", row["storage_key"]
                )
            if expired:
                await db.execute(
                    "DELETE FROM files WHERE id = ANY($1::bigint[])",
                    [r["id"] for r in expired],
                )
            await db.execute(
                "UPDATE jobs SET purged_at = now(), "
                "status = CASE WHEN status IN ('queued', 'processing') THEN 'error' ELSE status END, "
                "error_code = CASE WHEN status IN ('queued', 'processing') "
                "                  THEN 'timeout' ELSE error_code END "
                "WHERE expires_at < now() AND purged_at IS NULL"
            )
            if expired:
                log.info("Aufräumen: %s abgelaufene Dateien entfernt", len(expired))

            # Quellen entfernen, sobald ein Job fertig ist — sie werden nicht mehr gebraucht.
            done_sources = await db.fetch(
                "SELECT f.id, f.storage_key FROM files f JOIN jobs j ON j.id = f.job_id "
                "WHERE f.role = 'source' AND j.status IN ('done', 'error') "
                "AND j.finished_at < now() - interval '10 minutes'"
            )
            for row in done_sources:
                storage.delete("source", row["storage_key"])
            if done_sources:
                await db.execute(
                    "DELETE FROM files WHERE id = ANY($1::bigint[])",
                    [r["id"] for r in done_sources],
                )

            # Jobs, die ein abgestürzter Worker hängen ließ
            await db.execute(
                "UPDATE jobs SET status = 'queued', started_at = NULL "
                "WHERE status = 'processing' AND attempts < 3 "
                "AND started_at < now() - ($1 || ' minutes')::interval",
                str(CONFIG.job_stale_minutes),
            )
            await db.execute(
                "UPDATE jobs SET status = 'error', error_code = 'timeout', finished_at = now() "
                "WHERE status = 'processing' AND attempts >= 3 "
                "AND started_at < now() - ($1 || ' minutes')::interval",
                str(CONFIG.job_stale_minutes),
            )

            # Sicherheitsnetz: Dateien ohne Datenbankeintrag entfernen.
            # Sie entstehen, wenn ein Schreibvorgang durchgeht und der Eintrag
            # danach scheitert — sonst laegen sie fuer immer da und das
            # Loeschversprechen waere nicht gehalten.
            await _verwaiste_dateien_entfernen()

            await db.execute("DELETE FROM sessions WHERE expires_at < now()")
            await db.execute("DELETE FROM auth_tokens WHERE expires_at < now() - interval '7 days'")
            await db.execute("DELETE FROM audit_log WHERE created_at < now() - interval '90 days'")
            await quota.prune()
            from .security import prune_rate_limits

            await prune_rate_limits()
        except Exception:  # noqa: BLE001
            log.exception("Aufräumen fehlgeschlagen")
        await asyncio.wait([asyncio.create_task(_stop.wait())], timeout=300)


async def main() -> None:
    await db.connect()
    await db.migrate()
    storage.ensure_dirs()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _stop.set)

    client = DoclingClient()
    for _ in range(60):
        if await client.healthy():
            break
        log.info("Warte auf die Konvertierungs-Engine ...")
        await asyncio.sleep(5)

    log.info("Worker gestartet (%s parallel)", CONFIG.worker_concurrency)
    tasks = [
        asyncio.create_task(_worker_loop(i, client)) for i in range(CONFIG.worker_concurrency)
    ]
    tasks.append(asyncio.create_task(_housekeeping()))
    await asyncio.gather(*tasks, return_exceptions=True)
    await client.aclose()
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
