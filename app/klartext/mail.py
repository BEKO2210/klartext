"""E-Mail-Versand (Bestätigung, Passwort-Reset).

Es werden ausschließlich Links versendet, niemals Dokumentinhalte oder Dateinamen.
Ist kein SMTP konfiguriert, wird nichts versendet und der Aufrufer erfährt das.
"""

from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from .config import CONFIG

log = logging.getLogger("klartext.mail")


async def _send(to: str, subject: str, body: str) -> bool:
    if not CONFIG.mail_configured:
        return False
    message = EmailMessage()
    message["From"] = CONFIG.smtp_from
    message["To"] = to
    message["Subject"] = subject
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
