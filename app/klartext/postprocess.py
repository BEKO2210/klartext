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
import unicodedata
from collections import Counter

from pypdf import PdfReader

from . import i18n

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


def markdown_links_anhaengen(markdown: str, links: list[dict],
                             lang: str = i18n.DEFAULT_LANG) -> str:
    if not links:
        return markdown
    zeilen = ["", "", "## " + i18n.translate(lang, "result.links.h"), "",
              i18n.translate(lang, "result.links.intro"), ""]
    letzte_seite = None
    for eintrag in links:
        if eintrag["page_no"] != letzte_seite:
            letzte_seite = eintrag["page_no"]
            zeilen.append(
                "**" + i18n.translate(lang, "result.links.page", page=letzte_seite) + "**")
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


def seitenelemente_zusammenfassen(markdown: str, elemente: list[str],
                                  lang: str = i18n.DEFAULT_LANG) -> str:
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

    kopf = ["## " + i18n.translate(lang, "result.repeated.h"), "",
            i18n.translate(lang, "result.repeated.intro"), ""]
    for text in elemente:
        kopf.append(f"- {text}")
    kopf.extend(["", "---", ""])
    return "\n".join(kopf) + gekuerzt + "\n"


# --------------------------------------------------- Schreibweisen geradeziehen

# Datum zuerst schuetzen: 10.08.2021 darf nicht zu 10,08.2021 werden.
_DATUM = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")
# Uhrzeit und Netzadressen schuetzen, damit die Doppelpunkt-Regel sie nicht trifft.
_UHRZEIT = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")
_ADRESSE = re.compile(r"\b[a-z][a-z0-9+.-]*://\S+", re.I)

_DEZIMAL_PUNKT = re.compile(r"(?<=\d)\.(?=\d{2}\b)")
_KOMMA_ZAHL = re.compile(r"\d,\d{2}\b")
_PUNKT_ZAHL = re.compile(r"\d\.\d{2}\b")

_DOPPELPUNKT_ZAHL = re.compile(r"(?<=[A-Za-zÄÖÜäöüß]):(?=\d)")
_WAEHRUNG_KLEBT = re.compile(r"(?<=[A-Za-zÄÖÜäöüß0-9])(?=[€$£])")


def schreibweisen_glaetten(markdown: str) -> tuple[str, int]:
    """Zieht rein mechanische Schreibfehler der Texterkennung gerade.

    Ausdruecklich **keine** Rechtschreibkorrektur: es wird kein Wort geraten und
    kein Woerterbuch befragt. Verbessert werden nur Dinge, die sich aus dem
    Dokument selbst zweifelsfrei ergeben — Trennzeichen in Zahlen und fehlende
    Leerzeichen. Tippfehler der Vorlage bleiben erhalten.
    """
    schutz: list[str] = []

    def merken(treffer):
        schutz.append(treffer.group(0))
        return f"\x00{len(schutz) - 1}\x00"

    text = _ADRESSE.sub(merken, markdown)
    text = _DATUM.sub(merken, text)
    text = _UHRZEIT.sub(merken, text)

    aenderungen = 0

    # Dezimaltrennzeichen nur angleichen, wenn das Dokument erkennbar deutsch
    # formatiert ist — sonst waere es geraten statt hergeleitet.
    if len(_KOMMA_ZAHL.findall(text)) > len(_PUNKT_ZAHL.findall(text)):
        text, n = _DEZIMAL_PUNKT.subn(",", text)
        aenderungen += n

    text, n = _DOPPELPUNKT_ZAHL.subn(": ", text)
    aenderungen += n
    text, n = _WAEHRUNG_KLEBT.subn(" ", text)
    aenderungen += n

    def zurueck(treffer):
        return schutz[int(treffer.group(1))]

    return re.sub(r"\x00(\d+)\x00", zurueck, text), aenderungen


# --- Auflösung prüfen ----------------------------------------------------
#
# Die Texterkennung braucht eine Mindestgroesse je Buchstabe. Ist die Vorlage zu
# klein fotografiert oder zu grob gescannt, verwechselt sie einzelne Zeichen —
# das laesst sich nachtraeglich nicht reparieren, nur melden.
#
# Bei Bildern wird die tatsaechliche Schrifthoehe aus dem Erkennungsergebnis
# gemessen statt aus der Bildgroesse geraten: ein kleiner Ausschnitt mit grosser
# Schrift ist gut lesbar, eine ganze Seite mit derselben Pixelzahl nicht.
#
# Bei PDF geht das nicht — dort sind die Textmasse in Punkt und nicht in Pixel
# angegeben, eine normale 10-Punkt-Schrift waere von einem groben Scan nicht zu
# unterscheiden. Deshalb dort der Umweg ueber die eingebetteten Bilder.
#
# Bilddateien werden nur an den Kopfdaten vermessen, die Bilddaten selbst nie
# entpackt: Bilddecoder auf fremde Uploads anzuwenden waere eine unnoetig grosse
# Angriffsflaeche.

# Unterhalb dieser Zeilenhoehe in Bildpunkten wird die Zeichenerkennung
# unzuverlaessig. Gemessen: eine unbrauchbar gelesene Rechnung lag bei 11,
# ein sauber gelesenes Testbild bei 23.
_MINDEST_ZEILENHOEHE = 16
# Unter so vielen Punkten je Zoll wird ein Seitenscan unzuverlaessig.
_MINDEST_PUNKTE_JE_ZOLL = 150


def _groesse_png(kopf: bytes) -> tuple[int, int] | None:
    if not kopf.startswith(b"\x89PNG\r\n\x1a\n") or kopf[12:16] != b"IHDR":
        return None
    return int.from_bytes(kopf[16:20], "big"), int.from_bytes(kopf[20:24], "big")


def _groesse_jpeg(daten: bytes) -> tuple[int, int] | None:
    if not daten.startswith(b"\xff\xd8"):
        return None
    i = 2
    ende = len(daten)
    while i + 9 < ende:
        if daten[i] != 0xFF:
            i += 1
            continue
        marker = daten[i + 1]
        # Fuellbytes und Segmente ohne Laengenangabe ueberspringen.
        if marker in (0xFF, 0x01) or 0xD0 <= marker <= 0xD9:
            i += 2
            continue
        laenge = int.from_bytes(daten[i + 2 : i + 4], "big")
        if laenge < 2:
            return None
        # SOF0-SOF15, ohne DHT (C4), DAC (CC) und die Restart-Marker.
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            hoehe = int.from_bytes(daten[i + 5 : i + 7], "big")
            breite = int.from_bytes(daten[i + 7 : i + 9], "big")
            return breite, hoehe
        i += 2 + laenge
    return None


def _groesse_bmp(kopf: bytes) -> tuple[int, int] | None:
    if not kopf.startswith(b"BM") or len(kopf) < 26:
        return None
    breite = int.from_bytes(kopf[18:22], "little", signed=True)
    hoehe = int.from_bytes(kopf[22:26], "little", signed=True)
    return abs(breite), abs(hoehe)


def _groesse_webp(kopf: bytes) -> tuple[int, int] | None:
    if not (kopf.startswith(b"RIFF") and kopf[8:12] == b"WEBP"):
        return None
    art = kopf[12:16]
    if art == b"VP8X" and len(kopf) >= 30:
        breite = int.from_bytes(kopf[24:27], "little") + 1
        hoehe = int.from_bytes(kopf[27:30], "little") + 1
        return breite, hoehe
    if art == b"VP8 " and len(kopf) >= 30:
        return (
            int.from_bytes(kopf[26:28], "little") & 0x3FFF,
            int.from_bytes(kopf[28:30], "little") & 0x3FFF,
        )
    if art == b"VP8L" and len(kopf) >= 25:
        bits = int.from_bytes(kopf[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return None


def _groesse_tiff(daten: bytes) -> tuple[int, int] | None:
    if daten[:2] == b"II":
        ordnung = "little"
    elif daten[:2] == b"MM":
        ordnung = "big"
    else:
        return None

    def zahl(pos: int, laenge: int) -> int:
        return int.from_bytes(daten[pos : pos + laenge], ordnung)

    start = zahl(4, 4)
    if start + 2 > len(daten):
        return None
    masse: dict[int, int] = {}
    anzahl = zahl(start, 2)
    for n in range(anzahl):
        feld = start + 2 + n * 12
        if feld + 12 > len(daten):
            break
        kennung = zahl(feld, 2)
        if kennung in (256, 257):
            # Typ 3 ist ein 2-Byte-Wert, Typ 4 ein 4-Byte-Wert; beide stehen
            # linksbuendig im Feld.
            typ = zahl(feld + 2, 2)
            masse[kennung] = zahl(feld + 8, 2 if typ == 3 else 4)
    if 256 in masse and 257 in masse:
        return masse[256], masse[257]
    return None


def bildgroesse(daten: bytes) -> tuple[int, int] | None:
    """Liest Breite und Hoehe aus den Kopfdaten, ohne das Bild zu entpacken."""
    kopf = daten[:4096]
    for leser in (_groesse_png, _groesse_bmp, _groesse_webp):
        masse = leser(kopf)
        if masse:
            return masse
    for leser in (_groesse_jpeg, _groesse_tiff):
        masse = leser(daten)
        if masse:
            return masse
    return None


def _zeilenhoehe(struktur: dict) -> float | None:
    """Mittlere Hoehe der erkannten Textzeilen, in Einheiten der Seite."""
    hoehen: list[float] = []
    for eintrag in struktur.get("texts", []) or []:
        for stelle in eintrag.get("prov", []) or []:
            kasten = stelle.get("bbox") or {}
            oben, unten = kasten.get("t"), kasten.get("b")
            if isinstance(oben, (int, float)) and isinstance(unten, (int, float)):
                hoehen.append(abs(oben - unten))
    if len(hoehen) < 3:
        # Zu wenige Zeilen fuer eine belastbare Aussage.
        return None
    hoehen.sort()
    return hoehen[len(hoehen) // 2]


def aufloesung_pruefen(daten: bytes, mime: str, struktur: dict | None = None,
                       lang: str = i18n.DEFAULT_LANG) -> str | None:
    """Meldet zu grobe Vorlagen. Gibt einen Hinweistext zurueck oder nichts."""
    if mime == "application/pdf":
        return _aufloesung_pdf(daten, lang)
    if not mime.startswith("image/"):
        return None
    if not isinstance(struktur, dict):
        return None

    hoehe = _zeilenhoehe(struktur)
    if hoehe is None or hoehe >= _MINDEST_ZEILENHOEHE:
        return None

    masse = bildgroesse(daten)
    groesse = (i18n.translate(lang, "note.image_lowres.size",
                              width=masse[0], height=masse[1]) if masse else "")
    return i18n.translate(lang, "note.image_lowres", height=round(hoehe),
                          size=groesse, min=_MINDEST_ZEILENHOEHE)


def _bilder_einer_seite(seite) -> list[tuple[int, int]]:
    """Liest Breite und Hoehe der eingebetteten Bilder aus dem PDF-Verzeichnis.

    Bewusst ueber die Katalogeintraege und nicht ueber ``page.images``: letzteres
    entpackt die Bilddaten (und braucht dafuer Pillow). Die Masse stehen als
    Metadaten im Stream-Verzeichnis und sind ohne Dekodieren lesbar.
    """
    masse: list[tuple[int, int]] = []
    try:
        mittel = seite["/Resources"]["/XObject"].get_object()
    except Exception:
        return masse
    for schluessel in list(mittel.keys()):
        try:
            objekt = mittel[schluessel].get_object()
            if objekt.get("/Subtype") != "/Image":
                continue
            breite = int(objekt.get("/Width", 0))
            hoehe = int(objekt.get("/Height", 0))
        except Exception:
            continue
        if breite > 0 and hoehe > 0:
            masse.append((breite, hoehe))
    return masse


def _aufloesung_pdf(daten: bytes, lang: str = i18n.DEFAULT_LANG) -> str | None:
    """Prueft eingescannte PDF-Seiten: kein Textlayer, nur ein grobes Bild.

    Der Hinweis erscheint nur, wenn das Dokument ueberwiegend aus solchen Seiten
    besteht. Ein sauberes Textdokument mit einem Bild als Titelseite ist kein
    Scan — dort waere die Meldung schlicht falsch.
    """
    try:
        leser = PdfReader(io.BytesIO(daten))
        seiten = leser.pages[:5]
    except Exception:  # pragma: no cover - kaputte Dateien meldet die Engine
        return None
    if not seiten:
        return None

    schlechteste: tuple[int, int, float] | None = None
    grobe_seiten = 0
    for seite in seiten:
        try:
            # Seiten mit Textlayer brauchen keine Texterkennung.
            if len((seite.extract_text() or "").strip()) > 100:
                continue
            breite_punkt = float(seite.mediabox.width)
            hoehe_punkt = float(seite.mediabox.height)
        except Exception:
            continue
        if breite_punkt <= 0 or hoehe_punkt <= 0:
            continue
        seiten_verhaeltnis = hoehe_punkt / breite_punkt

        for breite, hoehe in _bilder_einer_seite(seite):
            # Schmale Streifen sind Linien oder Logos, keine Seitenscans.
            if breite < 200 or hoehe < 200:
                continue
            # Ein Seitenscan hat ungefaehr das Seitenverhaeltnis der Seite.
            # Ohne diese Pruefung wuerde jede grosse Grafik als Scan gelten:
            # aus ihrer Pixelzahl allein laesst sich nicht ablesen, wie gross
            # sie auf der Seite tatsaechlich abgebildet wird.
            if not 0.75 <= (hoehe / breite) / seiten_verhaeltnis <= 1.33:
                continue
            punkte_je_zoll = breite / (breite_punkt / 72.0)
            if round(punkte_je_zoll) >= _MINDEST_PUNKTE_JE_ZOLL:
                continue
            grobe_seiten += 1
            if schlechteste is None or punkte_je_zoll < schlechteste[2]:
                schlechteste = (breite, hoehe, punkte_je_zoll)
            break

    if schlechteste is None or grobe_seiten * 2 < len(seiten):
        return None
    breite, hoehe, punkte_je_zoll = schlechteste
    return i18n.translate(lang, "note.pdf_lowres", width=breite, height=hoehe,
                          dpi=round(punkte_je_zoll), min=_MINDEST_PUNKTE_JE_ZOLL)


# --- Einheiten prüfen ----------------------------------------------------
#
# Die Texterkennung verwechselt bei manchen Schriftarten ganze Einheiten:
# aus "g/dl" wird "IP/6", aus "U/l" wird "i/n" oder "v/n". Solche Zellen werden
# **gemeldet, nie geändert**. Eine automatische Korrektur waere geraten, und ein
# stillschweigend auf "mg/dl" gesetzter Wert, wo "g/dl" stand, ist um den Faktor
# 1000 falsch und faellt niemandem mehr auf. Ein sichtbar kaputtes "IP/6" ist
# ungefaehrlich, weil man es sofort erkennt.

_EINHEIT_SPALTEN = frozenset({
    "einheit", "einheiten", "masseinheit", "maßeinheit", "dimension",
    "unit", "units", "uom",
})

# Zellinhalte, die keine Einheit sein sollen und trotzdem in Ordnung sind.
_KEINE_EINHEIT = frozenset({"", "-", "–", "—", "/", "n.a.", "k.a.", "n/a", "."})

# Bekannte Einheiten, klein geschrieben und ohne Leerzeichen. Bewusst breit
# angelegt: eine zu kurze Liste meldet staendig Fehlalarme, und ein Hinweis,
# dem man nicht traut, wird ueberlesen.
_EINHEITEN = frozenset("""
g/dl g/l mg/dl mg/l mg/ml µg/l µg/dl µg/ml ng/ml ng/l ng/dl pg/ml pg fl
mmol/l µmol/l nmol/l pmol/l mol/l mval/l meq/l mosmol/kg
u/l u/ml mu/l mu/ml ku/l iu/l iu/ml ie/l ie/ml
% ‰ /l /ml /nl /µl /pl mio/µl mio/l tsd/µl tsd/l mrd/l
mm/h ml/min s sek min h std mg/g g/24h mg/24h µg/24h
kpa mmhg ph ratio titer index score
kg g mg µg ng t m cm mm µm nm km m² m³ l ml µl dl hl
tag tage woche monat jahr stk stück st paket
€ eur ct °c °f k v a w kw kwh wh hz khz mhz ghz
b kb mb gb tb bar pa mpa n nm rpm u/min km/h m/s ppm db
""".split())


def _einheit_normal(text: str) -> str:
    """Vereinheitlicht Schreibweisen, die dieselbe Einheit meinen."""
    wert = unicodedata.normalize("NFC", text or "").strip()
    # Mikro-Zeichen und griechisches My meinen dasselbe.
    wert = wert.replace("μ", "µ")
    wert = wert.replace("⁄", "/").replace("∕", "/")
    wert = re.sub(r"\s*/\s*", "/", wert)
    wert = re.sub(r"\s+", " ", wert)
    return wert.rstrip(".").lower()


# Ausgeschriebene Einheiten wie "Meter", "Stück" oder "Std." lassen sich nicht
# sinnvoll aufzaehlen — der Wortschatz waere endlos und jede Luecke ein
# Fehlalarm. Deshalb gilt: was wie ein Wort aussieht, wird nicht gemeldet.
# Gemeldet wird nur, was erkennbar kein Wort ist — Zeichensalat mit Schraeg-
# strichen oder Ziffern, also genau das Muster der Lesefehler ("i/n", "IP/6").
_WORTAEHNLICH = re.compile(r"^[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß.\- ]{1,}$")

# Zusammengesetzte Einheiten lassen sich nicht aufzaehlen: "°C/W", "ppm/°C",
# "%/V", "µA" sind alle gueltig und standen in keiner Liste — ein Datenblatt hat
# dafuer prompt neun Fehlalarme erzeugt. Deshalb wird zerlegt statt aufgezaehlt:
# an Bruch- und Malzeichen trennen, Hochzahlen abschneiden, Vorsatz abtrennen.
# Die Pruefung ist bewusst grosszuegig — eine faelschlich akzeptierte Einheit
# kostet nur eine ausgebliebene Meldung, ein Fehlalarm dagegen die Glaubwuerdigkeit.
_GRUNDEINHEITEN = frozenset("""
m g s a k mol cd n pa j w c v f ω ohm si wb t h lm lx bq gy sv kat
l t min h d °c °f % ‰ ppm ppb bar ev hz b byte bit u iu ie da val db rpm px °
mmhg mval eq osm mos
""".split())

_VORSAETZE = ("q", "r", "y", "z", "e", "p", "t", "g", "m", "k", "h", "da",
              "d", "c", "µ", "n", "f", "a")


def _teil_ist_einheit(teil: str) -> bool:
    teil = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]|\^-?\d+|(?<=[a-zäöüß°])\d+$", "", teil).strip()
    if not teil:
        return False
    if teil in _GRUNDEINHEITEN:
        return True
    for vorsatz in _VORSAETZE:
        if teil.startswith(vorsatz) and teil[len(vorsatz):] in _GRUNDEINHEITEN:
            return True
    return False


def _ist_einheit(normal: str) -> bool:
    if normal in _EINHEITEN:
        return True
    teile = [t for t in re.split(r"[/*·×]", normal) if t.strip()]
    if not teile or len(teile) > 3:
        return False
    return all(_teil_ist_einheit(t) for t in teile)


def einheiten_pruefen(struktur: dict, grenze: int = 30) -> list[dict]:
    """Meldet Zellen einer Einheiten-Spalte, die keine bekannte Einheit sind.

    Gibt Fundstellen mit Seite, Zeilenbezeichnung und dem **unveraenderten**
    Wert zurueck. Der Text im Ergebnis bleibt, wie die Erkennung ihn gelesen hat.
    """
    if not isinstance(struktur, dict):
        return []
    funde: list[dict] = []

    for tabelle in struktur.get("tables", []) or []:
        daten = tabelle.get("data") or {}
        zellen = daten.get("table_cells") or []
        if not zellen:
            continue

        seite = None
        for stelle in tabelle.get("prov", []) or []:
            if isinstance(stelle.get("page_no"), int):
                seite = stelle["page_no"]
                break

        # Welche Spalten tragen eine Einheiten-Ueberschrift?
        spalten: dict[int, str] = {}
        for zelle in zellen:
            if not zelle.get("column_header"):
                continue
            if _einheit_normal(zelle.get("text", "")) in _EINHEIT_SPALTEN:
                spalte = zelle.get("start_col_offset_idx")
                if isinstance(spalte, int):
                    spalten[spalte] = (zelle.get("text") or "").strip()
        if not spalten:
            continue

        # Zeilenbeschriftung ist die erste Zelle der Zeile.
        beschriftung: dict[int, str] = {}
        for zelle in zellen:
            zeile = zelle.get("start_row_offset_idx")
            if zelle.get("start_col_offset_idx") == 0 and isinstance(zeile, int):
                beschriftung[zeile] = (zelle.get("text") or "").strip()

        for zelle in zellen:
            if zelle.get("column_header"):
                continue
            spalte = zelle.get("start_col_offset_idx")
            if spalte not in spalten:
                continue
            roh = (zelle.get("text") or "").strip()
            normal = _einheit_normal(roh)
            if normal in _KEINE_EINHEIT or _ist_einheit(normal):
                continue
            if _WORTAEHNLICH.match(roh):
                continue
            zeile = zelle.get("start_row_offset_idx")
            funde.append({
                "seite": seite,
                "zeile": beschriftung.get(zeile, "") if isinstance(zeile, int) else "",
                "spalte": spalten[spalte],
                "wert": roh,
            })
            if len(funde) >= grenze:
                return funde
    return funde
