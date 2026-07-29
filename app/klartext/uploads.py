"""Prüfung hochgeladener Dateien.

Grundsatz: der Dateiname allein entscheidet nichts. Es zählt der tatsächliche Inhalt.
"""

from __future__ import annotations

import io
import pathlib

import magic
from pypdf import PdfReader

from .config import SUPPORTED_FORMATS


class RejectedUpload(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


_ZIP_BASED = {".docx", ".xlsx", ".pptx"}


def extension_of(filename: str) -> str:
    return pathlib.PurePosixPath(filename.replace("\\", "/")).suffix.lower()


def sniff_mime(data: bytes) -> str:
    return magic.from_buffer(data[:8192], mime=True) or "application/octet-stream"


def check(filename: str, data: bytes) -> tuple[str, str]:
    """Gibt (mime, anzeigetyp) zurück oder wirft RejectedUpload.

    Geprüft wird die Kombination aus Endung und echtem Inhaltstyp: beides muss
    zusammenpassen. Eine .pdf mit PNG-Inhalt wird abgelehnt, ebenso umgekehrt.
    """
    if not data:
        raise RejectedUpload("empty_file")

    ext = extension_of(filename)
    if ext not in SUPPORTED_FORMATS:
        raise RejectedUpload("unsupported_type")

    allowed_mimes, label = SUPPORTED_FORMATS[ext]
    mime = sniff_mime(data)

    if mime not in allowed_mimes:
        # Office-Dateien sind ZIP-Container; libmagic meldet je nach Version
        # den konkreten OOXML-Typ oder nur application/zip.
        if ext in _ZIP_BASED and mime == "application/zip":
            pass
        else:
            raise RejectedUpload("type_mismatch", f"{ext} vs {mime}")

    if ext == ".pdf" and not data.startswith(b"%PDF-"):
        raise RejectedUpload("type_mismatch", "pdf header")

    return mime, label


def pdf_page_count(data: bytes) -> int | None:
    """Seitenzahl einer PDF. None, wenn sie sich nicht lesen lässt."""
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            # Verschlüsselte PDFs können wir nicht zuverlässig zählen.
            try:
                reader.decrypt("")
            except Exception:  # noqa: BLE001
                return None
        return len(reader.pages)
    except Exception:  # noqa: BLE001
        return None
