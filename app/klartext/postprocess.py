"""Nachbearbeitung des Docling-Ergebnisses.

Drei Dinge, die Docling selbst nicht liefert:

1. Bilder als eigene Dateien statt als base64 mitten im Markdown
2. Verweise aus der PDF (Link-Annotationen), die beim Textexport verloren gehen
3. Erkennung wiederkehrender Kopf- und Fusszeilen

Grundsatz: Die JSON-Ausgabe bleibt vollstaendig — dort wird nichts entfernt.
Nur im Markdown werden wiederkehrende Elemente einmal gesammelt statt auf jeder
Seite wiederholt, und das steht auch so im Ergebnis.
"""

from __future__ import annotations

import base64
import binascii
import io
import logging
import re
from collections import Counter

from pypdf import PdfReader

log = logging.getLogger("klartext.postprocess")

# Ab diesem Anteil an Seiten gilt eine Zeile als wiederkehrendes Seitenelement.
WIEDERHOLUNG_AB = 0.8
MIN_SEITEN_FUER_ERKENNUNG = 4
MAX_BILDER = 300
MAX_BILD_BYTES = 8 * 1024 * 1024

_DATA_URI = re.compile(r"^data:(image/[a-z0-9.+-]+);base64,(.*)$", re.I | re.S)
_ENDUNG = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
           "image/tiff": ".tif", "image/gif": ".gif", "image/bmp": ".bmp"}


# --------------------------------------------------------------------- Bilder


def bilder_ausloesen(struktur: dict) -> list[dict]:
    """Holt die eingebetteten Bilder aus der Docling-Struktur.

    Gibt eine Liste von {'seq', 'page_no', 'mime', 'suffix', 'data'} zurueck und
    ersetzt die base64-Daten in der Struktur durch den spaeteren Dateinamen —
    damit bleibt die JSON-Ausgabe lesbar und trotzdem vollstaendig verweisend.
    """
    bilder: list[dict] = []
    if not isinstance(struktur, dict):
        return bilder

    for eintrag in (struktur.get("pictures") or [])[:MAX_BILDER]:
        if not isinstance(eintrag, dict):
            continue
        bild = eintrag.get("image")
        if not isinstance(bild, dict):
            continue
        uri = bild.get("uri")
        if not isinstance(uri, str):
            continue
        treffer = _DATA_URI.match(uri.strip())
        if not treffer:
            continue
        mime = treffer.group(1).lower()
        try:
            daten = base64.b64decode(treffer.group(2), validate=False)
        except (binascii.Error, ValueError):
            continue
        if not daten or len(daten) > MAX_BILD_BYTES:
            continue

        seq = len(bilder) + 1
        suffix = _ENDUNG.get(mime, ".bin")
        seite = None
        for verweis in (eintrag.get("prov") or []):
            if isinstance(verweis, dict) and isinstance(verweis.get("page_no"), int):
                seite = verweis["page_no"]
                break

        bilder.append({"seq": seq, "page_no": seite, "mime": mime,
                       "suffix": suffix, "data": daten})
        # Verweis statt Rohdaten: die JSON bleibt so unter einem Megabyte.
        bild["uri"] = f"bilder/bild-{seq:03d}{suffix}"
    return bilder


# Docling schreibt bei eingebetteten Bildern die Rohdaten direkt ins Markdown.
# Das macht die Datei unbrauchbar gross — eine 51-seitige PDF ergab 15 MB.
_MD_BILD = re.compile(r"!\[[^\]]*\]\(\s*data:image/[a-z0-9.+-]+;base64,[^)]*\)", re.I)
_MD_PLATZHALTER = re.compile(r"<!--\s*image\s*-->")


def markdown_bilder_verweisen(markdown: str, bilder: list[dict]) -> str:
    """Ersetzt eingebettete Bilddaten durch Verweise auf die abgelegten Dateien."""
    zaehler = {"i": 0}

    def ersetze(_treffer):
        zaehler["i"] += 1
        if zaehler["i"] > len(bilder):
            return "<!-- image -->"
        b = bilder[zaehler["i"] - 1]
        seite = f" (Seite {b['page_no']})" if b.get("page_no") else ""
        return f"![Bild {b['seq']}{seite}](bilder/bild-{b['seq']:03d}{b['suffix']})"

    markdown = _MD_BILD.sub(ersetze, markdown)
    if zaehler["i"] == 0:
        markdown = _MD_PLATZHALTER.sub(ersetze, markdown)
    # Sicherheitsnetz: falls doch noch Rohdaten stehen, werden sie entfernt statt
    # ausgeliefert — eine 15-MB-Markdown-Datei ist fuer niemanden brauchbar.
    return _MD_BILD.sub("<!-- image -->", markdown)


# --------------------------------------------------------------------- Links


def links_lesen(pdf_bytes: bytes) -> list[dict]:
    """Liest die Link-Annotationen einer PDF.

    Docling exportiert nur den Text; die Verweise liegen in einer eigenen
    Annotationsebene und gehen dabei vollstaendig verloren.
    """
    gefunden: list[dict] = []
    try:
        leser = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    except Exception:  # noqa: BLE001 - defekte PDF darf den Auftrag nicht kippen
        return gefunden

    gesehen: set[tuple[int, str]] = set()
    for nummer, seite in enumerate(leser.pages, start=1):
        try:
            annots = seite.get("/Annots") or []
        except Exception:  # noqa: BLE001
            continue
        for annot in annots:
            try:
                objekt = annot.get_object()
                if objekt.get("/Subtype") != "/Link":
                    continue
                aktion = objekt.get("/A") or {}
                ziel = aktion.get("/URI")
                if not ziel:
                    continue
                ziel = str(ziel).strip()
                if not ziel or len(ziel) > 2000:
                    continue
                schluessel = (nummer, ziel)
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                gefunden.append({"page_no": nummer, "url": ziel})
            except Exception:  # noqa: BLE001
                continue
    return gefunden


def markdown_links_anhaengen(markdown: str, links: list[dict]) -> str:
    if not links:
        return markdown
    zeilen = ["", "", "## Verweise im Dokument", "",
              "Diese Verweise liegen in der PDF als anklickbare Verknuepfungen vor "
              "und tauchen im Fliesstext nicht auf.", ""]
    letzte_seite = None
    for eintrag in links:
        if eintrag["page_no"] != letzte_seite:
            letzte_seite = eintrag["page_no"]
            zeilen.append(f"**Seite {letzte_seite}**")
            zeilen.append("")
        zeilen.append(f"- <{eintrag['url']}>")
    zeilen.append("")
    return markdown.rstrip() + "\n".join(zeilen)


# ------------------------------------------------- wiederkehrende Seitenelemente


def _kandidaten_aus_pdf(pdf_bytes: bytes) -> tuple[list[str], int]:
    """Zeilen, die in der Textebene der PDF auf fast jeder Seite stehen.

    Die Textebene ist die verlaessliche Quelle: dort steht ein Wasserzeichen noch
    als eigene Zeile. Im Markdown haengt es spaeter an Absaetzen und in
    Tabellenzellen und ist zeilenweise nicht mehr zu fassen.
    """
    try:
        leser = PdfReader(io.BytesIO(pdf_bytes), strict=False)
        seiten = leser.pages
    except Exception:  # noqa: BLE001
        return [], 0
    if len(seiten) < MIN_SEITEN_FUER_ERKENNUNG:
        return [], len(seiten)

    zaehler: Counter[str] = Counter()
    for seite in seiten:
        try:
            text = seite.extract_text() or ""
        except Exception:  # noqa: BLE001
            continue
        for zeile in {z.strip() for z in text.splitlines()}:
            if 8 <= len(zeile) <= 200:
                zaehler[zeile] += 1

    grenze = len(seiten) * WIEDERHOLUNG_AB
    return [t for t, n in zaehler.most_common() if n >= grenze], len(seiten)


def wiederkehrende_texte(pdf_bytes: bytes, markdown: str) -> list[str]:
    """Findet die Textbausteine, die sich aus dem Markdown entfernen lassen.

    Aus jeder Kandidatenzeile wird die laengste Wortfolge gesucht, die im
    Markdown selbst oft genug vorkommt — Docling kuerzt Wasserzeichen haeufig,
    ein Vergleich auf Gleichheit ginge deshalb ins Leere.
    """
    kandidaten, seiten = _kandidaten_aus_pdf(pdf_bytes)
    if not kandidaten or seiten < MIN_SEITEN_FUER_ERKENNUNG:
        return []

    mindestens = max(3, int(seiten * 0.5))
    treffer: list[str] = []
    for kandidat in kandidaten[:5]:
        woerter = kandidat.split()
        bester = ""
        for anfang in range(len(woerter)):
            for ende in range(len(woerter), anfang + 1, -1):
                folge = " ".join(woerter[anfang:ende])
                if len(folge) < 12 or len(folge) <= len(bester):
                    continue
                if markdown.count(folge) >= mindestens:
                    bester = folge
                    break
        if bester and bester not in treffer:
            treffer.append(bester)
    return treffer


def seitenelemente_zusammenfassen(markdown: str, elemente: list[str]) -> str:
    """Entfernt die Wiederholungen aus dem Fliesstext und nennt sie einmal.

    Nur im Markdown. Die JSON-Ausgabe bleibt unangetastet und vollstaendig.
    """
    if not elemente:
        return markdown

    gekuerzt = markdown
    for text in elemente:
        # Auch ein direkt davorstehendes Copyright-Zeichen mitnehmen.
        gekuerzt = re.sub(r"©\s*" + re.escape(text), "", gekuerzt)
        gekuerzt = gekuerzt.replace(text, "")

        # Docling kuerzt Wasserzeichen in Tabellenzellen oft auf die ersten
        # Woerter. Diese Reste nur dort entfernen, wo sie am Zellen- oder
        # Zeilenende stehen — mitten im Satz koennte dasselbe Wort echt sein.
        woerter = text.split()
        for anzahl in range(len(woerter) - 1, 0, -1):
            rest = " ".join(woerter[:anzahl])
            if len(rest) < 10:
                continue
            gekuerzt = re.sub(
                r"[ \t]*©?[ \t]*" + re.escape(rest) + r"[ \t]*(?=\||\n|$)",
                " ", gekuerzt)
    gekuerzt = re.sub(r"[ \t]{2,}", " ", gekuerzt)
    gekuerzt = re.sub(r" +\|", " |", gekuerzt)
    gekuerzt = re.sub(r"\n{3,}", "\n\n", gekuerzt).strip()

    kopf = ["## Wiederkehrende Seitenelemente", "",
            "Dieser Text steht in der Vorlage auf nahezu jeder Seite "
            "(Kopf- oder Fusszeile, Wasserzeichen). Er ist hier einmal aufgefuehrt "
            "statt auf jeder Seite wiederholt. Die JSON-Ausgabe enthaelt ihn "
            "unveraendert an jeder Fundstelle.", ""]
    for text in elemente:
        kopf.append(f"- {text}")
    kopf.extend(["", "---", ""])
    return "\n".join(kopf) + gekuerzt + "\n"
