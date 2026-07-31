"""Gemeinsame Bausteine für die Routen: Kontext, CSRF, Sprache, Fehlermeldungen."""

from __future__ import annotations

import datetime
import hashlib
import pathlib
import secrets
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

from . import i18n
from .config import CONFIG, SUPPORTED_EXT_LIST, SUPPORTED_EXT_SHORT
from .security import constant_time_eq

templates = Jinja2Templates(directory="klartext/templates")
templates.env.autoescape = True

CSRF_COOKIE = "klartext_csrf"

# Der Server laeuft auf UTC. Die deutsche Fassung zeigt deutsche Ortszeit — die
# Leserschaft sitzt dort. Die englische Fassung wird weltweit gelesen; eine
# Berliner Uhrzeit ohne Kennzeichnung waere dort schlicht falsch verstanden,
# deshalb steht in der englischen Fassung UTC und die Zone mit im Text.
ZEITZONE = ZoneInfo("Europe/Berlin")

_ZONE_JE_SPRACHE = {"de": ZEITZONE, "en": datetime.UTC}
_MUSTER_JE_SPRACHE = {"de": "%d.%m.%Y um %H:%M", "en": "%b %d, %Y at %H:%M %Z"}
_KURZMUSTER_JE_SPRACHE = {"de": "%d.%m.%y %H:%M", "en": "%Y-%m-%d %H:%M"}


def ortszeit(wert: datetime.datetime, lang: str = "de") -> datetime.datetime:
    """Rechnet einen Zeitpunkt in die Zone der jeweiligen Sprachfassung um."""
    if wert.tzinfo is None:
        wert = wert.replace(tzinfo=datetime.UTC)
    return wert.astimezone(_ZONE_JE_SPRACHE.get(lang, ZEITZONE))


def zeit(wert, lang: str = "de", kurz: bool = False) -> str:
    """Zeitpunkt in der Schreibweise der jeweiligen Sprache."""
    if not isinstance(wert, datetime.datetime):
        return ""
    tabelle = _KURZMUSTER_JE_SPRACHE if kurz else _MUSTER_JE_SPRACHE
    muster = tabelle.get(lang, tabelle["de"])
    return ortszeit(wert, lang).strftime(muster)


_STATIC_DIR = pathlib.Path("klartext/static")
_asset_cache: dict[str, str] = {}


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
    """Benutzerfreundlicher Fehler mit Statuscode — nie mit internen Details.

    Der Text wird erst beim Anzeigen uebersetzt: geworfen wird ein Schluessel,
    damit dieselbe Ausnahme in beiden Sprachfassungen richtig ankommt.
    """

    def __init__(self, status: int, key: str, **werte):
        super().__init__(key)
        self.status = status
        self.key = key
        self.werte = werte

    def text(self, lang: str) -> str:
        return i18n.translate(lang, self.key, **self.werte)


def lang_of(request: Request) -> str:
    return getattr(request.state, "lang", i18n.DEFAULT_LANG)


def message_for(code: str | None, lang: str) -> str:
    """Fehlercode aus der Verarbeitung -> verstaendlicher Satz."""
    if not code:
        return i18n.translate(lang, "error.generic")
    key = f"error.{code}"
    if key not in i18n.known_keys():
        return i18n.translate(lang, "error.generic")
    return i18n.translate(lang, key, list=", ".join(SUPPORTED_EXT_LIST))


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
        raise HttpProblem(400, "error.form_expired")


def base_context(request: Request, **extra) -> dict:
    session = getattr(request.state, "session", None)
    lang = lang_of(request)
    pfad = request.url.path

    def uebersetzen(key: str, **werte) -> str:
        werte.setdefault("product", CONFIG.product_name)
        return i18n.translate(lang, key, **werte)

    def pfad_fuer(key: str) -> str:
        return i18n.path_for(key, lang)

    # Texte fuer den Browser. Sie werden als Datenblock in die Seite gelegt,
    # nicht als Skript: die Inhaltsrichtlinie erlaubt kein Inline-JavaScript.
    js_texte = {
        schluessel[3:]: i18n.translate(lang, schluessel)
        for schluessel in i18n.known_keys()
        if schluessel.startswith("js.")
    }

    # Sprachumschalter: dieselbe Seite in der anderen Sprache. Der Parameter
    # merkt die Wahl im Cookie, damit die automatische Umleitung nach
    # Browsersprache danach nicht dagegenhaelt.
    andere = "de" if lang == "en" else "en"
    ctx = {
        "request": request,
        "lang": lang,
        "other_lang": andere,
        "html_lang": i18n.HTML_LANG[lang],
        "og_locale": i18n.OG_LOCALE[lang],
        "switch_url": i18n.twin(pfad, andere) + f"?lang={andere}",
        "alternates": (
            [
                {"lang": code, "url": CONFIG.public_url + i18n.twin(pfad, code)}
                for code in i18n.LANGS
            ]
            if i18n.is_public_path(pfad)
            else []
        ),
        "xdefault": (CONFIG.public_url + i18n.twin(pfad, i18n.DEFAULT_LANG)
                     if i18n.is_public_path(pfad) else ""),
        "canonical": CONFIG.public_url + pfad,
        "t": uebersetzen,
        "path_for": pfad_fuer,
        "js_strings": js_texte,
        "zeit": lambda wert, kurz=False: zeit(wert, lang, kurz),
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
