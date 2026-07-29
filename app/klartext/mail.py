"""E-Mail-Versand (Bestätigung, Passwort-Reset).

Es werden ausschließlich Links versendet, niemals Dokumentinhalte oder Dateinamen.
Ist kein SMTP konfiguriert, wird nichts versendet und der Aufrufer erfährt das.
"""

from __future__ import annotations

import logging
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

import aiosmtplib

from .config import CONFIG

log = logging.getLogger("klartext.mail")

# Adressbereiche, die per Norm nie Post annehmen koennen (RFC 2606 und RFC 6761).
# An diese Adressen wird gar nicht erst zugestellt: der Postausgangsserver wuerde
# es versuchen, an der Namensaufloesung scheitern und einen Unzustellbarkeits-
# bericht an den Absender schicken. Bei Tests entsteht so pro Registrierung eine
# Rueckläufer-Mail im Postfach des Betreibers.
_TOTE_ENDUNGEN = (".invalid", ".test", ".localhost", ".example")
_TOTE_DOMAINS = frozenset({"example.com", "example.net", "example.org", "localhost"})


def unzustellbar(adresse: str) -> bool:
    """Wahr, wenn die Adresse per Norm keine Post annehmen kann."""
    _, trenner, domain = adresse.strip().lower().rpartition("@")
    if not trenner or not domain:
        return False
    if domain.endswith(_TOTE_ENDUNGEN):
        return True
    # Untergeordnete Namen zaehlen mit: www.example.com nimmt genauso wenig Post
    # an wie example.com selbst.
    return any(domain == tot or domain.endswith("." + tot) for tot in _TOTE_DOMAINS)


def _absender_domain() -> str:
    """Domain fuer die Message-ID — aus der oeffentlichen Adresse des Dienstes."""
    rest = CONFIG.public_url.split("//", 1)[-1]
    domain = rest.split("/", 1)[0].split(":", 1)[0].strip()
    if domain:
        return domain
    _, adresse = parseaddr(CONFIG.smtp_from)
    return adresse.rpartition("@")[2] or "localhost"


async def _send(to: str, subject: str, body: str) -> bool:
    if unzustellbar(to):
        # Absichtlich still: der Aufrufer soll sich genauso verhalten wie sonst,
        # damit aus der Antwort nicht ablesbar wird, welche Konten existieren.
        log.info("Versand unterdrueckt, Adresse kann keine Post annehmen")
        return False
    if not CONFIG.mail_configured:
        return False
    message = EmailMessage()
    message["From"] = CONFIG.smtp_from
    message["To"] = to
    message["Subject"] = subject
    # Standardkopfzeilen selbst setzen. aiosmtplib ergaenzt weder Message-ID noch
    # Date; manche Postfaecher bewerten das Fehlen als Spam-Merkmal. Die Kennung
    # wird aus der eigenen Domain gebildet, damit sie eindeutig bleibt.
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=_absender_domain())
    # Antworten sollen beim Betreiber landen, nicht ins Leere laufen.
    message["Reply-To"] = CONFIG.smtp_from
    # Kennzeichnet die Nachricht als maschinell erzeugt: Abwesenheitsantworten
    # und Autoresponder sollen darauf nicht reagieren (RFC 3834).
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(body)
    try:
        await aiosmtplib.send(
            message,
            hostname=CONFIG.smtp_host,
            port=CONFIG.smtp_port,
            username=CONFIG.smtp_user or None,
            password=CONFIG.smtp_password or None,
            start_tls=CONFIG.smtp_starttls,
            timeout=20,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - Zustellfehler darf den Request nicht kippen
        log.warning("E-Mail konnte nicht zugestellt werden: %s", type(exc).__name__)
        return False


async def send_verification(to: str, token: str) -> bool:
    link = f"{CONFIG.public_url}/verify?token={token}"
    return await _send(
        to,
        f"{CONFIG.product_name}: E-Mail-Adresse bestätigen",
        f"""Hallo,

bitte bestätige deine E-Mail-Adresse für {CONFIG.product_name}:

{link}

Der Link ist 24 Stunden gültig. Wenn du dich nicht registriert hast,
ignoriere diese Nachricht einfach — es passiert dann nichts weiter.
""",
    )


async def send_password_reset(to: str, token: str) -> bool:
    link = f"{CONFIG.public_url}/passwort-neu?token={token}"
    return await _send(
        to,
        f"{CONFIG.product_name}: Passwort zurücksetzen",
        f"""Hallo,

über diesen Link kannst du ein neues Passwort setzen:

{link}

Der Link ist 1 Stunde gültig und funktioniert nur einmal.
Wenn du das nicht angefordert hast, ignoriere diese Nachricht —
dein bisheriges Passwort bleibt unverändert gültig.
""",
    )
