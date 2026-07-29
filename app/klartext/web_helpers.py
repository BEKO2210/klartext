"""Gemeinsame Bausteine für die Routen: Kontext, CSRF, Fehlermeldungen."""

from __future__ import annotations

import datetime
import hashlib
import pathlib
import secrets
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

from .config import CONFIG, SUPPORTED_EXT_LIST, SUPPORTED_EXT_SHORT
from .security import constant_time_eq

templates = Jinja2Templates(directory="klartext/templates")
templates.env.autoescape = True

CSRF_COOKIE = "klartext_csrf"

# Der Server laeuft auf UTC, die Benutzer sitzen in Deutschland. Ohne Umrechnung
# zeigen serverseitig gerenderte Zeiten zwei Stunden weniger an als die im
# Browser berechneten — im selben Bild, was zurecht wie ein Fehler aussieht.
ZEITZONE = ZoneInfo("Europe/Berlin")


def ortszeit(wert: datetime.datetime) -> datetime.datetime:
    """Rechnet einen Zeitpunkt in die deutsche Ortszeit um."""
    if wert.tzinfo is None:
        wert = wert.replace(tzinfo=datetime.UTC)
    return wert.astimezone(ZEITZONE)


def zeit(wert, muster: str = "%d.%m.%Y um %H:%M") -> str:
    """Jinja-Filter: Zeitpunkt in deutscher Ortszeit."""
    if not isinstance(wert, datetime.datetime):
        return ""
    return ortszeit(wert).strftime(muster)

_STATIC_DIR = pathlib.Path("klartext/static")
_asset_cache: dict[str, str] = {}


templates.env.filters["zeit"] = zeit


def asset(name: str) -> str:
    """Statische Datei mit Inhalts-Kennung.

    Cloudflare cacht /static/* vier Stunden. Ohne Kennung im Pfad bekaemen
    Besucher nach einem Update stundenlang die alte Datei. Die Kennung aendert
    sich mit dem Inhalt, also gibt es nach jedem Deploy sofort die neue Fassung —
    und unveraenderte Dateien bleiben weiter im Cache.
    """
    if name not in _asset_cache:
        try:
            digest = hashlib.sha256((_STATIC_DIR / name).read_bytes()).hexdigest()[:10]
        except OSError:
            digest = "0"
        _asset_cache[name] = f"/static/{name}?v={digest}"
    return _asset_cache[name]


class HttpProblem(Exception):
    """Benutzerfreundlicher Fehler mit Statuscode — nie mit internen Details."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# Fehlercodes -> verständliche deutsche Saetze. Keine Technikbegriffe, keine Pfade.
MESSAGES: dict[str, str] = {
    "unsupported_type": "Dieses Dateiformat wird nicht unterstützt. Möglich sind: "
    + ", ".join(SUPPORTED_EXT_LIST)
    + ".",
    "type_mismatch": "Der Inhalt der Datei passt nicht zur Dateiendung. "
    "Bitte lade die Originaldatei hoch.",
    "empty_file": "Die Datei ist leer.",
    "file_too_large": "Die Datei ist größer als erlaubt.",
    "too_many_files": "Du hast zu viele Dateien auf einmal ausgewählt.",
    "too_many_pages": "Das Dokument hat mehr Seiten als erlaubt.",
    "queue_full": "Deine Warteschlange ist voll. Warte, bis die laufenden "
    "Konvertierungen fertig sind.",
    "hourly_limit": "Du hast das Stundenkontingent erreicht. Bitte später noch einmal.",
    "daily_limit": "Du hast das Tageskontingent erreicht. Morgen geht es weiter.",
    "pages_limit": "Du hast das Seitenkontingent für heute erreicht.",
    "volume_limit": "Du hast das Datenvolumen für heute erreicht.",
    "server_busy": "Gerade sind sehr viele Konvertierungen unterwegs. "
    "Bitte versuche es in ein paar Minuten noch einmal.",
    "timeout": "Die Verarbeitung hat zu lange gedauert und wurde abgebrochen.",
    "conversion_failed": "Das Dokument konnte nicht gelesen werden. "
    "Möglicherweise ist es beschädigt oder passwortgeschützt.",
    "engine_unreachable": "Die Verarbeitung ist gerade nicht verfügbar. "
    "Der Auftrag bleibt in der Warteschlange.",
    "engine_error": "Bei der Verarbeitung ist ein Fehler aufgetreten.",
    "unsupported": "Dieses Dokument konnte nicht verarbeitet werden.",
    "no_files": "Es wurde keine Datei ausgewählt.",
    "encrypted_pdf": "Diese PDF ist passwortgeschützt und kann nicht gelesen werden.",
}


def message_for(code: str) -> str:
    return MESSAGES.get(code, "Es ist ein Fehler aufgetreten. Bitte versuche es noch einmal.")


def client_ip(request: Request) -> str:
    if CONFIG.trust_proxy_header:
        forwarded = request.headers.get("cf-connecting-ip") or request.headers.get(
            "x-forwarded-for", ""
        )
        if forwarded:
            return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unbekannt")[:64]


def csrf_token(request: Request) -> str:
    """Token der Session, sonst Token aus dem Doppel-Cookie für anonyme Formulare."""
    session = getattr(request.state, "session", None)
    if session is not None:
        return session["csrf_token"]
    token = request.cookies.get(CSRF_COOKIE)
    if not token:
        token = getattr(request.state, "fresh_csrf", None) or secrets.token_urlsafe(32)
        request.state.fresh_csrf = token
    return token


def verify_csrf(request: Request, submitted: str | None) -> None:
    expected = csrf_token(request)
    if not submitted or not constant_time_eq(expected, submitted):
        raise HttpProblem(400, "Das Formular ist abgelaufen. Bitte lade die Seite neu.")


def base_context(request: Request, **extra) -> dict:
    session = getattr(request.state, "session", None)
    ctx = {
        "request": request,
        "product": CONFIG.product_name,
        "public_url": CONFIG.public_url,
        "csrf": csrf_token(request),
        "user": None if session is None else {
            "email": session["email"],
            "is_admin": session["is_admin"],
            "verified": session["email_verified"],
        },
        "formats": SUPPORTED_EXT_LIST,
        "formats_kurz": SUPPORTED_EXT_SHORT,
        # Gemessen wird nur ausserhalb des angemeldeten Bereichs: dort stehen
        # Auftragskennungen in der Adresse, die nichts in einer Statistik zu
        # suchen haben.
        "messung": CONFIG.messung_aktiv and session is None,
        "messung_domain": CONFIG.plausible_domain,
        "asset": asset,
    }
    ctx.update(extra)
    return ctx
