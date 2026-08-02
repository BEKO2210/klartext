"""Klartext — Web-Anwendung.

Alle Ressourcen sind an eine user_id gebunden und werden serverseitig geprüft.
Es gibt keine Stelle, an der eine ID allein zum Zugriff genügt.

Sprachen: Englisch liegt auf den blanken Pfaden, Deutsch unter /de. Welche
Fassung ausgeliefert wird, entscheidet die Middleware — siehe i18n.py.
"""

from __future__ import annotations

import asyncio
import datetime
import io
import json
import logging
import pathlib
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import db, i18n, mail, quota, security, settings_store, storage, uploads
from .config import CONFIG, LIMIT_DEFS
from .i18n import APP_PATHS as AP
from .i18n import PATHS as P
from .web_helpers import (
    CSRF_COOKIE,
    HttpProblem,
    base_context,
    client_ip,
    lang_of,
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
class _StaticMitLangemCache(StaticFiles):
    """Statische Dateien ein Jahr cachebar machen.

    Jede Referenz traegt eine Inhalts-Kennung (?v=<hash>, siehe asset() in
    web_helpers). Eine geaenderte Datei bekommt eine neue Adresse — die alte
    darf also unbegrenzt im Cache liegen. Ohne diesen Header gilt der
    Cloudflare-Standard von vier Stunden, und jeder Besucher laedt die
    unveraenderten Dateien alle vier Stunden neu.
    """

    async def get_response(self, path, scope):
        antwort = await super().get_response(path, scope)
        if antwort.status_code == 200:
            antwort.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return antwort


app.mount("/static", _StaticMitLangemCache(directory="klartext/static"), name="static")


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

_LANG_COOKIE_JAHR = 365 * 24 * 3600


def _mit_query(request: Request, pfad: str, ohne: str = "") -> str:
    paare = [(k, v) for k, v in request.query_params.multi_items() if k != ohne]
    return f"{pfad}?{urlencode(paare)}" if paare else pfad


@app.middleware("http")
async def request_pipeline(request: Request, call_next):
    request.state.session = None
    request.state.lang = i18n.DEFAULT_LANG
    pfad = request.url.path

    if pfad == "/healthz":
        return await call_next(request)

    # 0) Alte deutsche Adressen. Sie standen ein Jahr lang in Suchtreffern und
    #    fremden Verweisen; deshalb dauerhaft weiterleiten statt fallen lassen.
    #    Bei Formularen 308, sonst ginge die Methode samt Rumpf verloren.
    alt = i18n.legacy_target(pfad)
    if alt is not None:
        code = 301 if request.method in {"GET", "HEAD"} else 308
        return RedirectResponse(_mit_query(request, alt), status_code=code)

    # 1) Grobes Anfragelimit pro IP
    ip = client_ip(request)
    try:
        allowed = await security.rate_limit_hit(
            f"ip:{ip}", 60, CONFIG.requests_per_minute_per_ip
        )
    except Exception:  # noqa: BLE001 - Datenbank noch nicht da: Anfrage nicht blockieren
        allowed = True
    if not allowed:
        return _plain_error(request, 429, "error.rate_limited")

    # 2) Sprache bestimmen
    gewuenscht = i18n.normalize(request.query_params.get("lang"))
    cookie_sprache = i18n.normalize(request.cookies.get(i18n.LANG_COOKIE))
    pfad_sprache = i18n.lang_from_path(pfad)
    browser_sprache = i18n.preferred_from_header(request.headers.get("accept-language", ""))
    request.state.lang = pfad_sprache or cookie_sprache or browser_sprache

    # Ausdrueckliche Wahl über den Umschalter: merken und auf die Fassung in der
    # gewaehlten Sprache schicken. Ohne das Merken wuerde die Umleitung nach
    # Browsersprache die Wahl beim naechsten Aufruf sofort wieder umwerfen.
    if gewuenscht and request.method in {"GET", "HEAD"}:
        ziel = _mit_query(request, i18n.twin(pfad, gewuenscht), ohne="lang")
        antwort = RedirectResponse(ziel, status_code=303)
        _set_cookie(antwort, i18n.LANG_COOKIE, gewuenscht,
                    http_only=False, max_age=_LANG_COOKIE_JAHR)
        return antwort

    # Englisch ist die Standardfassung. Wer laut Browser Deutsch bevorzugt und
    # noch nichts gewaehlt hat, landet einmalig auf der deutschen Fassung.
    if (
        request.method in {"GET", "HEAD"}
        and pfad_sprache == "en"
        and cookie_sprache is None
        and browser_sprache == "de"
    ):
        antwort = RedirectResponse(_mit_query(request, i18n.twin(pfad, "de")), status_code=302)
        antwort.headers["Vary"] = "Accept-Language, Cookie"
        return antwort

    # 3) Session laden
    try:
        request.state.session = await security.load_session(
            request.cookies.get(CONFIG.session_cookie)
        )
    except Exception:  # noqa: BLE001
        request.state.session = None

    # 4) Body-Größe begrenzen, bevor irgendetwas gelesen wird
    if request.method in {"POST", "PUT", "PATCH"}:
        limits = await _limits_safe()
        max_body = (
            limits["max_file_size_mb"] * limits["max_files_per_upload"] + 2
        ) * 1024 * 1024
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > max_body:
            return _plain_error(request, 413, "error.upload_too_large")

    response = await call_next(request)

    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    if CONFIG.cookie_secure:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    # Dieselbe Adresse kann je nach Browsersprache und Sprachcookie
    # unterschiedlich ausfallen. Ohne diesen Hinweis liefern Zwischenspeicher
    # die zuerst gesehene Fassung an alle weiteren Besucher aus.
    if response.headers.get("content-type", "").startswith("text/html"):
        response.headers.setdefault("Vary", "Accept-Language, Cookie")

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


def _plain_error(request: Request, status: int, key: str, **werte) -> Response:
    lang = lang_of(request)
    message = i18n.translate(lang, key, **werte)
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
    return _plain_error(request, exc.status, exc.key, **exc.werte)


@app.exception_handler(404)
async def handle_404(request: Request, exc):  # noqa: ANN001
    return _plain_error(request, 404, "error.not_found")


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    # Details bleiben im Log. Der Benutzer bekommt nie Stacktrace, Pfad oder Containernamen.
    log.exception("Unerwarteter Fehler auf %s", request.url.path)
    return _plain_error(request, 500, "error.unexpected")


# --------------------------------------------------------------------------- Zugriff


def _session(request: Request):
    session = getattr(request.state, "session", None)
    if session is None:
        raise HttpProblem(401, "error.login_required")
    return session


def _admin(request: Request):
    session = _session(request)
    if not session["is_admin"]:
        # Bewusst 404: Admin-Bereich wird für Nicht-Admins nicht einmal bestätigt.
        raise HttpProblem(404, "error.not_found")
    return session


def _redirect_login(request: Request) -> RedirectResponse:
    return RedirectResponse(i18n.path_for("login", lang_of(request)), status_code=303)


def _passwort_problem(request: Request, password: str) -> str | None:
    key = security.password_problem(password)
    if key is None:
        return None
    return i18n.translate(lang_of(request), key, min=security.MIN_PASSWORD_LEN)


# --------------------------------------------------------------------------- Öffentlich


@app.get("/healthz")
async def healthz():
    try:
        await db.fetchval("SELECT 1")
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": "degraded"}, status_code=503)
    return {"status": "ok"}


# --- Reichweitenmessung ------------------------------------------------------
#
# Das Zaehlskript und der Zaehlaufruf laufen ueber die eigene Domain. Sonst
# muesste die Inhaltsrichtlinie einen fremden Rechnernamen erlauben, in der Seite
# staende ein Fremd-Request, und die ueblichen Werbeblocker wuerden ihn ohnehin
# unterbinden. Weitergereicht wird nur an die fest eingestellte Adresse.

_MESSUNG_SKRIPT: bytes | None = None


@app.get("/js/script.js")
async def messung_skript():
    if not CONFIG.messung_aktiv:
        raise HttpProblem(404, "error.file_missing")
    global _MESSUNG_SKRIPT
    if _MESSUNG_SKRIPT is None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                antwort = await client.get(f"{CONFIG.plausible_url}/js/script.js")
            antwort.raise_for_status()
            _MESSUNG_SKRIPT = antwort.content
        except Exception:  # noqa: BLE001 - die Seite darf daran nicht scheitern
            log.warning("Zaehlskript nicht erreichbar")
            # Auf keinen Fall zwischenspeichern lassen: Cloudflare haelt
            # JavaScript vier Stunden fest, und eine einmal ausgelieferte leere
            # Antwort bliebe so lange haengen.
            return Response(content=b"", media_type="application/javascript",
                            headers={"Cache-Control": "no-store"})
    return Response(
        content=_MESSUNG_SKRIPT,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.post("/api/event")
async def messung_ereignis(request: Request):
    if not CONFIG.messung_aktiv:
        raise HttpProblem(404, "error.address_missing")
    rumpf = await request.body()
    if len(rumpf) > 4096:
        raise HttpProblem(400, "error.request_too_large")
    # Die echte Besucheradresse weiterreichen, sonst zaehlt Plausible alle
    # Aufrufe als denselben Besucher. Cloudflare stellt sie in diesem Kopffeld
    # bereit; sie wird von Plausible nur als taeglich wechselnder Hashwert
    # gespeichert, nie im Klartext.
    quelle = request.headers.get("cf-connecting-ip") or (
        request.client.host if request.client else "")
    kopf = {
        "Content-Type": "application/json",
        "User-Agent": request.headers.get("user-agent", ""),
    }
    if quelle:
        kopf["X-Forwarded-For"] = quelle
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{CONFIG.plausible_url}/api/event",
                              content=rumpf, headers=kopf)
    except Exception:  # noqa: BLE001 - Messung darf nie stoeren
        pass
    return Response(status_code=202)


@app.get("/robots.txt")
async def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        # Der Zaehlaufruf der Reichweitenmessung ist ausdruecklich erlaubt:
        # sonst meldet die Search Console beim Rendern "durch robots.txt
        # blockiert". Plausible verwirft Bot-Aufrufe am User-Agent, die
        # Statistik bleibt davon sauber. Die spezifischere Regel gewinnt.
        "Allow: /api/event",
        "Disallow: /app",
        "Disallow: /account",
        "Disallow: /admin",
        "Disallow: /api",
        "",
        f"Sitemap: {CONFIG.public_url}/sitemap.xml",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain; charset=utf-8")


# IndexNow-Schluessel: absichtlich oeffentlich — die Datei beweist nur, dass
# wir diese Domain kontrollieren. Bing/Yandex holen sie bei jedem Ping ab.
# Melden neuer Adressen: scripts/indexnow.sh nach jedem inhaltlichen Deploy.
INDEXNOW_KEY = "83c7219232f501978ffcc4bcdc3a1acb"


@app.get(f"/{INDEXNOW_KEY}.txt")
async def indexnow_key():
    return Response(INDEXNOW_KEY + "\n", media_type="text/plain; charset=utf-8")


@app.get("/BingSiteAuth.xml")
async def bing_site_auth():
    """Inhaberschafts-Nachweis fuer Bing Webmaster Tools (Belkis' Konto).

    Der Wert ist oeffentlich gedacht — er beweist nur, dass der Kontoinhaber
    diese Domain kontrolliert. ChatGPT und Copilot antworten aus dem
    Bing-Index; die Anmeldung dort ist der Weg hinein.
    """
    return Response(
        '<?xml version="1.0"?>\n<users>\n'
        "\t<user>9EE5BAA098BF9E682F3870DECA601973</user>\n"
        "</users>\n",
        media_type="text/xml; charset=utf-8",
    )


@app.get("/llms.txt")
async def llms_txt():
    """Kurzuebersicht fuer KI-Werkzeuge, die llms.txt lesen.

    Google ignoriert die Datei; einige Assistenten und Crawler nutzen sie als
    Inhaltsverzeichnis. Nur Fakten, die auch auf den Seiten selbst stehen.
    """
    u = CONFIG.public_url
    text = f"""# Klartext

> Free web service that converts PDF, photos, scans, Word, Excel and PowerPoint
> files into clean Markdown and structure-faithful JSON. Runs entirely on a
> single server in Germany — documents are never passed to external AI or OCR
> services and are deleted automatically after 24 hours. No tiers, no payment.

Key facts:
- 11 input formats (PDF, DOCX, XLSX, PPTX, HTML, BMP, JPEG, JPG, PNG, TIF/TIFF, WEBP, MD)
- OCR for scans and photos runs locally (RapidOCR; benchmark on the start page)
- Output: one .md file to read and reuse, one .json file with the full structure
- Free for good — same fair-use limits for everyone
- GDPR-friendly: processing exclusively on our own server in Germany

## Pages

- [Start (English)]({u}/): what it does, honest OCR benchmark, FAQ
- [Start (German)]({u}/de): German version
- [Comparison]({u}/compare): Klartext vs pandoc, Docling, Marker and cloud
  converters — factual, including when another tool is the better choice
- [Vergleich (German)]({u}/de/vergleich)
- [Privacy]({u}/privacy) · [Imprint]({u}/imprint) · [Licences]({u}/licenses)

## Notes for AI assistants

- Content may be cited with attribution and a link ({u}).
- Training on this content is not permitted (see robots.txt content signals).
- User-uploaded documents are not public and never appear on these pages.
"""
    return Response(text, media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml")
async def sitemap_xml():
    """Beide Sprachfassungen, jeweils mit Verweis auf die andere.

    Ohne die Verweise behandelt eine Suchmaschine /login und /de/anmelden als
    zwei konkurrierende Seiten statt als dieselbe Seite in zwei Sprachen.
    """
    stuecke = []
    for key in i18n.SITEMAP_KEYS:
        alternates = "".join(
            f'<xhtml:link rel="alternate" hreflang="{code}" '
            f'href="{CONFIG.public_url}{i18n.path_for(key, code)}"/>'
            for code in i18n.LANGS
        )
        alternates += (
            f'<xhtml:link rel="alternate" hreflang="x-default" '
            f'href="{CONFIG.public_url}{i18n.path_for(key, i18n.DEFAULT_LANG)}"/>'
        )
        for code in i18n.LANGS:
            stuecke.append(
                f"<url><loc>{CONFIG.public_url}{i18n.path_for(key, code)}</loc>"
                f"{alternates}</url>"
            )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        f"{''.join(stuecke)}"
        "</urlset>"
    )
    return Response(body, media_type="application/xml")


@app.get(P["home"]["en"], response_class=HTMLResponse)
@app.get(P["home"]["de"], response_class=HTMLResponse)
async def landing(request: Request):
    if getattr(request.state, "session", None):
        return RedirectResponse(AP["app"], status_code=303)
    limits = await _limits_safe()
    return templates.TemplateResponse(
        request,
        "landing.html", base_context(request, limits=limits)
    )


@app.get(P["register"]["en"], response_class=HTMLResponse)
@app.get(P["register"]["de"], response_class=HTMLResponse)
async def register_form(request: Request):
    if getattr(request.state, "session", None):
        return RedirectResponse(AP["app"], status_code=303)
    return templates.TemplateResponse(
        request,
        "register.html", base_context(request))


@app.post(P["register"]["en"], response_class=HTMLResponse)
@app.post(P["register"]["de"], response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    accept: str = Form(""),
    csrf: str = Form(""),
):
    verify_csrf(request, csrf)
    lang = lang_of(request)
    ip = client_ip(request)
    if not await security.rate_limit_hit(f"reg:{ip}", 3600, CONFIG.register_per_hour_per_ip):
        raise HttpProblem(429, "error.register_flood")

    email = email.strip()
    problems: list[str] = []
    if not security.valid_email(email):
        problems.append(i18n.translate(lang, "error.email_invalid"))
    pw_problem = _passwort_problem(request, password)
    if pw_problem:
        problems.append(pw_problem)
    if password != password2:
        problems.append(i18n.translate(lang, "error.password_mismatch"))
    if accept != "ja":
        problems.append(i18n.translate(lang, "error.accept_required"))

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
        await mail.send_verification(email, token, lang)
        return templates.TemplateResponse(
            request,
            "register_done.html",
            base_context(request, email=email, mail_configured=True),
        )

    token, _ = await security.create_session(user_id)
    response = RedirectResponse(AP["app"], status_code=303)
    _set_cookie(response, CONFIG.session_cookie, token, http_only=True,
                max_age=CONFIG.session_hours * 3600)
    return response


@app.get(P["verify_again"]["en"], response_class=HTMLResponse)
@app.get(P["verify_again"]["de"], response_class=HTMLResponse)
async def bestaetigung_form(request: Request):
    """Formular, um die Bestätigungsmail erneut zu schicken."""
    return templates.TemplateResponse(
        request, "verify_again.html",
        base_context(request, mail_configured=CONFIG.mail_configured),
    )


@app.post(P["verify_again"]["en"])
@app.post(P["verify_again"]["de"])
async def bestaetigung_erneut(request: Request, email: str = Form(""), csrf: str = Form("")):
    """Schickt die Bestätigungsmail erneut.

    Die Antwort ist immer dieselbe, unabhaengig davon, ob es das Konto gibt und ob
    es schon bestaetigt ist — sonst liesse sich hier abfragen, welche Adressen
    registriert sind.
    """
    verify_csrf(request, csrf)
    lang = lang_of(request)
    norm = security.normalize_email(email)
    ip = client_ip(request)

    # Bremse gegen Missbrauch als Mailschleuder: je Verbindung und je Adresse.
    if not await security.rate_limit_hit(f"verify-again-ip:{ip}", 3600, 10):
        raise HttpProblem(429, "error.verify_flood_ip")
    if norm and not await security.rate_limit_hit(f"verify-again:{norm}", 3600, 3):
        raise HttpProblem(429, "error.verify_flood_mail")

    row = await db.fetchrow(
        "SELECT id, email, email_verified FROM users WHERE email_norm = $1 AND is_active = TRUE",
        norm,
    ) if norm else None

    if row is not None and not row["email_verified"] and CONFIG.mail_configured:
        # Alte, noch offene Links entwerten: es soll immer nur einer gelten.
        await db.execute(
            "UPDATE auth_tokens SET used_at = now() "
            "WHERE user_id = $1 AND kind = 'verify_email' AND used_at IS NULL",
            row["id"],
        )
        token = security.new_token()
        await db.execute(
            "INSERT INTO auth_tokens(token_hash, user_id, kind, expires_at) "
            "VALUES($1, $2, 'verify_email', now() + interval '24 hours')",
            security.token_hash(token),
            row["id"],
        )
        await mail.send_verification(row["email"], token, lang)

    return templates.TemplateResponse(
        request,
        "info.html",
        base_context(
            request,
            heading=i18n.translate(lang, "info.verify_sent.h"),
            text=i18n.translate(lang, "info.verify_sent.p"),
        ),
    )


@app.get(P["verify"]["en"], response_class=HTMLResponse)
@app.get(P["verify"]["de"], response_class=HTMLResponse)
async def verify_email(request: Request, token: str = ""):
    lang = lang_of(request)
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
                heading=i18n.translate(lang, "info.verify_dead.h"),
                text=i18n.translate(lang, "info.verify_dead.p"),
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
            heading=i18n.translate(lang, "info.verified.h"),
            text=i18n.translate(lang, "info.verified.p"),
            link=i18n.path_for("login", lang),
            link_text=i18n.translate(lang, "info.to_login"),
        ),
    )


@app.get(P["login"]["en"], response_class=HTMLResponse)
@app.get(P["login"]["de"], response_class=HTMLResponse)
async def login_form(request: Request):
    if getattr(request.state, "session", None):
        return RedirectResponse(AP["app"], status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html", base_context(request))


@app.post(P["login"]["en"], response_class=HTMLResponse)
@app.post(P["login"]["de"], response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    csrf: str = Form(""),
):
    verify_csrf(request, csrf)
    lang = lang_of(request)
    norm = security.normalize_email(email)
    ip = client_ip(request)

    ok_ip = await security.rate_limit_hit(
        f"login-ip:{ip}", 900, CONFIG.login_attempts_per_15min * 3)
    ok_account = await security.rate_limit_hit(
        f"login-acct:{norm}", 900, CONFIG.login_attempts_per_15min
    )
    if not (ok_ip and ok_account):
        raise HttpProblem(429, "error.login_flood")

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
                errors=[i18n.translate(lang, "error.login_wrong")],
                email=email,
            ),
            status_code=401,
        )
    if not row["is_active"]:
        return templates.TemplateResponse(
            request,
            "login.html",
            base_context(
                request,
                errors=[i18n.translate(lang, "error.account_disabled")],
                email=email,
            ),
            status_code=403,
        )
    if CONFIG.require_email_verification and CONFIG.mail_configured and not row["email_verified"]:
        return templates.TemplateResponse(
            request,
            "login.html",
            base_context(
                request,
                errors=[i18n.translate(lang, "error.email_unverified")],
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
    response = RedirectResponse(AP["app"], status_code=303)
    _set_cookie(response, CONFIG.session_cookie, token, http_only=True,
                max_age=CONFIG.session_hours * 3600)
    # Die gewaehlte Sprache ueberdauert die Anmeldung: im angemeldeten Bereich
    # steht sie in keinem Pfad mehr, dort entscheidet allein das Cookie.
    _set_cookie(response, i18n.LANG_COOKIE, lang, http_only=False,
                max_age=_LANG_COOKIE_JAHR)
    response.delete_cookie(CSRF_COOKIE, path="/")
    return response


@app.post(AP["logout"])
async def logout(request: Request, csrf: str = Form("")):
    verify_csrf(request, csrf)
    await security.destroy_session(request.cookies.get(CONFIG.session_cookie))
    response = RedirectResponse(i18n.path_for("home", lang_of(request)), status_code=303)
    response.delete_cookie(CONFIG.session_cookie, path="/")
    return response


@app.get(P["forgot"]["en"], response_class=HTMLResponse)
@app.get(P["forgot"]["de"], response_class=HTMLResponse)
async def forgot_form(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot.html", base_context(request, mail_configured=CONFIG.mail_configured)
    )


@app.post(P["forgot"]["en"], response_class=HTMLResponse)
@app.post(P["forgot"]["de"], response_class=HTMLResponse)
async def forgot_submit(request: Request, email: str = Form(""), csrf: str = Form("")):
    verify_csrf(request, csrf)
    lang = lang_of(request)
    ip = client_ip(request)
    if not await security.rate_limit_hit(f"forgot:{ip}", 3600, 5):
        raise HttpProblem(429, "error.forgot_flood")

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
        await mail.send_password_reset(row["email"], token, lang)

    # Immer dieselbe Antwort — keine Auskunft darüber, ob es das Konto gibt.
    return templates.TemplateResponse(
        request,
        "info.html",
        base_context(
            request,
            heading=i18n.translate(lang, "info.forgot_sent.h"),
            text=i18n.translate(lang, "info.forgot_sent.p"),
            link=i18n.path_for("login", lang),
            link_text=i18n.translate(lang, "info.to_login"),
        ),
    )


@app.get(P["reset"]["en"], response_class=HTMLResponse)
@app.get(P["reset"]["de"], response_class=HTMLResponse)
async def reset_form(request: Request, token: str = ""):
    return templates.TemplateResponse(
        request,
        "reset.html", base_context(request, token=token))


@app.post(P["reset"]["en"], response_class=HTMLResponse)
@app.post(P["reset"]["de"], response_class=HTMLResponse)
async def reset_submit(
    request: Request,
    token: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    csrf: str = Form(""),
):
    verify_csrf(request, csrf)
    lang = lang_of(request)
    problems = []
    pw_problem = _passwort_problem(request, password)
    if pw_problem:
        problems.append(pw_problem)
    if password != password2:
        problems.append(i18n.translate(lang, "error.password_mismatch"))
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
                errors=[i18n.translate(lang, "error.reset_link_dead")],
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
            heading=i18n.translate(lang, "info.password_changed.h"),
            text=i18n.translate(lang, "info.password_changed.p"),
            link=i18n.path_for("login", lang),
            link_text=i18n.translate(lang, "info.to_login"),
        ),
    )


# --------------------------------------------------------------------------- Dashboard


@app.get(AP["app"], response_class=HTMLResponse)
async def dashboard(request: Request):
    session = getattr(request.state, "session", None)
    if session is None:
        return _redirect_login(request)
    limits = await settings_store.limits()
    usage = await quota.current_usage(session["user_id"])
    jobs = await _jobs_for(session["user_id"], lang_of(request))
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        base_context(request, jobs=jobs, limits=limits, usage=usage),
    )


async def _jobs_for(user_id: int, lang: str, limit: int = 60) -> list[dict]:
    rows = await db.fetch(
        "SELECT public_id, original_name, mime_type, size_bytes, status, error_code, "
        "       page_count, image_count, link_count, quality_note, "
        "       created_at, started_at, finished_at, duration_ms, expires_at, "
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
            "error": message_for(r["error_code"], lang) if r["error_code"] else None,
            "pages": r["page_count"],
            "images": r["image_count"],
            "links": r["link_count"],
            "note": r["quality_note"],
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
        "jobs": await _jobs_for(session["user_id"], lang_of(request)),
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


@app.post(AP["upload"])
async def upload(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    csrf: str = Form(""),
):
    session = _session(request)
    verify_csrf(request, csrf)
    lang = lang_of(request)
    user_id = session["user_id"]
    limits = await settings_store.limits()

    incoming = [f for f in files if f.filename]
    if not incoming:
        raise HttpProblem(400, "error.no_files")
    if len(incoming) > limits["max_files_per_upload"]:
        raise HttpProblem(400, "error.too_many_files")

    max_bytes = limits["max_file_size_mb"] * 1024 * 1024
    prepared: list[dict] = []
    total_bytes = 0
    est_pages = 0

    # Eine unbrauchbare Datei darf die anderen nicht mitreissen. Wer fuenf Scans
    # auswaehlt und bei einem die Seitenzahl reisst, soll die vier guten
    # trotzdem bekommen — und erfahren, welche Datei warum liegen blieb.
    abgelehnt: list[dict] = []
    erste_ablehnung: list = []

    def ablehnen(name: str, status: int, code: str, zusatz: str = "") -> None:
        text = message_for(code, lang) + (f" {zusatz}" if zusatz else "")
        abgelehnt.append({"name": storage.display_name(name), "grund": text})
        if not erste_ablehnung:
            erste_ablehnung.append((status, text))

    async with _upload_slots:
        for item in incoming:
            data = await item.read(max_bytes + 1)
            if len(data) > max_bytes:
                ablehnen(item.filename, 413, "file_too_large",
                         i18n.translate(lang, "error.max_size_hint",
                                        mb=limits["max_file_size_mb"]))
                continue
            try:
                mime, _label = uploads.check(item.filename, data)
            except uploads.RejectedUpload as exc:
                ablehnen(item.filename, 400, exc.code)
                continue

            pages = 1
            if mime == "application/pdf":
                counted, grund = uploads.pdf_page_count(data)
                if counted is None:
                    ablehnen(item.filename, 400,
                             "encrypted_pdf" if grund == "encrypted" else "unreadable_pdf")
                    continue
                if counted > limits["max_pages"]:
                    ablehnen(item.filename, 400, "too_many_pages",
                             i18n.translate(lang, "error.pages_hint",
                                            count=counted, max=limits["max_pages"]))
                    continue
                pages = counted

            total_bytes += len(data)
            est_pages += pages
            prepared.append({"name": item.filename, "data": data,
                             "mime": mime, "pages": pages})

    if not prepared:
        status, text = (erste_ablehnung[0] if erste_ablehnung
                        else (400, message_for("no_files", lang)))
        if len(incoming) > 1 and abgelehnt:
            text = i18n.translate(lang, "error.rejected_file",
                                  name=abgelehnt[0]["name"], reason=text)
        raise HttpProblem(status, "error.passthrough", text=text)

    try:
        await quota.check_batch(user_id, len(prepared), total_bytes, est_pages)
    except quota.QuotaExceeded as exc:
        raise HttpProblem(429, f"error.{exc.code}") from None

    batch_id = uuid.uuid4()
    retention = timedelta(hours=limits["retention_hours"])
    created = 0

    for entry in prepared:
        key = storage.new_key()
        storage.write("source", key, entry["data"])
        # Auftrag und Quelldatei in einer einzigen Anweisung. Als zwei getrennte
        # Anweisungen committet die erste sofort: der Auftrag steht dann auf
        # 'queued' und ist fuer den Worker sichtbar, waehrend der Verweis auf die
        # Quelldatei noch fehlt. Genau in diese Luecke ist am 31.07.2026 ein
        # Worker gefahren — vier Millisekunden nach dem Anlegen — und hat den
        # Auftrag mangels Quelldatei als fehlgeschlagen abgelegt.
        await db.fetchval(
            "WITH neuer_auftrag AS ("
            "  INSERT INTO jobs(public_id, batch_id, user_id, original_name, mime_type, "
            "                   size_bytes, page_count, expires_at, lang) "
            "  VALUES($1, $2, $3, $4, $5, $6, $7, now() + $8::interval, $9) "
            "  RETURNING id, user_id"
            ") "
            "INSERT INTO files(job_id, user_id, role, storage_key, size_bytes) "
            "SELECT id, user_id, 'source', $10, $11 FROM neuer_auftrag "
            "RETURNING job_id",
            uuid.uuid4(),
            batch_id,
            user_id,
            entry["name"][:250],
            entry["mime"],
            len(entry["data"]),
            entry["pages"],
            retention,
            lang,
            key,
            len(entry["data"]),
        )
        # Verbrauch wird beim Einstellen gezählt, nicht erst bei Erfolg — sonst
        # könnte man das Kontingent durch absichtlich fehlschlagende Aufträge umgehen.
        await quota.record(user_id, entry["pages"], len(entry["data"]))
        created += 1

    return JSONResponse({"ok": True, "created": created, "batch": str(batch_id),
                         "abgelehnt": abgelehnt})


# Uploads werden zum Prüfen vollständig in den Speicher gelesen. Ohne Bremse
# könnten mehrere gleichzeitige große Uploads den Web-Container an sein
# Speicherlimit treiben; deshalb höchstens zwei parallel.
_upload_slots = asyncio.Semaphore(2)


async def _owned_job(user_id: int, public_id: str):
    """Lädt einen Job — immer mit user_id in der Bedingung."""
    try:
        job_uuid = uuid.UUID(public_id)
    except (ValueError, AttributeError):
        raise HttpProblem(404, "error.job_missing") from None
    row = await db.fetchrow(
        "SELECT id, public_id, original_name, status, error_code, page_count, size_bytes, "
        "       image_count, link_count, table_count, merged_table_count, "
        "       quality_note, quality_findings, "
        "       created_at, duration_ms, expires_at "
        "FROM jobs WHERE public_id = $1 AND user_id = $2 AND status <> 'deleted'",
        job_uuid,
        user_id,
    )
    if row is None:
        # Gleiche Antwort für 'gibt es nicht' und 'gehört jemand anderem'.
        raise HttpProblem(404, "error.job_missing")
    return row


@app.get("/app/job/{public_id}", response_class=HTMLResponse)
async def job_detail(request: Request, public_id: str):
    session = getattr(request.state, "session", None)
    if session is None:
        return _redirect_login(request)
    lang = lang_of(request)
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

    bilder = await db.fetch(
        "SELECT seq, page_no, mime_type, size_bytes FROM job_images "
        "WHERE job_id = $1 AND user_id = $2 ORDER BY seq",
        job["id"], session["user_id"],
    )

    return templates.TemplateResponse(
        request,
        "job.html",
        base_context(
            request,
            bilder=bilder,
            job={
                "id": str(job["public_id"]),
                "name": storage.display_name(job["original_name"]),
                "status": job["status"],
                "error": message_for(job["error_code"], lang) if job["error_code"] else None,
                "pages": job["page_count"],
                "images": job["image_count"],
                "links": job["link_count"],
                "tables": job["table_count"],
                "merged_tables": job["merged_table_count"],
                "note": job["quality_note"],
                "funde": json.loads(job["quality_findings"]) if job["quality_findings"] else [],
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


@app.get("/app/job/{public_id}/download/{fmt}")
async def download(request: Request, public_id: str, fmt: str):
    session = _session(request)
    if fmt not in _DOWNLOAD_ROLES:
        raise HttpProblem(404, "error.format_missing")
    role, suffix, content_type = _DOWNLOAD_ROLES[fmt]

    job = await _owned_job(session["user_id"], public_id)
    row = await db.fetchrow(
        "SELECT storage_key FROM files WHERE job_id = $1 AND role = $2 AND user_id = $3",
        job["id"],
        role,
        session["user_id"],
    )
    if row is None:
        raise HttpProblem(404, "error.result_gone")
    try:
        data = storage.read("result", row["storage_key"])
    except (OSError, ValueError):
        raise HttpProblem(404, "error.result_gone") from None

    name = storage.safe_download_name(job["original_name"], suffix, job["created_at"])
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/app/job/{public_id}/image/{seq}")
async def bild(request: Request, public_id: str, seq: int):
    session = _session(request)
    job = await _owned_job(session["user_id"], public_id)
    row = await db.fetchrow(
        "SELECT storage_key, mime_type FROM job_images "
        "WHERE job_id = $1 AND user_id = $2 AND seq = $3",
        job["id"], session["user_id"], seq,
    )
    if row is None:
        raise HttpProblem(404, "error.image_missing")
    try:
        daten = storage.read("result", row["storage_key"])
    except (OSError, ValueError):
        raise HttpProblem(404, "error.image_gone") from None
    return Response(
        content=daten,
        media_type=row["mime_type"],
        headers={"X-Content-Type-Options": "nosniff",
                 "Content-Disposition": "inline",
                 "Cache-Control": "private, max-age=600"},
    )


@app.get(AP["zip"])
async def download_zip(request: Request, ids: str = ""):
    session = _session(request)
    lang = lang_of(request)
    wanted = [part for part in ids.split(",") if part][:50]
    if not wanted:
        raise HttpProblem(400, "error.zip_empty")

    buffer = io.BytesIO()
    verwendet: set[str] = set()
    count = 0
    einzeln: str | None = None
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
            bilder = await db.fetch(
                "SELECT seq, storage_key, mime_type FROM job_images "
                "WHERE job_id = $1 AND user_id = $2 ORDER BY seq",
                job["id"], session["user_id"],
            )

            # Zeitstempel im Namen: sonst heissen zwei Umwandlungen derselben
            # Vorlage gleich und der Browser haengt beim Herunterladen ein
            # "-2" an. Kollidieren zwei Vorlagen trotzdem, unterscheidet sie das
            # Ausgangsformat — das sagt mehr als eine laufende Nummer.
            basis = storage.safe_download_name(job["original_name"], "", job["created_at"])
            if basis in verwendet:
                endung = pathlib.PurePosixPath(job["original_name"]).suffix.lstrip(".")
                stamm = storage.safe_download_name(job["original_name"], "")
                basis = storage.safe_download_name(
                    f"{stamm}-{endung}" if endung else stamm, "", job["created_at"])
            zaehler = 2
            while basis in verwendet:
                basis = f"{basis}-{zaehler}"
                zaehler += 1
            verwendet.add(basis)
            einzeln = basis if len(verwendet) == 1 else None

            # Eigener Ordner, sobald Bilder dabei sind oder mehrere Auftraege im
            # Archiv liegen. Das Markdown verweist auf "bilder/bild-001.png";
            # ohne Ordner zeigt nach dem Entpacken kein einziges Bild.
            ordner = f"{basis}/" if (bilder or len(wanted) > 1) else ""

            for bild_row in bilder:
                endung = {"image/png": ".png", "image/jpeg": ".jpg",
                          "image/webp": ".webp", "image/tiff": ".tif"}.get(
                              bild_row["mime_type"], ".bin")
                name = f"{ordner}bilder/bild-{bild_row['seq']:03d}{endung}"
                try:
                    archive.writestr(name, storage.read("result", bild_row["storage_key"]))
                    count += 1
                except (OSError, ValueError):
                    continue

            if job["quality_note"]:
                # Der Hinweis gehoert nicht ins Markdown — das bleibt unveraendert.
                # Als eigene Datei geht er beim Herunterladen aber nicht verloren.
                zeilen = [job["quality_note"]]
                auffaellig = json.loads(job["quality_findings"] or "[]")
                if auffaellig:
                    zeilen += ["", i18n.translate(lang, "note.file.cells"), ""]
                for fund in auffaellig:
                    ort = (i18n.translate(lang, "note.file.page", page=fund["seite"])
                           if fund.get("seite")
                           else i18n.translate(lang, "note.file.table"))
                    zeile = fund.get("zeile") or i18n.translate(lang, "note.file.unnamed")
                    zeilen.append(i18n.translate(
                        lang, "note.file.line", place=ort, row=zeile,
                        column=fund["spalte"], value=fund["wert"]))
                hinweis_name = "hinweis.txt" if ordner else f"{basis}-hinweis.txt"
                archive.writestr(f"{ordner}{hinweis_name}", "\n".join(zeilen) + "\n")
                count += 1

            for row in rows:
                suffix = ".md" if row["role"] == "markdown" else ".json"
                # Namen im Archiv werden von uns erzeugt, nie vom Benutzer uebernommen.
                try:
                    archive.writestr(f"{ordner}{basis}{suffix}",
                                     storage.read("result", row["storage_key"]))
                    count += 1
                except (OSError, ValueError):
                    continue

    if count == 0:
        raise HttpProblem(404, "error.zip_nothing")

    # Bei einem Auftrag traegt das Archiv dessen Namen, bei mehreren den
    # Zeitpunkt des Herunterladens. So heisst keine zwei Dateien im
    # Download-Ordner gleich.
    zip_name = (f"{einzeln}.zip" if einzeln
                else f"Klartext_{storage.zeitstempel(datetime.datetime.now(datetime.UTC))}.zip")

    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post("/app/job/{public_id}/delete")
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
    bilder = await db.fetch(
        "SELECT storage_key FROM job_images WHERE job_id = $1 AND user_id = $2",
        job["id"], session["user_id"],
    )
    for row in bilder:
        storage.delete("result", row["storage_key"])
    await db.execute("DELETE FROM job_images WHERE job_id = $1", job["id"])
    await db.execute("DELETE FROM files WHERE job_id = $1", job["id"])
    await db.execute(
        "UPDATE jobs SET status = 'deleted', purged_at = now() WHERE id = $1", job["id"]
    )
    return RedirectResponse(AP["app"], status_code=303)


# --------------------------------------------------------------------------- Konto


@app.get(AP["account"], response_class=HTMLResponse)
async def account(request: Request):
    session = getattr(request.state, "session", None)
    if session is None:
        return _redirect_login(request)
    limits = await settings_store.limits()
    usage = await quota.current_usage(session["user_id"])
    return templates.TemplateResponse(
        request,
        "account.html", base_context(request, limits=limits, usage=usage)
    )


@app.post(AP["account_password"], response_class=HTMLResponse)
async def change_password(
    request: Request,
    current: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    csrf: str = Form(""),
):
    session = _session(request)
    verify_csrf(request, csrf)
    lang = lang_of(request)

    row = await db.fetchrow("SELECT password_hash FROM users WHERE id = $1", session["user_id"])
    ok, _ = security.verify_password(row["password_hash"] if row else None, current)

    problems = []
    if not ok:
        problems.append(i18n.translate(lang, "error.password_current_wrong"))
    pw_problem = _passwort_problem(request, password)
    if pw_problem:
        problems.append(pw_problem)
    if password != password2:
        problems.append(i18n.translate(lang, "error.password_new_mismatch"))

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
    response = RedirectResponse(f"{AP['account']}?changed=1", status_code=303)
    _set_cookie(response, CONFIG.session_cookie, token, http_only=True,
                max_age=CONFIG.session_hours * 3600)
    return response


# Das Bestaetigungswort steht in der Sprache der Oberflaeche auf dem Knopf.
# Beide Schreibweisen des deutschen Worts bleiben gueltig — auf Handytastaturen
# ist das Ö umstaendlich.
_LOESCH_WOERTER = {"LÖSCHEN", "LOESCHEN", "DELETE"}


@app.post(AP["account_delete"])
async def delete_account(request: Request, confirm: str = Form(""), csrf: str = Form("")):
    session = _session(request)
    verify_csrf(request, csrf)
    if confirm.strip().upper() not in _LOESCH_WOERTER:
        raise HttpProblem(400, "error.delete_confirm")

    rows = await db.fetch(
        "SELECT role, storage_key FROM files WHERE user_id = $1", session["user_id"]
    )
    for row in rows:
        storage.delete("source" if row["role"] == "source" else "result", row["storage_key"])
    for row in await db.fetch(
        "SELECT storage_key FROM job_images WHERE user_id = $1", session["user_id"]
    ):
        storage.delete("result", row["storage_key"])
    # users kaskadiert auf sessions, jobs, files, usage_events, auth_tokens.
    await db.execute("DELETE FROM users WHERE id = $1", session["user_id"])
    await db.execute("INSERT INTO audit_log(action) VALUES('account_deleted')")

    response = RedirectResponse(i18n.path_for("home", lang_of(request)), status_code=303)
    response.delete_cookie(CONFIG.session_cookie, path="/")
    return response


# --------------------------------------------------------------------------- Admin


@app.get(AP["admin"], response_class=HTMLResponse)
async def admin_page(request: Request):
    # Auch ohne Anmeldung 404 statt Weiterleitung: eine Weiterleitung wuerde
    # bestaetigen, dass es diesen Bereich ueberhaupt gibt.
    session = getattr(request.state, "session", None)
    if session is None or not session["is_admin"]:
        raise HttpProblem(404, "error.not_found")

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


@app.post(AP["admin_limits"])
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
    return RedirectResponse(f"{AP['admin']}?saved=1", status_code=303)


@app.post("/admin/users/{user_id}/status")
async def admin_toggle_user(request: Request, user_id: int, csrf: str = Form("")):
    session = _admin(request)
    verify_csrf(request, csrf)
    if user_id == session["user_id"]:
        raise HttpProblem(400, "error.admin_self")
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
    return RedirectResponse(AP["admin"], status_code=303)


# --------------------------------------------------------------------------- Rechtliches


@app.get(P["compare"]["en"], response_class=HTMLResponse)
@app.get(P["compare"]["de"], response_class=HTMLResponse)
async def compare(request: Request):
    return templates.TemplateResponse(
        request,
        "compare.html", base_context(request))


@app.get(P["imprint"]["en"], response_class=HTMLResponse)
@app.get(P["imprint"]["de"], response_class=HTMLResponse)
async def imprint(request: Request):
    return templates.TemplateResponse(
        request,
        "legal_imprint.html", base_context(request, cfg=CONFIG))


@app.get(P["privacy"]["en"], response_class=HTMLResponse)
@app.get(P["privacy"]["de"], response_class=HTMLResponse)
async def privacy(request: Request):
    limits = await _limits_safe()
    return templates.TemplateResponse(
        request,
        "legal_privacy.html", base_context(request, cfg=CONFIG, limits=limits)
    )


@app.get(P["terms"]["en"], response_class=HTMLResponse)
@app.get(P["terms"]["de"], response_class=HTMLResponse)
async def terms(request: Request):
    limits = await _limits_safe()
    return templates.TemplateResponse(
        request,
        "legal_terms.html", base_context(request, cfg=CONFIG, limits=limits)
    )


@app.get(P["licenses"]["en"], response_class=HTMLResponse)
@app.get(P["licenses"]["de"], response_class=HTMLResponse)
async def licenses(request: Request):
    path = pathlib.Path("/srv/THIRD_PARTY_LICENSES.md")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return templates.TemplateResponse(
        request,
        "legal_licenses.html", base_context(request, licenses_text=text)
    )
