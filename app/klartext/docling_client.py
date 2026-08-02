"""Serverseitiger Zugriff auf Docling Serve.

Der API-Key verlässt nie den Server. Es werden ausschließlich Datei-Uploads
gesendet — keine URLs, damit Docling nie für uns ins Netz greift.
"""

from __future__ import annotations

import json
import logging

import httpx

from .config import CONFIG

log = logging.getLogger("klartext.docling")


def _custom_presets() -> dict[str, dict]:
    """Eigene OCR-Konfigurationen aus der Umgebung, defensiv gelesen."""
    if not CONFIG.ocr_custom_presets_json.strip():
        return {}
    try:
        daten = json.loads(CONFIG.ocr_custom_presets_json)
    except ValueError:
        log.error("OCR_CUSTOM_PRESETS ist kein gueltiges JSON — wird ignoriert.")
        return {}
    if not isinstance(daten, dict):
        return {}
    return {k: v for k, v in daten.items() if isinstance(v, dict) and v.get("kind")}


_CUSTOM_PRESETS = _custom_presets()


class ConversionError(Exception):
    """Fachlicher Fehler mit einem Code, den das Frontend übersetzt."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class DoclingClient:
    def __init__(self) -> None:
        headers = {"Accept": "application/json"}
        if CONFIG.docling_api_key:
            headers["X-Api-Key"] = CONFIG.docling_api_key
        self._client = httpx.AsyncClient(
            base_url=CONFIG.docling_url,
            headers=headers,
            timeout=httpx.Timeout(connect=10.0, read=CONFIG.docling_timeout_s + 30, write=120.0, pool=30.0),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def healthy(self) -> bool:
        try:
            resp = await self._client.get("/health", timeout=10.0)
            return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    async def convert(self, filename: str, data: bytes, mime: str, max_pages: int,
                      engine: str | None = None) -> dict:
        """Konvertiert genau eine Datei. Gibt {'markdown', 'json', 'pages', 'status'} zurück."""
        # httpx akzeptiert bei Multipart nur ein Dict — Mehrfachwerte als Liste.
        # Eine Liste von Tupeln führt in httpx 0.28 zu
        # "Attempted to send an sync request with an AsyncClient instance".
        form: dict[str, object] = {
            "to_formats": ["md", "json"],
            "target_type": "inbody",
            # Verlustarm: Tabellenstruktur an, genauer Modus, Lesereihenfolge aus dem Layoutmodell
            "do_table_structure": "true",
            "table_mode": CONFIG.table_mode,
            "table_cell_matching": "true",
            "do_ocr": "true",
            "force_ocr": "false",
            "pdf_backend": "docling_parse",
            "pipeline": "standard",
            # Bilder werden eingebettet geliefert und danach von uns als eigene
            # Dateien abgelegt — sonst gingen alle Abbildungen des Dokuments verloren.
            "image_export_mode": "embedded",
            "include_images": "true",
            "include_page_images": "false",
            # Keine externen Dienste, keine Bild-/Formel-/Code-Anreicherung durch Modelle,
            # die den Originaltext umschreiben könnten.
            "do_code_enrichment": "false",
            "do_formula_enrichment": "false",
            "do_picture_classification": "false",
            "do_picture_description": "false",
            "do_chart_extraction": "false",
            "abort_on_error": "false",
            "document_timeout": str(CONFIG.docling_timeout_s),
            "page_range": ["1", str(max_pages)],
            "md_page_break_placeholder": "<!-- seitenumbruch -->",
        }
        # Entweder ein eingebauter Preset-Name (rapidocr, tesseract, ...) oder
        # eine eigene Konfiguration aus OCR_CUSTOM_PRESETS — dann geht die
        # vollstaendige Engine-Konfiguration je Anfrage mit.
        gewaehlt = engine or CONFIG.ocr_engine
        eigene = _CUSTOM_PRESETS.get(gewaehlt)
        if eigene is not None:
            form["ocr_preset"] = "auto"
            form["ocr_custom_config"] = json.dumps(eigene)
        else:
            form["ocr_preset"] = gewaehlt

        langs = [l.strip() for l in CONFIG.ocr_lang.split(",") if l.strip()]
        if langs:
            form["ocr_lang"] = langs
        # Tabellenmodell nur benennen, wenn ausdruecklich eines gewaehlt ist —
        # sonst gilt der eingebaute Standard (v1 accurate ueber table_mode).
        if CONFIG.table_preset:
            form["table_structure_preset"] = CONFIG.table_preset

        try:
            resp = await self._client.post(
                "/v1/convert/file",
                data=form,
                files=[("files", (filename, data, mime))],
            )
        except httpx.TimeoutException:
            raise ConversionError("timeout") from None
        except httpx.HTTPError:
            raise ConversionError("engine_unreachable") from None

        if resp.status_code == 413:
            raise ConversionError("file_too_large")
        if resp.status_code >= 500:
            raise ConversionError("engine_error")
        if resp.status_code >= 400:
            # Details bewusst nicht an den Benutzer geben, nur intern protokollieren.
            log.warning("Docling lehnte Anfrage ab: HTTP %s", resp.status_code)
            raise ConversionError("unsupported")

        payload = resp.json()
        status = str(payload.get("status", "")).lower()
        document = payload.get("document") or {}
        markdown = document.get("md_content")
        structured = document.get("json_content")

        if status in {"failure", "skipped"} or markdown is None:
            categories = {str(e.get("category", "")).lower() for e in payload.get("errors") or []}
            if "timeout" in categories:
                raise ConversionError("timeout")
            raise ConversionError("conversion_failed")

        pages = 0
        if isinstance(structured, dict):
            page_map = structured.get("pages")
            if isinstance(page_map, dict):
                pages = len(page_map)
            elif isinstance(page_map, list):
                pages = len(page_map)

        return {
            "markdown": markdown,
            "json": structured,
            "pages": pages or 1,
            "status": status,
            "partial": status == "partial_success",
        }
