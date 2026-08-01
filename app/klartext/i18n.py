"""Sprachen: Englisch als Standard, Deutsch unter /de.

Die Seite lief bis hierher ausschliesslich auf Deutsch, der Zulauf kommt aber
ueberwiegend aus dem englischsprachigen Raum. Deshalb liegt Englisch jetzt auf
den blanken Pfaden und Deutsch unter dem Praefix /de. Die alten deutschen Pfade
bleiben als dauerhafte Weiterleitung erhalten, damit gesetzte Links und
Suchtreffer nicht ins Leere laufen.

Die Sprache steckt bei oeffentlichen Seiten im Pfad — nur so koennen Suchmaschinen
beide Fassungen getrennt aufnehmen. Im angemeldeten Bereich gibt es keine
Praefixe: dort wird nichts indexiert, die Sprache kommt aus dem Cookie.
"""

from __future__ import annotations

from .strings_de import STRINGS as _DE
from .strings_en import STRINGS as _EN

LANGS = ("en", "de")
DEFAULT_LANG = "en"
LANG_COOKIE = "klartext_lang"

_TABLES = {"en": _EN, "de": _DE}

# HTML-Sprachkennzeichen und Ortsangabe fuer die sozialen Vorschaubilder.
HTML_LANG = {"en": "en", "de": "de"}
OG_LOCALE = {"en": "en_US", "de": "de_DE"}


# --------------------------------------------------------------------- Pfade

# Oeffentliche Seiten. Schluessel -> Pfad je Sprache. Der deutsche Pfad traegt
# immer das Praefix /de, damit die Zuordnung eindeutig aus der Adresse hervorgeht.
PATHS: dict[str, dict[str, str]] = {
    "home":         {"en": "/",                   "de": "/de"},
    "register":     {"en": "/register",           "de": "/de/registrieren"},
    "login":        {"en": "/login",              "de": "/de/anmelden"},
    "verify_again": {"en": "/resend-confirmation", "de": "/de/bestaetigung"},
    "verify":       {"en": "/verify",             "de": "/de/verify"},
    "forgot":       {"en": "/forgot-password",    "de": "/de/passwort-vergessen"},
    "reset":        {"en": "/new-password",       "de": "/de/passwort-neu"},
    "imprint":      {"en": "/imprint",            "de": "/de/impressum"},
    "privacy":      {"en": "/privacy",            "de": "/de/datenschutz"},
    "terms":        {"en": "/terms",              "de": "/de/nutzungsbedingungen"},
    "licenses":     {"en": "/licenses",           "de": "/de/lizenzen"},
}

# Seiten hinter der Anmeldung. Eine Adresse fuer beide Sprachen: hier crawlt
# niemand, und ein Sprachwechsel soll nicht die Auftragsadresse veraendern.
APP_PATHS: dict[str, str] = {
    "app": "/app",
    "account": "/account",
    "admin": "/admin",
    "logout": "/logout",
    "upload": "/app/upload",
    "zip": "/app/download/zip",
    "account_password": "/account/password",
    "account_delete": "/account/delete",
    "admin_limits": "/admin/limits",
}

# Nur diese Seiten gehoeren in die Sitemap; alles andere braucht eine Anmeldung.
# Bewusst ohne login/register/forgot: duenne Funktionsseiten ohne Suchwert.
# Sie bleiben erreichbar und verlinkt, lenken aber kein Crawl-Budget mehr
# von den inhaltstragenden Seiten ab.
SITEMAP_KEYS = (
    "home", "imprint", "privacy", "terms", "licenses",
)

# Alte deutsche Adressen -> neue Adresse. Wird in der Middleware ausgewertet,
# nicht als Route: so kann kein Pfad doppelt vergeben sein.
LEGACY_REDIRECTS: dict[str, str] = {
    "/registrieren": PATHS["register"]["de"],
    "/anmelden": PATHS["login"]["de"],
    "/bestaetigung": PATHS["verify_again"]["de"],
    "/passwort-vergessen": PATHS["forgot"]["de"],
    "/passwort-neu": PATHS["reset"]["de"],
    "/impressum": PATHS["imprint"]["de"],
    "/datenschutz": PATHS["privacy"]["de"],
    "/nutzungsbedingungen": PATHS["terms"]["de"],
    "/lizenzen": PATHS["licenses"]["de"],
    "/konto": APP_PATHS["account"],
    "/konto/passwort": APP_PATHS["account_password"],
    "/konto/loeschen": APP_PATHS["account_delete"],
    "/abmelden": APP_PATHS["logout"],
}

# Pfad -> Schluessel, fuer die Rueckrichtung (welche Seite ist das gerade?).
_KEY_BY_PATH: dict[str, tuple[str, str]] = {
    path: (key, lang) for key, langs in PATHS.items() for lang, path in langs.items()
}


def legacy_target(path: str) -> str | None:
    """Neue Adresse fuer einen alten deutschen Pfad, sonst None."""
    if path in LEGACY_REDIRECTS:
        return LEGACY_REDIRECTS[path]
    # Auftragsadressen: /app/auftrag/<id>/... wurde zu /app/job/<id>/...
    if path.startswith("/app/auftrag/"):
        rest = path[len("/app/auftrag/"):]
        rest = rest.replace("/bild/", "/image/")
        if rest.endswith("/loeschen"):
            rest = rest[: -len("/loeschen")] + "/delete"
        return "/app/job/" + rest
    if path.startswith("/admin/nutzer/"):
        return "/admin/users/" + path[len("/admin/nutzer/"):]
    return None


def path_for(key: str, lang: str) -> str:
    """Pfad einer Seite in der gewuenschten Sprache."""
    if key in APP_PATHS:
        return APP_PATHS[key]
    entry = PATHS.get(key)
    if entry is None:
        return "/"
    return entry.get(lang) or entry[DEFAULT_LANG]


def twin(path: str, lang: str) -> str:
    """Dieselbe Seite in der anderen Sprache. Unbekanntes bleibt, wie es ist."""
    found = _KEY_BY_PATH.get(path)
    if found is None:
        return path
    return path_for(found[0], lang)


def page_key(path: str) -> str | None:
    found = _KEY_BY_PATH.get(path)
    return found[0] if found else None


def is_public_path(path: str) -> bool:
    return path in _KEY_BY_PATH


def lang_from_path(path: str) -> str | None:
    """Sprache, sofern sie im Pfad steht."""
    if path == "/de" or path.startswith("/de/"):
        return "de"
    if is_public_path(path):
        return "en"
    return None


def preferred_from_header(header: str) -> str:
    """Wunschsprache aus Accept-Language. Ohne Treffer bleibt es bei Englisch."""
    best_lang = DEFAULT_LANG
    best_q = -1.0
    for teil in (header or "").split(","):
        stueck = teil.strip()
        if not stueck:
            continue
        marke, _, rest = stueck.partition(";")
        gewicht = 1.0
        if rest.startswith("q="):
            try:
                gewicht = float(rest[2:])
            except ValueError:
                gewicht = 0.0
        code = marke.strip().lower().split("-")[0]
        if code in LANGS and gewicht > best_q:
            best_lang, best_q = code, gewicht
    return best_lang


def normalize(value: str | None) -> str | None:
    return value if value in LANGS else None


# ------------------------------------------------------------------- Texte


def translate(lang: str, key: str, **werte) -> str:
    """Text in der gewuenschten Sprache. Fehlt er, greift Englisch."""
    text = _TABLES.get(lang, _EN).get(key)
    if text is None:
        text = _EN.get(key)
    if text is None:
        # Sichtbar, aber ohne die Seite zu zerlegen: der fehlende Schluessel
        # steht dann im Layout und faellt beim Durchsehen sofort auf.
        return key
    if werte:
        try:
            return text.format(**werte)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def known_keys() -> set[str]:
    return set(_EN) | set(_DE)
