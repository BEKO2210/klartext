"""Layouttreue: Gliederung und Tabellenstruktur der Vorlage erhalten.

Drei Dinge gehen auf dem Weg nach Markdown verloren, obwohl die Vorlage sie
klar hergibt:

1. **Die Gliederungstiefe.** Das Layoutmodell erkennt Ueberschriften, aber keine
   Ebenen — "1", "1.1" und "1.1.1" kommen alle als ``##`` heraus. Die Nummer
   steht im Text und nennt die Ebene selbst; daraus wird sie zurueckgerechnet.
   Die Nummer bleibt dabei unveraendert stehen, sie gehoert zur Vorlage.

2. **Verbundene Zellen.** Markdown kennt kein ``rowspan``. Docling fuellt jede
   ueberdeckte Rasterstelle mit demselben Text — aus einer Zelle "Zwischensumme"
   ueber vier Spalten werden vier gleiche Zellen, aus einer zweizeiligen
   Kopfzelle zwei. Genau das macht Rechnungen und Formulare unbrauchbar.
   Solche Tabellen werden deshalb als HTML-Tabelle geschrieben: Markdown
   erlaubt HTML, jeder gaengige Betrachter stellt es dar, und die Struktur
   bleibt erhalten. Tabellen ohne verbundene Zellen bleiben unveraendert im
   gewohnten Markdown-Raster.

3. **Verschachtelte Listen.** Eine Unterliste ("a., b.") landet auf derselben
   Ebene wie die Hauptliste. Sie wird nur dann eingerueckt, wenn die Vorlage
   selbst es zweifelsfrei zeigt: Buchstabenmarken zwischen zwei Zifferpunkten.

Grundsatz wie im ganzen Projekt: nichts erfinden. Jede Regel prueft sich selbst
und laesst das Dokument unveraendert, sobald die Belege nicht reichen. Die
JSON-Ausgabe wird hier ohnehin nicht angefasst — dort stehen ``row_span`` und
``col_span`` vollstaendig.
"""

from __future__ import annotations

import logging
import re

log = logging.getLogger("klartext.layout")

# --------------------------------------------------------------- Gliederung

_UEBERSCHRIFT = re.compile(r"^(#{1,6})[ \t]+(\S.*?)[ \t]*$")
# "1", "1.2", "1.2.3" — auch mit abschliessendem Punkt, danach muss Text folgen.
_NUMMER = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){0,5})\.?[ \t\u00a0]+\S")
_ZAUN = "```"

# Weniger Ueberschriften sagen nichts: zwei zufaellig mit Zahl beginnende
# Zeilen ergeben noch keine Gliederung.
_MINDEST_UEBERSCHRIFTEN = 3


def gliederung_wiederherstellen(markdown: str) -> tuple[str, int]:
    """Stellt die Ebenen nummerierter Ueberschriften wieder her.

    Aendert nur die Anzahl der Rautezeichen. Der Text der Ueberschrift — und
    damit die Nummer der Vorlage — bleibt Zeichen fuer Zeichen stehen.
    """
    zeilen = markdown.split("\n")
    im_zaun = False
    treffer: list[tuple[int, int, str, int]] = []  # Zeile, Stufe, Nummer, Tiefe
    stufen: set[int] = set()

    for i, zeile in enumerate(zeilen):
        if zeile.lstrip().startswith(_ZAUN):
            im_zaun = not im_zaun
            continue
        if im_zaun:
            continue
        kopf = _UEBERSCHRIFT.match(zeile)
        if not kopf:
            continue
        nummer = _NUMMER.match(kopf.group(2))
        if not nummer:
            continue
        stufe = len(kopf.group(1))
        stufen.add(stufe)
        gliederung = nummer.group(1)
        treffer.append((i, stufe, gliederung, gliederung.count(".") + 1))

    if len(treffer) < _MINDEST_UEBERSCHRIFTEN:
        return markdown, 0
    # Bringt das Dokument schon eigene Ebenen mit (etwa aus einer DOCX-Datei),
    # dann ist die Vorlage die bessere Quelle als unsere Herleitung.
    if len(stufen) != 1:
        return markdown, 0

    tiefen = {t for *_, t in treffer}
    if len(tiefen) < 2:
        return markdown, 0

    # Selbstpruefung: zu einer "1.1" sollte vorher eine "1" stehen. Fehlt das
    # bei der Mehrheit, ist es keine Gliederung, sondern Zufall (Jahreszahlen,
    # Beträge, Aktenzeichen).
    kleinste = min(tiefen)
    bekannt: set[str] = set()
    verwaist = 0
    for _, _, gliederung, tiefe in treffer:
        if tiefe > kleinste and gliederung.rsplit(".", 1)[0] not in bekannt:
            verwaist += 1
        bekannt.add(gliederung)
    if verwaist * 2 > len(treffer):
        return markdown, 0

    basis = stufen.pop()
    geaendert = 0
    for i, stufe, _, tiefe in treffer:
        neu = min(6, basis + tiefe - kleinste)
        if neu == stufe:
            continue
        zeilen[i] = "#" * neu + zeilen[i][stufe:]
        geaendert += 1
    return "\n".join(zeilen), geaendert


# ------------------------------------------------------------------ Tabellen

_TRENNZEILE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")


def _ganzzahl(wert, ersatz: int = -1) -> int:
    return wert if isinstance(wert, int) and not isinstance(wert, bool) else ersatz


def _zellentext(zelle: dict) -> str:
    roh = (zelle.get("text") or "").replace("\r\n", "\n").strip()
    roh = roh.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\n+", "<br>", roh)


def hat_verbundene_zellen(tabelle: dict) -> bool:
    for zelle in ((tabelle.get("data") or {}).get("table_cells") or []):
        if not isinstance(zelle, dict):
            continue
        if _ganzzahl(zelle.get("row_span"), 1) > 1 or _ganzzahl(zelle.get("col_span"), 1) > 1:
            return True
    return False


def html_tabelle(tabelle: dict) -> str | None:
    """Baut aus der Docling-Tabelle eine HTML-Tabelle mit rowspan/colspan.

    Gibt nichts zurueck, wenn die Struktur unvollstaendig ist — dann bleibt das
    Markdown-Raster stehen, das ist immer noch besser als eine halbe Tabelle.
    """
    daten = tabelle.get("data") or {}
    zellen = [z for z in (daten.get("table_cells") or []) if isinstance(z, dict)]
    anzahl_zeilen = _ganzzahl(daten.get("num_rows"), 0)
    anzahl_spalten = _ganzzahl(daten.get("num_cols"), 0)
    if not zellen or anzahl_zeilen <= 0 or anzahl_spalten <= 0:
        return None

    belegt: set[tuple[int, int]] = set()
    reihen: list[list[tuple[dict, int, int]]] = [[] for _ in range(anzahl_zeilen)]

    for zelle in sorted(zellen, key=lambda z: (_ganzzahl(z.get("start_row_offset_idx")),
                                               _ganzzahl(z.get("start_col_offset_idx")))):
        zeile = _ganzzahl(zelle.get("start_row_offset_idx"))
        spalte = _ganzzahl(zelle.get("start_col_offset_idx"))
        if not (0 <= zeile < anzahl_zeilen) or not (0 <= spalte < anzahl_spalten):
            continue
        if (zeile, spalte) in belegt:
            # Kommt vor, wenn eine Zelle doppelt gemeldet wird: die zweite
            # wuerde die Zeile verschieben.
            continue
        hoch = max(1, min(_ganzzahl(zelle.get("row_span"), 1), anzahl_zeilen - zeile))
        breit = max(1, min(_ganzzahl(zelle.get("col_span"), 1), anzahl_spalten - spalte))
        for r in range(zeile, zeile + hoch):
            for s in range(spalte, spalte + breit):
                belegt.add((r, s))
        reihen[zeile].append((zelle, hoch, breit))

    if not any(reihen):
        return None

    # Fuehrende Zeilen, die ausschliesslich Kopfzellen beginnen, werden zum
    # Tabellenkopf. Danach faengt der Rumpf an.
    kopf_bis = 0
    for r in range(anzahl_zeilen):
        if reihen[r] and all(z.get("column_header") for z, _, _ in reihen[r]):
            kopf_bis = r + 1
        else:
            break

    def zeile_bauen(r: int) -> str | None:
        if not reihen[r]:
            return None
        stuecke = []
        for zelle, hoch, breit in reihen[r]:
            kopf = bool(zelle.get("column_header") or zelle.get("row_header"))
            marke = "th" if kopf else "td"
            merkmale = ""
            if hoch > 1:
                merkmale += f' rowspan="{hoch}"'
            if breit > 1:
                merkmale += f' colspan="{breit}"'
            if kopf and zelle.get("row_header") and not zelle.get("column_header"):
                merkmale += ' scope="row"'
            stuecke.append(f"<{marke}{merkmale}>{_zellentext(zelle)}</{marke}>")
        return "<tr>" + "".join(stuecke) + "</tr>"

    kopfzeilen = [z for z in (zeile_bauen(r) for r in range(kopf_bis)) if z]
    rumpfzeilen = [z for z in (zeile_bauen(r) for r in range(kopf_bis, anzahl_zeilen)) if z]
    if not kopfzeilen and not rumpfzeilen:
        return None

    aus = ["<table>"]
    if kopfzeilen:
        aus += ["<thead>", *kopfzeilen, "</thead>"]
    if rumpfzeilen:
        aus += ["<tbody>", *rumpfzeilen, "</tbody>"]
    aus.append("</table>")
    return "\n".join(aus)


def _signatur(texte) -> tuple[str, ...]:
    return tuple(re.sub(r"\s+", " ", (t or "")).strip().lower() for t in texte)


def _blocksignatur(zeile: str) -> tuple[str, ...]:
    return _signatur(zeile.strip().strip("|").split("|"))


def _tabellensignatur(tabelle: dict) -> tuple[str, ...]:
    raster = (tabelle.get("data") or {}).get("grid") or []
    if not raster:
        return ()
    return _signatur((z or {}).get("text") for z in raster[0])


def _tabellenbloecke(zeilen: list[str]) -> list[tuple[int, int]]:
    """Findet die Markdown-Tabellen als Zeilenbereiche [Anfang, Ende)."""
    bloecke: list[tuple[int, int]] = []
    im_zaun = False
    i = 0
    while i < len(zeilen):
        if zeilen[i].lstrip().startswith(_ZAUN):
            im_zaun = not im_zaun
            i += 1
            continue
        if (not im_zaun and zeilen[i].startswith("|")
                and i + 1 < len(zeilen) and _TRENNZEILE.match(zeilen[i + 1])):
            anfang = i
            i += 2
            while i < len(zeilen) and zeilen[i].startswith("|"):
                i += 1
            bloecke.append((anfang, i))
            continue
        i += 1
    return bloecke


def verbundene_tabellen_erhalten(markdown: str, struktur: dict | None) -> tuple[str, int]:
    """Ersetzt flachgeklopfte Tabellen durch HTML-Tabellen mit den Verbuenden.

    Zugeordnet wird ueber die Kopfzeile: nur wenn die erste Zeile des
    Markdown-Blocks Zelle fuer Zelle zur Tabelle in der Struktur passt, wird
    ersetzt. Passt sie nicht, bleibt der Block unangetastet — lieber eine flache
    Tabelle als eine an der falschen Stelle eingesetzte.
    """
    if not isinstance(struktur, dict):
        return markdown, 0
    tabellen = [t for t in (struktur.get("tables") or []) if isinstance(t, dict)]
    if not tabellen:
        return markdown, 0

    zeilen = markdown.split("\n")
    bloecke = _tabellenbloecke(zeilen)
    if not bloecke:
        return markdown, 0

    ersetzungen: list[tuple[int, int, str]] = []
    zeiger = 0
    for anfang, ende in bloecke:
        signatur = _blocksignatur(zeilen[anfang])
        passend = None
        for j in range(zeiger, len(tabellen)):
            if _tabellensignatur(tabellen[j]) == signatur:
                passend = j
                break
        if passend is None:
            continue
        zeiger = passend + 1
        tabelle = tabellen[passend]
        if not hat_verbundene_zellen(tabelle):
            continue
        html = html_tabelle(tabelle)
        if html:
            ersetzungen.append((anfang, ende, html))

    for anfang, ende, html in reversed(ersetzungen):
        zeilen[anfang:ende] = html.split("\n")
    return "\n".join(zeilen), len(ersetzungen)


# -------------------------------------------------------------------- Listen

# "5. Text" oder "5) Text" — die Nummer der Vorlage, so wie Docling sie liefert.
_ZIFFERNPUNKT = re.compile(r"^\d{1,3}[.)][ \t]+\S")
# "- a. Text": eine Unterliste, die Docling auf die Hauptebene gelegt hat.
_BUCHSTABENPUNKT = re.compile(r"^- ([a-z]|[ivx]{1,4})[.)][ \t]+\S")


def listen_verschachteln(markdown: str) -> tuple[str, int]:
    """Rueckt Unterlisten ein, die auf der Hauptebene gelandet sind.

    Nur dort, wo die Vorlage es selbst belegt: ein Block mit Buchstabenmarken
    steht zwischen zwei nummerierten Punkten, und die Buchstaben laufen luecken-
    los in der Reihenfolge des Alphabets. Alles andere bleibt, wie es ist.
    """
    zeilen = markdown.split("\n")
    geaendert = 0
    i = 0
    im_zaun = False
    while i < len(zeilen):
        if zeilen[i].lstrip().startswith(_ZAUN):
            im_zaun = not im_zaun
            i += 1
            continue
        if im_zaun or not _BUCHSTABENPUNKT.match(zeilen[i]):
            i += 1
            continue

        # Davor muss ein nummerierter Punkt stehen.
        if i == 0 or not _ZIFFERNPUNKT.match(zeilen[i - 1]):
            i += 1
            continue

        block: list[int] = []
        marken: list[str] = []
        j = i
        while j < len(zeilen):
            marke = _BUCHSTABENPUNKT.match(zeilen[j])
            if marke is None:
                break
            block.append(j)
            marken.append(marke.group(1))
            j += 1
        # Danach muss die Hauptliste weitergehen — sonst war es vielleicht doch
        # eine eigenstaendige Liste.
        if j >= len(zeilen) or not _ZIFFERNPUNKT.match(zeilen[j]):
            i = j
            continue
        lueckenlos = all(len(m) == 1 for m in marken) and [
            ord(m) for m in marken] == list(range(ord(marken[0]), ord(marken[0]) + len(marken)))
        if len(block) < 2 or not lueckenlos:
            i = j
            continue

        for k in block:
            # Drei Leerzeichen: so weit reicht der Text eines Punktes "5. ".
            zeilen[k] = "   " + zeilen[k]
            geaendert += 1
        i = j

    return "\n".join(zeilen), geaendert
