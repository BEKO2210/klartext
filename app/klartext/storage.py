"""Dateiablage außerhalb des Webroots.

Interne Dateinamen sind zufällige Hex-Strings ohne Endung. Der vom Benutzer gelieferte
Name wird ausschließlich als Datenbankfeld geführt und beim Download neu gesetzt —
er landet nie in einem Pfad.
"""

from __future__ import annotations

import datetime
import os
import pathlib
import re
import secrets
import unicodedata
from zoneinfo import ZoneInfo

from .config import CONFIG

UPLOAD_ROOT = pathlib.Path(CONFIG.upload_dir).resolve()
RESULT_ROOT = pathlib.Path(CONFIG.result_dir).resolve()

_KEY_RE = re.compile(r"^[0-9a-f]{2}/[0-9a-f]{32}$")


def ensure_dirs() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)


def new_key() -> str:
    raw = secrets.token_hex(16)
    return f"{raw[:2]}/{raw}"


def _root(kind: str) -> pathlib.Path:
    # Bilder liegen wie Ergebnisse — sie entstehen aus der Konvertierung.
    return UPLOAD_ROOT if kind == "source" else RESULT_ROOT


def path_for(kind: str, key: str) -> pathlib.Path:
    """Löst einen Storage-Key auf. Wirft bei allem, was kein sauberer Key ist."""
    if not _KEY_RE.match(key):
        raise ValueError("ungültiger Storage-Key")
    root = _root(kind)
    target = (root / key).resolve()
    # Zweite, unabhängige Absicherung gegen Path Traversal.
    if not target.is_relative_to(root):
        raise ValueError("Pfad außerhalb des Speicherbereichs")
    return target


def write(kind: str, key: str, data: bytes) -> int:
    target = path_for(kind, key)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, target)
    os.chmod(target, 0o600)
    return len(data)


def read(kind: str, key: str) -> bytes:
    return path_for(kind, key).read_bytes()


def delete(kind: str, key: str) -> None:
    try:
        path_for(kind, key).unlink(missing_ok=True)
    except ValueError:
        return


_ZEITZONE = ZoneInfo("Europe/Berlin")

_UNSAFE = re.compile(r'[\x00-\x1f\x7f/\\:*?"<>|]')


def safe_download_name(original: str, suffix: str, zeitpunkt=None) -> str:
    """Erzeugt einen unbedenklichen Dateinamen für den Content-Disposition-Header.

    Mit ``zeitpunkt`` wird der Umwandlungszeitpunkt angehaengt. Ohne ihn heissen
    zwei Umwandlungen derselben Vorlage gleich, und der Browser haengt beim
    Herunterladen ein ``-2``, ``-3`` an — man sieht den Dateien dann nicht mehr
    an, welche welche ist.
    """
    name = unicodedata.normalize("NFC", original or "dokument")
    name = name.replace("\r", " ").replace("\n", " ")
    name = _UNSAFE.sub("_", name)
    name = name.strip(" .") or "dokument"
    stem = pathlib.PurePosixPath(name).stem or "dokument"
    stem = stem[:120]
    if zeitpunkt is not None:
        stem = f"{stem}_{zeitstempel(zeitpunkt)}"
    return f"{stem}{suffix}"


def zeitstempel(wert) -> str:
    """Datum und Uhrzeit in deutscher Ortszeit, sortierbar und dateinamentauglich."""
    if wert.tzinfo is None:
        wert = wert.replace(tzinfo=datetime.UTC)
    return wert.astimezone(_ZEITZONE).strftime("%Y-%m-%d_%H%M")


def display_name(original: str) -> str:
    """Nur zur Anzeige — Steuerzeichen raus, Länge begrenzt."""
    name = unicodedata.normalize("NFC", original or "")
    name = "".join(ch for ch in name if ch.isprintable())
    return name[:180] or "unbenannt"


def alle_schluessel(kind: str) -> list[str]:
    """Alle vorhandenen Dateien als Storage-Keys, unabhaengig von der Datenbank."""
    wurzel = _root(kind)
    gefunden: list[str] = []
    if not wurzel.exists():
        return gefunden
    for unterordner in wurzel.iterdir():
        if not unterordner.is_dir() or len(unterordner.name) != 2:
            continue
        for datei in unterordner.iterdir():
            if datei.is_file() and len(datei.name) == 32:
                gefunden.append(f"{unterordner.name}/{datei.name}")
    return gefunden


def alter_sekunden(kind: str, key: str) -> float:
    """Alter der Datei in Sekunden, oder -1 wenn sie nicht existiert."""
    import time
    try:
        return time.time() - path_for(kind, key).stat().st_mtime
    except (OSError, ValueError):
        return -1.0
