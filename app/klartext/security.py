"""Passwörter, Sessions, CSRF, Rate-Limits."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import unicodedata
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.low_level import Type

from . import db
from .config import CONFIG

# Argon2id — bewusst moderate Parameter, der Server teilt sich CPU mit anderen Diensten.
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)

# Dummy-Hash gegen User-Enumeration über Antwortzeiten.
_DUMMY_HASH = _hasher.hash("klartext-dummy-password-for-timing")

MIN_PASSWORD_LEN = 10
MAX_PASSWORD_LEN = 256


def now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> tuple[bool, str | None]:
    """Gibt (ok, neuer_hash_falls_rehash_nötig) zurück."""
    target = stored_hash or _DUMMY_HASH
    try:
        _hasher.verify(target, password)
    except Exception:  # noqa: BLE001 - falsches Passwort oder defekter Hash
        return False, None
    if stored_hash is None:
        return False, None
    if _hasher.check_needs_rehash(stored_hash):
        return True, _hasher.hash(password)
    return True, None


def password_problem(password: str) -> str | None:
    """Gibt einen Textschluessel zurueck, damit die Meldung uebersetzbar bleibt."""
    if len(password) < MIN_PASSWORD_LEN:
        return "error.password_short"
    if len(password) > MAX_PASSWORD_LEN:
        return "error.password_long"
    if password.strip() == "":
        return "error.password_blank"
    return None


def normalize_email(email: str) -> str:
    return unicodedata.normalize("NFKC", email).strip().lower()


def valid_email(email: str) -> bool:
    email = email.strip()
    if not (3 < len(email) <= 254) or email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    if not local or not domain or "." not in domain:
        return False
    if any(ch.isspace() for ch in email):
        return False
    return not domain.startswith(".") and not domain.endswith(".")


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


# --------------------------------------------------------------------------- Sessions


async def create_session(user_id: int) -> tuple[str, str]:
    """Legt eine neue Session an. Gibt (cookie_token, csrf_token) zurück."""
    token = new_token()
    csrf = new_token()
    await db.execute(
        "INSERT INTO sessions(token_hash, user_id, csrf_token, expires_at) "
        "VALUES($1, $2, $3, $4)",
        token_hash(token),
        user_id,
        csrf,
        now() + timedelta(hours=CONFIG.session_hours),
    )
    return token, csrf


async def load_session(token: str | None):
    if not token:
        return None
    row = await db.fetchrow(
        "SELECT s.id, s.user_id, s.csrf_token, s.expires_at, "
        "       u.email, u.is_admin, u.is_active, u.email_verified "
        "FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = $1 AND s.expires_at > now()",
        token_hash(token),
    )
    if row is None:
        return None
    if not row["is_active"]:
        await db.execute("DELETE FROM sessions WHERE id = $1", row["id"])
        return None
    await db.execute("UPDATE sessions SET last_seen_at = now() WHERE id = $1", row["id"])
    return row


async def destroy_session(token: str | None) -> None:
    if token:
        await db.execute("DELETE FROM sessions WHERE token_hash = $1", token_hash(token))


async def destroy_all_sessions(user_id: int) -> None:
    await db.execute("DELETE FROM sessions WHERE user_id = $1", user_id)


# --------------------------------------------------------------------------- Rate-Limits


async def rate_limit_hit(bucket: str, window_seconds: int, max_hits: int) -> bool:
    """True = erlaubt, False = Limit erreicht. Fixed-Window-Zähler in der Datenbank."""
    window_start = now().timestamp() // window_seconds * window_seconds
    window_at = datetime.fromtimestamp(window_start, tz=timezone.utc)
    hits = await db.fetchval(
        "INSERT INTO rate_limits(bucket, window_at, hits) VALUES($1, $2, 1) "
        "ON CONFLICT (bucket, window_at) DO UPDATE SET hits = rate_limits.hits + 1 "
        "RETURNING hits",
        bucket,
        window_at,
    )
    return int(hits) <= max_hits


async def rate_limit_reset(bucket: str) -> None:
    await db.execute("DELETE FROM rate_limits WHERE bucket = $1", bucket)


async def prune_rate_limits() -> None:
    await db.execute("DELETE FROM rate_limits WHERE window_at < now() - interval '2 days'")
