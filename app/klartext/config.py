"""Zentrale Konfiguration. Alles über Environment-Variablen steuerbar.

Limits sind zusätzlich zur Laufzeit vom Admin überschreibbar (Tabelle app_settings);
die Auflösung passiert in settings_store.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _s(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _i(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _b(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Fair-Use-Limits: Schlüssel -> (ENV-Variable, Vorgabe, Beschreibung für den Admin)
LIMIT_DEFS: dict[str, tuple[str, int, str]] = {
    "max_file_size_mb": ("MAX_FILE_SIZE_MB", 25, "Maximale Größe einer einzelnen Datei (MB)"),
    "max_files_per_upload": ("MAX_FILES_PER_UPLOAD", 5, "Maximale Anzahl Dateien pro Upload"),
    "max_pages": ("MAX_PAGES", 100, "Maximale Seitenzahl pro Dokument"),
    "jobs_per_hour": ("JOBS_PER_HOUR", 30, "Konvertierungen pro Benutzer und Stunde"),
    "jobs_per_day": ("JOBS_PER_DAY", 100, "Konvertierungen pro Benutzer und Tag"),
    "pages_per_day": ("PAGES_PER_DAY", 600, "Seiten pro Benutzer und Tag"),
    "mb_per_day": ("MB_PER_DAY", 300, "Hochgeladene Megabyte pro Benutzer und Tag"),
    "max_active_jobs": ("MAX_ACTIVE_JOBS", 2, "Gleichzeitig laufende Jobs pro Benutzer"),
    "max_queued_jobs": ("MAX_QUEUED_JOBS", 10, "Maximale Warteschlange pro Benutzer"),
    "global_queue_limit": ("GLOBAL_QUEUE_LIMIT", 200, "Globale Warteschlangenlänge"),
    "retention_hours": ("RETENTION_HOURS", 24, "Aufbewahrung von Dateien und Ergebnissen (Stunden)"),
}


@dataclass(frozen=True)
class Config:
    # --- Produkt / Branding ---
    product_name: str = _s("PRODUCT_NAME", "Klartext")
    public_url: str = _s("PUBLIC_URL", "http://localhost:8160").rstrip("/")

    # --- Datenbank ---
    db_dsn: str = _s("DATABASE_URL", "")
    db_pool_min: int = _i("DB_POOL_MIN", 1)
    db_pool_max: int = _i("DB_POOL_MAX", 8)

    # --- Docling ---
    docling_url: str = _s("DOCLING_URL", "http://docling:5001").rstrip("/")
    docling_api_key: str = _s("DOCLING_API_KEY", "")
    docling_timeout_s: int = _i("DOCLING_DOC_TIMEOUT", 900)
    ocr_engine: str = _s("OCR_ENGINE", "rapidocr")
    ocr_lang: str = _s("OCR_LANG", "deu,eng")
    table_mode: str = _s("TABLE_MODE", "accurate")

    # --- Speicher ---
    upload_dir: str = _s("UPLOAD_DIR", "/data/uploads")
    result_dir: str = _s("RESULT_DIR", "/data/results")

    # --- Sessions ---
    session_cookie: str = _s("SESSION_COOKIE", "klartext_session")
    session_hours: int = _i("SESSION_HOURS", 72)
    cookie_secure: bool = _b("COOKIE_SECURE", True)

    # --- Worker ---
    worker_concurrency: int = _i("WORKER_CONCURRENCY", 2)
    worker_poll_seconds: float = float(_s("WORKER_POLL_SECONDS", "2"))
    job_stale_minutes: int = _i("JOB_STALE_MINUTES", 30)

    # --- E-Mail (optional) ---
    # Reichweitenmessung. Leer = ausgeschaltet. Gemessen wird ausschliesslich auf
    # den oeffentlichen Seiten, nie im angemeldeten Bereich: dort stehen
    # Auftragskennungen in der Adresse.
    plausible_url: str = _s("PLAUSIBLE_URL", "").rstrip("/")
    plausible_domain: str = _s("PLAUSIBLE_DOMAIN", "")

    smtp_host: str = _s("SMTP_HOST", "")
    smtp_port: int = _i("SMTP_PORT", 587)
    smtp_user: str = _s("SMTP_USER", "")
    smtp_password: str = _s("SMTP_PASSWORD", "")
    smtp_from: str = _s("SMTP_FROM", "")
    smtp_starttls: bool = _b("SMTP_STARTTLS", True)
    require_email_verification: bool = _b("REQUIRE_EMAIL_VERIFICATION", True)

    # --- Missbrauchsschutz ---
    login_attempts_per_15min: int = _i("LOGIN_ATTEMPTS_PER_15MIN", 10)
    register_per_hour_per_ip: int = _i("REGISTER_PER_HOUR_PER_IP", 5)
    requests_per_minute_per_ip: int = _i("REQUESTS_PER_MINUTE_PER_IP", 240)
    trust_proxy_header: bool = _b("TRUST_PROXY_HEADER", True)

    # --- Rechtliche Angaben (leer = im Frontend als "nicht konfiguriert" markiert) ---
    legal_operator: str = _s("LEGAL_OPERATOR", "")
    legal_address: str = _s("LEGAL_ADDRESS", "")
    legal_email: str = _s("LEGAL_EMAIL", "")
    legal_phone: str = _s("LEGAL_PHONE", "")
    legal_vat_id: str = _s("LEGAL_VAT_ID", "")
    legal_responsible: str = _s("LEGAL_RESPONSIBLE", "")

    limit_env_defaults: dict[str, int] = field(default_factory=dict)

    @property
    def mail_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    @property
    def messung_aktiv(self) -> bool:
        return bool(self.plausible_url and self.plausible_domain)


def load() -> Config:
    cfg = Config()
    object.__setattr__(
        cfg,
        "limit_env_defaults",
        {key: _i(env_name, default) for key, (env_name, default, _) in LIMIT_DEFS.items()},
    )
    return cfg


CONFIG = load()

# Formate, die tatsächlich getestet und freigegeben sind.
# Jeder Eintrag: Endung -> (erlaubte MIME-Typen aus der Inhaltsprüfung, Anzeigename)
SUPPORTED_FORMATS: dict[str, tuple[tuple[str, ...], str]] = {
    ".pdf": (("application/pdf",), "PDF"),
    ".png": (("image/png",), "PNG-Bild"),
    ".jpg": (("image/jpeg",), "JPEG-Bild"),
    ".jpeg": (("image/jpeg",), "JPEG-Bild"),
    ".tif": (("image/tiff",), "TIFF-Bild"),
    ".tiff": (("image/tiff",), "TIFF-Bild"),
    ".webp": (("image/webp",), "WebP-Bild"),
    ".bmp": (("image/bmp", "image/x-ms-bmp"), "BMP-Bild"),
    ".docx": (
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"),
        "Word-Dokument",
    ),
    ".xlsx": (
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/zip"),
        "Excel-Tabelle",
    ),
    ".pptx": (
        ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/zip"),
        "PowerPoint-Präsentation",
    ),
    ".html": (("text/html", "text/plain"), "HTML-Datei"),
    ".md": (("text/markdown", "text/plain"), "Markdown-Datei"),
}

SUPPORTED_EXT_LIST = sorted({e.lstrip(".").upper() for e in SUPPORTED_FORMATS})


def _formate_ohne_dubletten() -> list[str]:
    """Je Dateityp nur eine Endung — fuer die Anzeige auf der Startseite.

    Die vollstaendige Liste enthaelt Paare wie JPG und JPEG oder TIF und TIFF,
    die denselben Typ meinen. Nebeneinander gezeigt wirkt das wie ein Versehen.
    Zusammengefasst wird ueber den Medientyp, nicht ueber eine Namensliste —
    dann stimmt es auch, wenn spaeter ein Format dazukommt.
    """
    gesehen: dict[str, str] = {}
    for endung, (typen, _) in sorted(SUPPORTED_FORMATS.items()):
        schluessel = typen[0]
        name = endung.lstrip(".").upper()
        vorhanden = gesehen.get(schluessel)
        # Die kuerzere Schreibweise gewinnt: JPG vor JPEG, TIF vor TIFF.
        if vorhanden is None or len(name) < len(vorhanden):
            gesehen[schluessel] = name
    return sorted(gesehen.values())


SUPPORTED_EXT_SHORT = _formate_ohne_dubletten()
