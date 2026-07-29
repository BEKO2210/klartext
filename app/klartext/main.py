"""Klartext — Web-Anwendung.

Alle Ressourcen sind an eine user_id gebunden und werden serverseitig geprüft.
Es gibt keine Stelle, an der eine ID allein zum Zugriff genügt.
"""

from __future__ import annotations

import asyncio
import io
import logging
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import db, mail, quota, security, settings_store, storage, uploads
from .config import CONFIG, LIMIT_DEFS
from .web_helpers import (
    CSRF_COOKIE,
    HttpProblem,
    base_context,
    client_ip,
    message_for,
    templates,
    verify_csrf,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("klartext.web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.ensure_dirs()
    await db.connect()
    await db.migrate()
    log.info("Klartext bereit")
    yield
    await db.close()


app = FastAPI(
    title="Klartext",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.mount("/static", StaticFiles(directory="klartext/static"), name="static")


# --------------------------------------------------------------------------- Middleware


SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "object-src 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


@app.middleware("http")
async def request_pipeline(request: Request, call_next):
    request.state.session = None

    if request.url.path == "/healthz":
        return await call_next(request)

    # 1) Grobes Anfragelimit pro IP
    ip = client_ip(request)
    try:
        allowed = await security.rate_limit_hit(
            f"ip:{ip}", 60, CONFIG.requests_per_minute_per_ip
        )
    except Exception:  # noqa: BLE001 - Datenbank noch nicht da: Anfrage nicht blockieren
        allowed = True
    if not allowed:
        return _plain_error(request, 429, "Zu viele Anfragen. Bitte kurz warten.")

    # 2) Session laden
    try:
        request.state.session = await security.load_session(
            request.cookies.get(CONFIG.session_cookie)
        )
    except Exception:  # noqa: BLE001
        request.state.session = None

    # 3) Body-Größe begrenzen, bevor irgendetwas gelesen wird
    if request.method in {"POST", "PUT", "PATCH"}:
        limits = await _limits_safe()
        max_body = (
            limits["max_file_size_mb"] * limits["max_files_per_upload"] + 2
        ) * 1024 * 1024
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > max_body:
            return _plain_error(request, 413, "Der Upload ist zu groß.")

    response = await call_next(request)

    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    if CONFIG.cookie_secure:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )

    fresh = getattr(request.state, "fresh_csrf", None)
    if fresh and request.state.session is None:
        _set_cookie(response, CSRF_COOKIE, fresh, http_only=False, max_age=60 * 60 * 12)
    return response


async def _limits_safe() -> dict[str, int]:
    try:
        return await settings_store.limits()
    except Exception:  # noqa: BLE001
        return dict(CONFIG.limit_env_defaults)


def _set_cookie(response: Response, name: str, value: str, *, http_only: bool, max_age: int):
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=http_only,
        secure=CONFIG.cookie_secure,
        samesite="lax",
        path="/",
    )


def _plain_error(request: Request, status: int, message: str) -> Response:
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"error": message}, status_code=status)
    return templates.TemplateResponse(
        request,
        "error.html",
        base_context(request, status=status, message=message),
        status_code=status,
    )


@app.exception_handler(HttpProblem)
async def handle_problem(request: Request, exc: HttpProblem):
    return _plain_error(request, exc.status, exc.message)


@app.exception_handler(404)
async def handle_404(request: Request, exc):  # noqa: ANN001
    return _plain_error(request, 404, "Diese Seite gibt es nicht.")


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    # Details bleiben im Log. Der Benutzer bekommt nie Stacktrace, Pfad oder Containernamen.
    log.exception("Unerwarteter Fehler auf %s", request.url.path)
    return _plain_error(
        request, 500, "Es ist ein unerwarteter Fehler aufgetreten. Bitte versuche es erneut."
    )


# --------------------------------------------------------------------------- Zugriff


def _session(request: Request):
    session = getattr(request.state, "session", None)
    if session is None:
        raise HttpProblem(401, "Bitte melde dich an.")
    return session


def _admin(request: Request):
    session = _session(request)
    if not session["is_admin"]:
        # Bewusst 404: Admin-Bereich wird für Nicht-Admins nicht einmal bestätigt.
        raise HttpProblem(404, "Diese Seite gibt es nicht.")
    return session


def _redirect_login() -> RedirectResponse:
    return RedirectResponse("/anmelden", status_code=303)


# --------------------------------------------------------------------------- Öffentlich


@app.get("/healthz")
async def healthz():
    try:
        await db.fetchval("SELECT 1")
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": "degraded"}, status_code=503)
    return {"status": "ok"}


# Öffentliche Seiten, die eine Suchmaschine sehen und indexieren darf.
# /app, /konto und /admin brauchen eine Anmeldung und liefern für Gäste ohnehin
# keinen sinnvollen Inhalt — deshalb weder in der Sitemap noch zum Crawlen frei.
_PUBLIC_PATHS = [
    "/",
    "/registrieren",
    "/anmelden",
    "/passwort-vergessen",
    "/impressum",
    "/datenschutz",
    "/nutzungsbedingungen",
    "/lizenzen",
]


@app.get("/robots.txt")
async def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /app",
        "Disallow: /konto",
        "Disallow: /admin",
        "Disallow: /api",
        "",
        f"Sitemap: {CONFIG.public_url}/sitemap.xml",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml")
async def sitemap_xml():
    urls = "".join(
        f"<url><loc>{CONFIG.public_url}{path}</loc></url>" for path in _PUBLIC_PATHS
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}"
        "</urlset>"
    )
    return Response(body, media_type="application/xml")


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    if getattr(request.state, "session", None):
        return RedirectResponse("/app", status_code=303)
    limits = await _limits_safe()
    return templates.TemplateResponse(
        request,
        "landing.html", base_context(request, limits=limits)
    )


@app.get("/registrieren", response_class=HTMLResponse)
async def register_form(request: Request):
    if getattr(request.state, "session", None):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse(
        request,
        "register.html", base_context(request))


@app.post("/registrieren", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    accept: str = Form(""),
    csrf: str = Form(""),
):
    verify_csrf(request, csrf)
    ip = client_ip(request)
    if not await security.rate_limit_hit(f"reg:{ip}", 3600, CONFIG.register_per_hour_per_ip):
        raise HttpProblem(429, "Zu viele Registrierungen von dieser Verbindung. Bitte später.")

    email = email.strip()
    problems: list[str] = []
    if not security.valid_email(email):
        problems.append("Bitte gib eine gültige E-Mail-Adresse an.")
    pw_problem = security.password_problem(password)
    if pw_problem:
        problems.append(pw_problem)
    if password != password2:
        problems.append("Die beiden Passwörter stimmen nicht überein.")
    if accept != "ja":
        problems.append("Bitte bestätige die Nutzungsbedingungen und die Datenschutzhinweise.")

    if problems:
        return templates.TemplateResponse(
        request,
        "register.html",
            base_context(request, errors=problems, email=email),
            status_code=400,
        )

    norm = security.normalize_email(email)
    password_hash = security.hash_password(password)
    is_first_user = (await db.fetchval("SELECT COUNT(*) FROM users")) == 0

    user_id = await db.fetchval(
        "INSERT INTO users(email, email_norm, password_hash, is_admin, email_verified) "
        "VALUES($1, $2, $3, $4, $5) ON CONFLICT (email_norm) DO NOTHING RETURNING id",
        email,
        norm,
        password_hash,
        is_first_user,
        not CONFIG.require_email_verification or not CONFIG.mail_configured,
    )

    if user_id is None:
        # Kein Hinweis darauf, ob die Adresse bereits existiert (keine Enumeration).
        return templates.TemplateResponse(
        request,
        "register_done.html",
            base_context(request, email=email, mail_configured=CONFIG.mail_configured),
        )

    await db.execute(
        "INSERT INTO audit_log(user_id, action) VALUES($1, 'register')", user_id
    )

    if CONFIG.require_email_verification and CONFIG.mail_configured:
        token = security.new_token()
        await db.execute(
            "INSERT INTO auth_tokens(token_hash, user_id, kind, expires_at) "
            "VALUES($1, $2, 'verify_email', now() + interval '24 hours')",
            security.token_hash(token),
            user_id,
        )
        await mail.send_verification(email, token)
        return templates.TemplateResponse(
        request,
        "register_done.html",
            base_context(request, email=email, mail_configured=True),
        )

    token, _ = await security.create_session(user_id)
    response = RedirectResponse("/app", status_code=303)
    _set_cookie(response, CONFIG.session_cookie, token, http_only=True,
                max_age=CONFIG.session_hours * 3600)
    return response


@app.get("/verify", response_class=HTMLResponse)
async def verify_email(request: Request, token: str = ""):
    row = await db.fetchrow(
        "SELECT id, user_id FROM auth_tokens "
        "WHERE token_hash = $1 AND kind = 'verify_email' "
        "AND used_at IS NULL AND expires_at > now()",
        security.token_hash(token or ""),
    )
    if row is None:
        return templates.TemplateResponse(
        request,
        "info.html",
            base_context(
                request,
                heading="Link ungültig",
                text="Dieser Bestätigungslink ist abgelaufen oder wurde bereits benutzt.",
            ),
            status_code=400,
        )
    await db.execute("UPDATE auth_tokens SET used_at = now() WHERE id = $1", row["id"])
    await db.execute("UPDATE users SET email_verified = TRUE WHERE id = $1", row["user_id"])
    return templates.TemplateResponse(
        request,
        "info.html",
        base_context(
            request,
            heading="E-Mail bestätigt",
            text="Deine Adresse ist bestätigt. Du kannst dich jetzt anmelden.",
            link="/anmelden",
            link_text="Zur Anmeldung",
        ),
    )


@app.get("/anmelden", response_class=HTMLResponse)
async def login_form(request: Request):
    if getattr(request.state, "session", None):
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html", base_context(request))


@app.post("/anmelden", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    csrf: str = Form(""),
):
    verify_csrf(request, csrf)
    norm = security.normalize_email(email)
    ip = client_ip(request)

    ok_ip = await security.rate_limit_hit(f"login-ip:{ip}", 900, CONFIG.login_attempts_per_15min * 3)
    ok_account = await security.rate_limit_hit(
        f"login-acct:{norm}", 900, CONFIG.login_attempts_per_15min
    )
    if not (ok_ip and ok_account):
        raise HttpProblem(
            429, "Zu viele Anmeldeversuche. Bitte warte 15 Minuten und versuche es erneut."
        )

    row = await db.fetchrow(
        "SELECT id, password_hash, is_active, email_verified FROM users WHERE email_norm = $1",
        norm,
    )
    ok, new_hash = security.verify_password(row["password_hash"] if row else None, password)

    if not ok or row is None:
        return templates.TemplateResponse(
        request,
        "login.html",
            base_context(
                request,
                errors=["E-Mail-Adresse oder Passwort stimmt nicht."],
                email=email,
            ),
            status_code=401,
        )
    if not row["is_active"]:
        return templates.TemplateResponse(
        request,
        "login.html",
            base_context(request, errors=["Dieses Konto ist deaktiviert."], email=email),
            status_code=403,
        )
    if CONFIG.require_email_verification and CONFIG.mail_configured and not row["email_verified"]:
        return templates.TemplateResponse(
        request,
        "login.html",
            base_context(
                request,
                errors=["Bitte bestätige zuerst deine E-Mail-Adresse über den Link, "
                        "den wir dir geschickt haben."],
                email=email,
            ),
            status_code=403,
        )

    if new_hash:
        await db.execute("UPDATE users SET password_hash = $1 WHERE id = $2", new_hash, row["id"])

    # Session-Rotation: alte Sessions dieses Kontos bleiben bestehen, aber die
    # Anmeldung erzeugt immer ein frisches Token (kein Session Fixation).
    await security.rate_limit_reset(f"login-acct:{norm}")
    await db.execute("UPDATE users SET last_login_at = now() WHERE id = $1", row["id"])
    token, _ = await security.create_session(row["id"])
    response = RedirectResponse("/app", status_code=303)
    _set_cookie(response, CONFIG.session_cookie, token, http_only=True,
                max_age=CONFIG.session_hours * 3600)
    response.delete_cookie(CSRF_COOKIE, path="/")
    return response


@app.post("/abmelden")
async def logout(request: Request, csrf: str = Form("")):
    verify_csrf(request, csrf)
    await security.destroy_session(request.cookies.get(CONFIG.session_cookie))
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(CONFIG.session_cookie, path="/")
    return response


@app.get("/passwort-vergessen", response_class=HTMLResponse)
async def forgot_form(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot.html", base_context(request, mail_configured=CONFIG.mail_configured)
    )


@app.post("/passwort-vergessen", response_class=HTMLResponse)
async def forgot_submit(request: Request, email: str = Form(""), csrf: str = Form("")):
    verify_csrf(request, csrf)
    ip = client_ip(request)
    if not await security.rate_limit_hit(f"forgot:{ip}", 3600, 5):
        raise HttpProblem(429, "Zu viele Anfragen. Bitte später noch einmal.")

    norm = security.normalize_email(email)
    row = await db.fetchrow("SELECT id, email FROM users WHERE email_norm = $1 AND is_active", norm)
    if row is not None and CONFIG.mail_configured:
        token = security.new_token()
        await db.execute(
            "INSERT INTO auth_tokens(token_hash, user_id, kind, expires_at) "
            "VALUES($1, $2, 'password_reset', now() + interval '1 hour')",
            security.token_hash(token),
            row["id"],
        )
        await mail.send_password_reset(row["email"], token)

    # Immer dieselbe Antwort — keine Auskunft darüber, ob es das Konto gibt.
    return templates.TemplateResponse(
        request,
        "info.html",
        base_context(
            request,
            heading="E-Mail unterwegs",
            text="Falls es zu dieser Adresse ein Konto gibt, ist eine E-Mail mit einem "
            "Link zum Zurücksetzen unterwegs. Der Link gilt eine Stunde.",
            link="/anmelden",
            link_text="Zur Anmeldung",
        ),
    )


@app.get("/passwort-neu", response_class=HTMLResponse)
async def reset_form(request: Request, token: str = ""):
    return templates.TemplateResponse(
        request,
        "reset.html", base_context(request, token=token))


@app.post("/passwort-neu", response_class=HTMLResponse)
async def reset_submit(
    request: Request,
    token: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    csrf: str = Form(""),
):
    verify_csrf(request, csrf)
    problems = []
    pw_problem = security.password_problem(password)
    if pw_problem:
        problems.append(pw_problem)
    if password != password2:
        problems.append("Die beiden Passwörter stimmen nicht überein.")
    if problems:
        return templates.TemplateResponse(
        request,
        "reset.html",
            base_context(request, token=token, errors=problems),
            status_code=400,
        )

    row = await db.fetchrow(
        "SELECT id, user_id FROM auth_tokens WHERE token_hash = $1 AND kind = 'password_reset' "
        "AND used_at IS NULL AND expires_at > now()",
        security.token_hash(token),
    )
    if row is None:
        return templates.TemplateResponse(
        request,
        "reset.html",
            base_context(
                request,
                token="",
                errors=["Dieser Link ist abgelaufen oder wurde bereits benutzt."],
            ),
            status_code=400,
        )

    await db.execute("UPDATE auth_tokens SET used_at = now() WHERE id = $1", row["id"])
    await db.execute(
        "UPDATE users SET password_hash = $1, email_verified = TRUE WHERE id = $2",
        security.hash_password(password),
        row["user_id"],
    )
    # Alle bestehenden Sitzungen beenden — auch die eines möglichen Angreifers.
    await security.destroy_all_sessions(row["user_id"])
    await db.execute(
        "INSERT INTO audit_log(user_id, action) VALUES($1, 'password_reset')", row["user_id"]
    )
    return templates.TemplateResponse(
        request,
        "info.html",
        base_context(
            request,
            heading="Passwort geändert",
            text="Du kannst dich jetzt mit dem neuen Passwort anmelden.",
            link="/anmelden",
            link_text="Zur Anmeldung",
        ),
    )


# --------------------------------------------------------------------------- Dashboard


@app.get("/app", response_class=HTMLResponse)
async def dashboard(request: Request):
    session = getattr(request.state, "session", None)
    if session is None:
        return _redirect_login()
    limits = await settings_store.limits()
    usage = await quota.current_usage(session["user_id"])
    jobs = await _jobs_for(session["user_id"])
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        base_context(request, jobs=jobs, limits=limits, usage=usage),
    )


async def _jobs_for(user_id: int, limit: int = 60) -> list[dict]:
    rows = await db.fetch(
        "SELECT public_id, original_name, mime_type, size_bytes, status, error_code, "
        "       page_count, created_at, started_at, finished_at, duration_ms, expires_at, "
        "       (SELECT COUNT(*) FROM jobs q WHERE q.status = 'queued' "
        "         AND q.created_at < jobs.created_at) AS ahead "
        "FROM jobs WHERE user_id = $1 AND status <> 'deleted' "
        "ORDER BY created_at DESC LIMIT $2",
        user_id,
        limit,
    )
    return [
        {
            "id": str(r["public_id"]),
            "name": storage.display_name(r["original_name"]),
            "size": r["size_bytes"],
            "status": r["status"],
            "error": message_for(r["error_code"]) if r["error_code"] else None,
            "pages": r["page_count"],
            "created_at": r["created_at"].isoformat(),
            "started_at": r["started_at"].isoformat() if r["started_at"] else None,
            # Wie viele Auftraege stehen noch davor — fuer eine ehrliche Wartenanzeige.
            "ahead": int(r["ahead"]) if r["status"] == "queued" else 0,
            "duration_ms": r["duration_ms"],
            "expires_at": r["expires_at"].isoformat(),
        }
        for r in rows
    ]


@app.get("/api/jobs")
async def api_jobs(request: Request):
    session = _session(request)
    # Verbrauch mitliefern: die Zeile im Dashboard wird sonst nur beim
    # Seitenaufruf gesetzt und zeigt nach einem Upload veraltete Zahlen.
    limits = await settings_store.limits()
    usage = await quota.current_usage(session["user_id"])
    return {
        "jobs": await _jobs_for(session["user_id"]),
        "usage": {
            "jobs_day": usage.jobs_day,
            "pages_day": usage.pages_day,
            "active": usage.active,
            "queued": usage.queued,
        },
        "limits": {
            "jobs_per_day": limits["jobs_per_day"],
            "pages_per_day": limits["pages_per_day"],
        },
    }


@app.post("/app/upload")
async def upload(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    csrf: str = Form(""),
):
    session = _session(request)
    verify_csrf(request, csrf)
    user_id = session["user_id"]
    limits = await settings_store.limits()

    incoming = [f for f in files if f.filename]
    if not incoming:
        raise HttpProblem(400, message_for("no_files"))
    if len(incoming) > limits["max_files_per_upload"]:
        raise HttpProblem(400, message_for("too_many_files"))

    max_bytes = limits["max_file_size_mb"] * 1024 * 1024
    prepared: list[dict] = []
    total_bytes = 0
    est_pages = 0

    async with _upload_slots:
        for item in incoming:
            data = await item.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise HttpProblem(413, message_for("file_too_large"))
            try:
                mime, _label = uploads.check(item.filename, data)
            except uploads.RejectedUpload as exc:
                raise HttpProblem(400, message_for(exc.code)) from None

            pages = 1
            if mime == "application/pdf":
                counted = uploads.pdf_page_count(data)
                if counted is None:
                    raise HttpProblem(400, message_for("encrypted_pdf"))
                if counted > limits["max_pages"]:
                    raise HttpProblem(400, message_for("too_many_pages"))
                pages = counted

            total_bytes += len(data)
            est_pages += pages
            prepared.append({"name": item.filename, "data": data,
                             "mime": mime, "pages": pages})

    try:
        await quota.check_batch(user_id, len(prepared), total_bytes, est_pages)
    except quota.QuotaExceeded as exc:
        raise HttpProblem(429, message_for(exc.code)) from None

    batch_id = uuid.uuid4()
    retention = timedelta(hours=limits["retention_hours"])
    created = 0

    for entry in prepared:
        key = storage.new_key()
        storage.write("source", key, entry["data"])
        job_id = await db.fetchval(
            "INSERT INTO jobs(public_id, batch_id, user_id, original_name, mime_type, "
            "                 size_bytes, page_count, expires_at) "
            "VALUES($1, $2, $3, $4, $5, $6, $7, now() + $8::interval) RETURNING id",
            uuid.uuid4(),
            batch_id,
            user_id,
            entry["name"][:250],
            entry["mime"],
            len(entry["data"]),
            entry["pages"],
            retention,
        )
        await db.execute(
            "INSERT INTO files(job_id, user_id, role, storage_key, size_bytes) "
            "VALUES($1, $2, 'source', $3, $4)",
            job_id,
            user_id,
            key,
            len(entry["data"]),
        )
        # Verbrauch wird beim Einstellen gezählt, nicht erst bei Erfolg — sonst
        # könnte man das Kontingent durch absichtlich fehlschlagende Aufträge umgehen.
        await quota.record(user_id, entry["pages"], len(entry["data"]))
        created += 1

    return JSONResponse({"ok": True, "created": created, "batch": str(batch_id)})


# Uploads werden zum Prüfen vollständig in den Speicher gelesen. Ohne Bremse
# könnten mehrere gleichzeitige große Uploads den Web-Container an sein
# Speicherlimit treiben; deshalb höchstens zwei parallel.
_upload_slots = asyncio.Semaphore(2)


async def _owned_job(user_id: int, public_id: str):
    """Lädt einen Job — immer mit user_id in der Bedingung."""
    try:
        job_uuid = uuid.UUID(public_id)
    except (ValueError, AttributeError):
        raise HttpProblem(404, "Dieser Auftrag existiert nicht.") from None
    row = await db.fetchrow(
        "SELECT id, public_id, original_name, status, error_code, page_count, size_bytes, "
        "       created_at, duration_ms, expires_at "
        "FROM jobs WHERE public_id = $1 AND user_id = $2 AND status <> 'deleted'",
        job_uuid,
        user_id,
    )
    if row is None:
        # Gleiche Antwort für 'gibt es nicht' und 'gehört jemand anderem'.
        raise HttpProblem(404, "Dieser Auftrag existiert nicht.")
    return row


@app.get("/app/auftrag/{public_id}", response_class=HTMLResponse)
async def job_detail(request: Request, public_id: str):
    session = getattr(request.state, "session", None)
    if session is None:
        return _redirect_login()
    job = await _owned_job(session["user_id"], public_id)

    markdown = None
    if job["status"] == "done":
        row = await db.fetchrow(
            "SELECT storage_key FROM files WHERE job_id = $1 AND role = 'markdown'", job["id"]
        )
        if row:
            try:
                markdown = storage.read("result", row["storage_key"]).decode("utf-8")
            except (OSError, ValueError):
                markdown = None

    return templates.TemplateResponse(
        request,
        "job.html",
        base_context(
            request,
            job={
                "id": str(job["public_id"]),
                "name": storage.display_name(job["original_name"]),
                "status": job["status"],
                "error": message_for(job["error_code"]) if job["error_code"] else None,
                "pages": job["page_count"],
                "size": job["size_bytes"],
                "duration_ms": job["duration_ms"],
                "expires_at": job["expires_at"],
            },
            markdown=markdown,
        ),
    )


_DOWNLOAD_ROLES = {
    "md": ("markdown", ".md", "text/markdown; charset=utf-8"),
    "json": ("json", ".json", "application/json; charset=utf-8"),
}


@app.get("/app/auftrag/{public_id}/download/{fmt}")
async def download(request: Request, public_id: str, fmt: str):
    session = _session(request)
    if fmt not in _DOWNLOAD_ROLES:
        raise HttpProblem(404, "Dieses Format gibt es nicht.")
    role, suffix, content_type = _DOWNLOAD_ROLES[fmt]

    job = await _owned_job(session["user_id"], public_id)
    row = await db.fetchrow(
        "SELECT storage_key FROM files WHERE job_id = $1 AND role = $2 AND user_id = $3",
        job["id"],
        role,
        session["user_id"],
    )
    if row is None:
        raise HttpProblem(404, "Das Ergebnis ist nicht (mehr) verfügbar.")
    try:
        data = storage.read("result", row["storage_key"])
    except (OSError, ValueError):
        raise HttpProblem(404, "Das Ergebnis ist nicht mehr verfügbar.") from None

    name = storage.safe_download_name(job["original_name"], suffix)
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/app/download/zip")
async def download_zip(request: Request, ids: str = ""):
    session = _session(request)
    wanted = [part for part in ids.split(",") if part][:50]
    if not wanted:
        raise HttpProblem(400, "Es wurden keine Ergebnisse ausgewählt.")

    buffer = io.BytesIO()
    used: set[str] = set()
    count = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for public_id in wanted:
            try:
                job = await _owned_job(session["user_id"], public_id)
            except HttpProblem:
                continue
            if job["status"] != "done":
                continue
            rows = await db.fetch(
                "SELECT role, storage_key FROM files "
                "WHERE job_id = $1 AND user_id = $2 AND role IN ('markdown', 'json')",
                job["id"],
                session["user_id"],
            )
            for row in rows:
                suffix = ".md" if row["role"] == "markdown" else ".json"
                # Namen im Archiv werden von uns erzeugt, nie vom Benutzer übernommen.
                name = storage.safe_download_name(job["original_name"], suffix)
                base, dot, ext = name.rpartition(".")
                counter = 1
                while name in used:
                    name = f"{base}-{counter}{dot}{ext}"
                    counter += 1
                used.add(name)
                try:
                    archive.writestr(name, storage.read("result", row["storage_key"]))
                    count += 1
                except (OSError, ValueError):
                    continue

    if count == 0:
        raise HttpProblem(404, "Es gibt keine fertigen Ergebnisse zum Herunterladen.")

    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="klartext-ergebnisse.zip"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post("/app/auftrag/{public_id}/loeschen")
async def delete_job(request: Request, public_id: str, csrf: str = Form("")):
    session = _session(request)
    verify_csrf(request, csrf)
    job = await _owned_job(session["user_id"], public_id)

    rows = await db.fetch(
        "SELECT role, storage_key FROM files WHERE job_id = $1 AND user_id = $2",
        job["id"],
        session["user_id"],
    )
    for row in rows:
        storage.delete("source" if row["role"] == "source" else "result", row["storage_key"])
    await db.execute("DELETE FROM files WHERE job_id = $1", job["id"])
    await db.execute(
        "UPDATE jobs SET status = 'deleted', purged_at = now() WHERE id = $1", job["id"]
    )
    return RedirectResponse("/app", status_code=303)


# --------------------------------------------------------------------------- Konto


@app.get("/konto", response_class=HTMLResponse)
async def account(request: Request):
    session = getattr(request.state, "session", None)
    if session is None:
        return _redirect_login()
    limits = await settings_store.limits()
    usage = await quota.current_usage(session["user_id"])
    return templates.TemplateResponse(
        request,
        "account.html", base_context(request, limits=limits, usage=usage)
    )


@app.post("/konto/passwort", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    csrf: str = Form(""),
):
    session = _session(request)
    verify_csrf(request, csrf)

    row = await db.fetchrow("SELECT password_hash FROM users WHERE id = $1", session["user_id"])
    ok, _ = security.verify_password(row["password_hash"] if row else None, current)

    problems = []
    if not ok:
        problems.append("Das aktuelle Passwort stimmt nicht.")
    pw_problem = security.password_problem(password)
    if pw_problem:
        problems.append(pw_problem)
    if password != password2:
        problems.append("Die beiden neuen Passwörter stimmen nicht überein.")

    if problems:
        limits = await settings_store.limits()
        usage = await quota.current_usage(session["user_id"])
        return templates.TemplateResponse(
        request,
        "account.html",
            base_context(request, errors=problems, limits=limits, usage=usage),
            status_code=400,
        )

    await db.execute(
        "UPDATE users SET password_hash = $1 WHERE id = $2",
        security.hash_password(password),
        session["user_id"],
    )
    await security.destroy_all_sessions(session["user_id"])
    await db.execute(
        "INSERT INTO audit_log(user_id, action) VALUES($1, 'password_change')", session["user_id"]
    )
    token, _ = await security.create_session(session["user_id"])
    response = RedirectResponse("/konto?geaendert=1", status_code=303)
    _set_cookie(response, CONFIG.session_cookie, token, http_only=True,
                max_age=CONFIG.session_hours * 3600)
    return response


@app.post("/konto/loeschen")
async def delete_account(request: Request, confirm: str = Form(""), csrf: str = Form("")):
    session = _session(request)
    verify_csrf(request, csrf)
    # Beide Schreibweisen akzeptieren — auf Handytastaturen ist das Ö umständlich.
    if confirm.strip().upper() not in {"LÖSCHEN", "LOESCHEN"}:
        raise HttpProblem(400, "Zur Bestätigung muss LÖSCHEN eingegeben werden.")

    rows = await db.fetch(
        "SELECT role, storage_key FROM files WHERE user_id = $1", session["user_id"]
    )
    for row in rows:
        storage.delete("source" if row["role"] == "source" else "result", row["storage_key"])
    # users kaskadiert auf sessions, jobs, files, usage_events, auth_tokens.
    await db.execute("DELETE FROM users WHERE id = $1", session["user_id"])
    await db.execute("INSERT INTO audit_log(action) VALUES('account_deleted')")

    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(CONFIG.session_cookie, path="/")
    return response


# --------------------------------------------------------------------------- Admin


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    # Auch ohne Anmeldung 404 statt Weiterleitung: eine Weiterleitung wuerde
    # bestaetigen, dass es diesen Bereich ueberhaupt gibt.
    session = getattr(request.state, "session", None)
    if session is None or not session["is_admin"]:
        raise HttpProblem(404, "Diese Seite gibt es nicht.")

    users = await db.fetch(
        "SELECT u.id, u.email, u.is_admin, u.is_active, u.email_verified, u.created_at, "
        "       u.last_login_at, "
        "       (SELECT COUNT(*) FROM jobs j WHERE j.user_id = u.id "
        "         AND j.status <> 'deleted') AS job_count "
        "FROM users u ORDER BY u.created_at DESC LIMIT 200"
    )
    stats = await db.fetchrow(
        "SELECT "
        " (SELECT COUNT(*) FROM jobs WHERE status = 'queued')     AS queued, "
        " (SELECT COUNT(*) FROM jobs WHERE status = 'processing') AS processing, "
        " (SELECT COUNT(*) FROM jobs WHERE status = 'done' "
        "    AND created_at > now() - interval '1 day')           AS done_day, "
        " (SELECT COUNT(*) FROM jobs WHERE status = 'error' "
        "    AND created_at > now() - interval '1 day')           AS error_day, "
        " (SELECT COALESCE(AVG(duration_ms), 0) FROM jobs WHERE status = 'done' "
        "    AND finished_at > now() - interval '1 day')          AS avg_ms, "
        " (SELECT COUNT(*) FROM users)                            AS user_count"
    )
    failed = await db.fetch(
        "SELECT public_id, error_code, created_at, user_id FROM jobs "
        "WHERE status = 'error' ORDER BY created_at DESC LIMIT 20"
    )
    return templates.TemplateResponse(
        request,
        "admin.html",
        base_context(
            request,
            users=users,
            user_id=session["user_id"],
            stats=stats,
            failed=failed,
            limits=await settings_store.limits(),
            limit_defs=LIMIT_DEFS,
        ),
    )


@app.post("/admin/limits")
async def admin_limits(request: Request):
    _admin(request)
    form = await request.form()
    verify_csrf(request, form.get("csrf"))
    for key in LIMIT_DEFS:
        raw = form.get(key)
        if raw is None:
            continue
        try:
            await settings_store.set_limit(key, int(str(raw)))
        except (ValueError, KeyError):
            continue
    return RedirectResponse("/admin?gespeichert=1", status_code=303)


@app.post("/admin/nutzer/{user_id}/status")
async def admin_toggle_user(request: Request, user_id: int, csrf: str = Form("")):
    session = _admin(request)
    verify_csrf(request, csrf)
    if user_id == session["user_id"]:
        raise HttpProblem(400, "Das eigene Konto kann hier nicht deaktiviert werden.")
    active = await db.fetchval(
        "UPDATE users SET is_active = NOT is_active WHERE id = $1 RETURNING is_active", user_id
    )
    if active is False:
        await security.destroy_all_sessions(user_id)
    await db.execute(
        "INSERT INTO audit_log(user_id, action, detail) VALUES($1, 'admin_toggle_user', $2)",
        session["user_id"],
        str(user_id),
    )
    return RedirectResponse("/admin", status_code=303)


# --------------------------------------------------------------------------- Rechtliches


@app.get("/impressum", response_class=HTMLResponse)
async def imprint(request: Request):
    return templates.TemplateResponse(
        request,
        "legal_imprint.html", base_context(request, cfg=CONFIG))


@app.get("/datenschutz", response_class=HTMLResponse)
async def privacy(request: Request):
    limits = await _limits_safe()
    return templates.TemplateResponse(
        request,
        "legal_privacy.html", base_context(request, cfg=CONFIG, limits=limits)
    )


@app.get("/nutzungsbedingungen", response_class=HTMLResponse)
async def terms(request: Request):
    limits = await _limits_safe()
    return templates.TemplateResponse(
        request,
        "legal_terms.html", base_context(request, cfg=CONFIG, limits=limits)
    )


@app.get("/lizenzen", response_class=HTMLResponse)
async def licenses(request: Request):
    import pathlib

    path = pathlib.Path("/srv/THIRD_PARTY_LICENSES.md")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return templates.TemplateResponse(
        request,
        "legal_licenses.html", base_context(request, licenses_text=text)
    )
