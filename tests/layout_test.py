#!/usr/bin/env python3
"""Prueft die Layouttreue deterministisch gegen nachgebaute Docling-Strukturen.

Aufruf:  python3 tests/layout_test.py
         docker exec -i klartext-web python - < tests/layout_test.py

Absicht wie bei der Einheitenpruefung in e2e.py: geprueft werden die Regeln
selbst, nicht die Tagesform der Texterkennung. Kein Netz, keine Datenbank.
"""

from __future__ import annotations

import pathlib
import sys

_HIER = pathlib.Path(__file__).resolve().parent if "__file__" in globals() else None
for pfad in (_HIER.parent / "app" if _HIER else None, pathlib.Path("/app")):
    if pfad and pfad.is_dir():
        sys.path.insert(0, str(pfad))

from klartext import layout  # noqa: E402

_fehler = 0


def pruefe(name: str, ok: bool, detail: str = "") -> None:
    global _fehler
    print(("  ok  " if ok else "FEHLT ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        _fehler += 1


# --------------------------------------------------------------- Gliederung

DOKUMENT = "\n".join([
    "## 1 Allgemeine Geschäftsbedingungen",
    "",
    "Text.",
    "",
    "## 1.1 Geltungsbereich",
    "",
    "## 1.1.1 Abweichende Vereinbarungen",
    "",
    "## 1.2 Vergütung",
    "",
    "## 2 Haftung",
    "",
    "## 2.1 Haftungsumfang",
])

neu, anzahl = layout.gliederung_wiederherstellen(DOKUMENT)
pruefe("Gliederung: Ebenen aus der Nummer hergeleitet",
       "## 1 Allgemeine" in neu and "### 1.1 Geltungsbereich" in neu
       and "#### 1.1.1 Abweichende" in neu and "### 2.1 Haftungsumfang" in neu,
       neu)
pruefe("Gliederung: vier Zeilen geaendert", anzahl == 4, str(anzahl))
pruefe("Gliederung: Nummern bleiben unveraendert im Text",
       all(t in neu for t in ("1.1.1 Abweichende Vereinbarungen", "2.1 Haftungsumfang")))

# Ohne Untergliederung darf nichts passieren.
flach = "## 1 Eins\n\n## 2 Zwei\n\n## 3 Drei"
pruefe("Gliederung: eine Ebene bleibt unangetastet",
       layout.gliederung_wiederherstellen(flach) == (flach, 0))

# Bringt das Dokument eigene Ebenen mit, ist die Vorlage die bessere Quelle.
eigene = "# 1 Eins\n\n## 1.1 Eins-Eins\n\n## 1.2 Eins-Zwei\n\n## 2 Zwei"
pruefe("Gliederung: vorhandene Ebenen werden nicht ueberschrieben",
       layout.gliederung_wiederherstellen(eigene) == (eigene, 0))

# Zahlen, die keine Gliederung sind, duerfen nichts ausloesen.
zufall = "## 2021.10 Bericht\n\n## 4711.22 Aktenzeichen\n\n## 815.99 Posten"
_, n_zufall = layout.gliederung_wiederherstellen(zufall)
pruefe("Gliederung: Aktenzeichen ohne Elternnummer aendern nichts", n_zufall == 0,
       str(n_zufall))

# In Codebloecken wird nichts angefasst.
zaun = "```\n## 1 Eins\n## 1.1 Zwei\n## 1.2 Drei\n```\n"
pruefe("Gliederung: Codebloecke bleiben unberuehrt",
       layout.gliederung_wiederherstellen(zaun) == (zaun, 0))


# ------------------------------------------ Gliederung ohne Nummer (Größe)

def kopf(text, hoehe, links=60.0, rechts=300.0, oben=None):
    oben = hoehe * 100 if oben is None else oben
    return {"label": "section_header", "text": text,
            "prov": [{"page_no": 1, "bbox": {"l": links, "r": rechts, "t": oben,
                                             "b": oben - hoehe,
                                             "coord_origin": "BOTTOMLEFT"}}]}


OHNE_NUMMER = "## Rechnung 2026-0417\n\nText.\n\n## Leistungen\n\n## Zahlungsbedingungen"
STRUKTUR_KLAR = {"texts": [kopf("Rechnung 2026-0417", 7.19), kopf("Leistungen", 6.07),
                           kopf("Zahlungsbedingungen", 6.07)]}

neu, anzahl = layout.ueberschriften_nach_groesse(OHNE_NUMMER, STRUKTUR_KLAR)
pruefe("Größe: Titel bleibt oben, Abschnitte eine Ebene tiefer",
       "## Rechnung 2026-0417" in neu and "### Leistungen" in neu
       and "### Zahlungsbedingungen" in neu and anzahl == 2, neu)

# Ein Scan: die Höhen schwanken mit Ober- und Unterlängen, eine Ebene ist
# daraus nicht ableitbar. Genau dann darf nichts passieren.
STRUKTUR_SCAN = {"texts": [kopf("Rechnung 2026-0417", 17.82), kopf("Leistungen", 16.98),
                           kopf("Zahlungsbedingungen", 18.25)]}
pruefe("Größe: schwankende Scanhöhen aendern nichts",
       layout.ueberschriften_nach_groesse(OHNE_NUMMER, STRUKTUR_SCAN) == (OHNE_NUMMER, 0))

# Gleiche Größe heißt gleiche Ebene.
STRUKTUR_GLEICH = {"texts": [kopf("Rechnung 2026-0417", 6.07), kopf("Leistungen", 6.07),
                             kopf("Zahlungsbedingungen", 6.07)]}
pruefe("Größe: eine einzige Größe bleibt eine Ebene",
       layout.ueberschriften_nach_groesse(OHNE_NUMMER, STRUKTUR_GLEICH) == (OHNE_NUMMER, 0))

pruefe("Größe: ohne Struktur passiert nichts",
       layout.ueberschriften_nach_groesse(OHNE_NUMMER, {}) == (OHNE_NUMMER, 0))

# Steht eine Überschrift nicht in der Struktur, ist die Zuordnung unsicher.
STRUKTUR_LUECKIG = {"texts": [kopf("Rechnung 2026-0417", 7.19), kopf("Leistungen", 6.07)]}
pruefe("Größe: fehlende Zuordnung laesst das Dokument in Ruhe",
       layout.ueberschriften_nach_groesse(OHNE_NUMMER, STRUKTUR_LUECKIG) == (OHNE_NUMMER, 0))


# --------------------------------------------------------- Lesereihenfolge

def block(text, links, rechts, oben, unten, marke="text"):
    return {"label": marke, "text": text,
            "prov": [{"page_no": 1, "bbox": {"l": links, "r": rechts, "t": oben,
                                             "b": unten, "coord_origin": "BOTTOMLEFT"}}]}


# Zwei Spalten, darunter ein durchgehender Schlussabsatz. Docling haengt die
# rechte Spalte hinten an — so sieht das Markdown vorher aus.
SPALTEN_MD = "\n".join([
    "Einleitung über die volle Breite.", "",
    "Links oben beginnt der Text.", "",
    "Links unten geht er weiter.", "",
    "Schlusswort über die volle Breite.", "",
    "Rechts oben steht die Fortsetzung.", "",
    "Rechts unten endet die Spalte.",
])
SPALTEN_STRUKTUR = {"texts": [
    block("Einleitung über die volle Breite.", 60, 520, 750, 740),
    block("Links oben beginnt der Text.", 60, 280, 700, 620),
    block("Links unten geht er weiter.", 60, 280, 600, 520),
    block("Schlusswort über die volle Breite.", 60, 520, 300, 280),
    block("Rechts oben steht die Fortsetzung.", 310, 530, 700, 620),
    block("Rechts unten endet die Spalte.", 310, 530, 600, 520),
]}

neu, verschoben = layout.lesereihenfolge_spalten(SPALTEN_MD, SPALTEN_STRUKTUR)
reihenfolge = [z for z in neu.split("\n") if z.strip()]
pruefe("Spalten: erst links, dann rechts, dann der Schlussabsatz",
       reihenfolge == ["Einleitung über die volle Breite.",
                       "Links oben beginnt der Text.",
                       "Links unten geht er weiter.",
                       "Rechts oben steht die Fortsetzung.",
                       "Rechts unten endet die Spalte.",
                       "Schlusswort über die volle Breite."] and verschoben > 0,
       str(reihenfolge))

# Einspaltig: nichts anfassen.
EIN_MD = "Erster Absatz.\n\nZweiter Absatz.\n\nDritter Absatz.\n\nVierter Absatz."
EIN_STRUKTUR = {"texts": [
    block("Erster Absatz.", 60, 520, 700, 680),
    block("Zweiter Absatz.", 60, 520, 660, 640),
    block("Dritter Absatz.", 60, 520, 620, 600),
    block("Vierter Absatz.", 60, 520, 580, 560),
]}
pruefe("Spalten: einspaltiger Satz bleibt unveraendert",
       layout.lesereihenfolge_spalten(EIN_MD, EIN_STRUKTUR) == (EIN_MD, 0))

# Sobald eine Tabelle im Abschnitt steht, wird nicht sortiert.
MIT_TABELLE = SPALTEN_MD + "\n\n| A | B |\n|---|---|\n| 1 | 2 |"
pruefe("Spalten: mit Tabelle im Abschnitt wird nicht umgestellt",
       layout.lesereihenfolge_spalten(MIT_TABELLE, SPALTEN_STRUKTUR) == (MIT_TABELLE, 0))


# ------------------------------------------------------ Getrennte Absaetze

GETRENNT = ("Ohne ihn laufen einzelne Stränge zu warm und andere zu kalt,\n\n"
            "und die Regelung gleicht das mit einer höheren Vorlauftemperatur aus.")
neu, anzahl = layout.getrennte_absaetze_verbinden(GETRENNT)
pruefe("Absätze: am Umbruch zerschnittener Absatz wird verbunden",
       neu.count("\n\n") == 0 and "zu kalt, und die Regelung" in neu and anzahl == 1, neu)

UEBER_SEITE = ("Der Satz bricht hier ab,\n\n<!-- seitenumbruch -->\n\n"
               "und geht auf der nächsten Seite weiter.")
_, anzahl_seite = layout.getrennte_absaetze_verbinden(UEBER_SEITE)
pruefe("Absätze: auch über den Seitenumbruch hinweg", anzahl_seite == 1, str(anzahl_seite))

VOLLSTAENDIG = "Der erste Satz ist zu Ende.\n\nDer zweite beginnt groß."
pruefe("Absätze: vollstaendige Saetze bleiben getrennt",
       layout.getrennte_absaetze_verbinden(VOLLSTAENDIG) == (VOLLSTAENDIG, 0))

MIT_KOPF = "Der Satz bricht ab,\n\n## Überschrift\n\nund hier geht es klein weiter."
pruefe("Absätze: über eine Überschrift hinweg wird nicht verbunden",
       layout.getrennte_absaetze_verbinden(MIT_KOPF) == (MIT_KOPF, 0))


# ----------------------------------------------------------------- Tabellen

def zelle(zeile, spalte, text, hoch=1, breit=1, kopf=False):
    return {"text": text, "start_row_offset_idx": zeile, "start_col_offset_idx": spalte,
            "end_row_offset_idx": zeile + hoch, "end_col_offset_idx": spalte + breit,
            "row_span": hoch, "col_span": breit, "column_header": kopf, "row_header": False}


ZELLEN = [
    zelle(0, 0, "Position", hoch=2, kopf=True),
    zelle(0, 1, "Leistung", breit=2, kopf=True),
    zelle(0, 3, "Betrag", hoch=2, kopf=True),
    zelle(1, 1, "Beschreibung", kopf=True),
    zelle(1, 2, "Menge", kopf=True),
    zelle(2, 0, "1"), zelle(2, 1, "Wartung"), zelle(2, 2, "2 h"), zelle(2, 3, "170,00 €"),
    zelle(3, 0, "Zwischensumme", breit=3), zelle(3, 3, "170,00 €"),
]
# Das Raster ist die flach gefuellte Fassung — genau die, aus der Docling das
# Markdown baut.
RASTER = [
    [{"text": "Position"}, {"text": "Leistung"}, {"text": "Leistung"}, {"text": "Betrag"}],
    [{"text": "Position"}, {"text": "Beschreibung"}, {"text": "Menge"}, {"text": "Betrag"}],
    [{"text": "1"}, {"text": "Wartung"}, {"text": "2 h"}, {"text": "170,00 €"}],
    [{"text": "Zwischensumme"}, {"text": "Zwischensumme"}, {"text": "Zwischensumme"},
     {"text": "170,00 €"}],
]
TABELLE = {"data": {"table_cells": ZELLEN, "num_rows": 4, "num_cols": 4, "grid": RASTER}}

MARKDOWN = "\n".join([
    "## Rechnung",
    "",
    "| Position      | Leistung      | Leistung      | Betrag   |",
    "|---------------|---------------|---------------|----------|",
    "| Position      | Beschreibung  | Menge         | Betrag   |",
    "| 1             | Wartung       | 2 h           | 170,00 € |",
    "| Zwischensumme | Zwischensumme | Zwischensumme | 170,00 € |",
    "",
    "Danach geht der Text weiter.",
])

ergebnis, ersetzt = layout.verbundene_tabellen_erhalten(MARKDOWN, {"tables": [TABELLE]})
pruefe("Tabelle: eine Tabelle ersetzt", ersetzt == 1, str(ersetzt))
pruefe("Tabelle: Verbuende stehen als rowspan/colspan",
       '<th rowspan="2">Position</th>' in ergebnis
       and '<th colspan="2">Leistung</th>' in ergebnis
       and '<td colspan="3">Zwischensumme</td>' in ergebnis, ergebnis)
pruefe("Tabelle: kein doppelter Text mehr",
       ergebnis.count("Zwischensumme") == 1 and ergebnis.count("Leistung") == 1, ergebnis)
pruefe("Tabelle: Kopf und Rumpf getrennt",
       "<thead>" in ergebnis and "<tbody>" in ergebnis
       and ergebnis.index("<thead>") < ergebnis.index("<tbody>"))
pruefe("Tabelle: Text davor und danach bleibt stehen",
       ergebnis.startswith("## Rechnung") and ergebnis.endswith("Danach geht der Text weiter."))
pruefe("Tabelle: kein Markdown-Raster mehr uebrig", "|---" not in ergebnis)

# Tabelle ohne Verbuende bleibt Markdown.
schlicht_zellen = [zelle(0, 0, "A", kopf=True), zelle(0, 1, "B", kopf=True),
                   zelle(1, 0, "1"), zelle(1, 1, "2")]
schlicht = {"data": {"table_cells": schlicht_zellen, "num_rows": 2, "num_cols": 2,
                     "grid": [[{"text": "A"}, {"text": "B"}], [{"text": "1"}, {"text": "2"}]]}}
schlicht_md = "| A | B |\n|---|---|\n| 1 | 2 |"
pruefe("Tabelle: ohne Verbund bleibt das Markdown-Raster",
       layout.verbundene_tabellen_erhalten(schlicht_md, {"tables": [schlicht]})
       == (schlicht_md, 0))

# Passt die Kopfzeile nicht, wird nichts ersetzt.
fremd = "| X | Y | Z | W |\n|---|---|---|---|\n| 1 | 2 | 3 | 4 |"
pruefe("Tabelle: ohne passende Kopfzeile wird nichts ersetzt",
       layout.verbundene_tabellen_erhalten(fremd, {"tables": [TABELLE]}) == (fremd, 0))

# Spitze Klammern im Zellentext duerfen kein HTML erzeugen.
gefaehrlich = [zelle(0, 0, "<script>alert(1)</script>", breit=2, kopf=True),
               zelle(1, 0, "a"), zelle(1, 1, "b")]
gefahr_tab = {"data": {"table_cells": gefaehrlich, "num_rows": 2, "num_cols": 2,
                       "grid": [[{"text": "<script>alert(1)</script>"},
                                 {"text": "<script>alert(1)</script>"}],
                                [{"text": "a"}, {"text": "b"}]]}}
gefahr_md = ("| <script>alert(1)</script> | <script>alert(1)</script> |\n"
             "|---|---|\n| a | b |")
gefahr_aus, _ = layout.verbundene_tabellen_erhalten(gefahr_md, {"tables": [gefahr_tab]})
pruefe("Tabelle: Zellentext wird maskiert",
       "<script>" not in gefahr_aus and "&lt;script&gt;" in gefahr_aus, gefahr_aus)

# Mehrere Tabellen: nur die mit Verbund wird ersetzt, die Reihenfolge stimmt.
zwei_md = schlicht_md + "\n\n" + "\n".join(MARKDOWN.split("\n")[2:7])
zwei_aus, zwei_n = layout.verbundene_tabellen_erhalten(
    zwei_md, {"tables": [schlicht, TABELLE]})
pruefe("Tabelle: in einem Dokument mit mehreren Tabellen trifft es die richtige",
       zwei_n == 1 and zwei_aus.startswith("| A | B |") and "<table>" in zwei_aus, zwei_aus)


# ------------------------------------------------------------------- Listen

LISTE = "\n".join([
    "5. Anlage abschalten",
    "6. Druck ablassen",
    "- a. Ventil oben",
    "- b. Ventil unten",
    "7. Dichtung tauschen",
])
liste_neu, liste_n = layout.listen_verschachteln(LISTE)
pruefe("Liste: Unterliste eingerueckt",
       "   - a. Ventil oben" in liste_neu and "   - b. Ventil unten" in liste_neu
       and liste_n == 2, liste_neu)
pruefe("Liste: Nummern der Vorlage unveraendert",
       liste_neu.startswith("5. Anlage") and liste_neu.endswith("7. Dichtung tauschen"))

# Eigenstaendige Buchstabenliste bleibt, wie sie ist.
eigen = "- a. Erstens\n- b. Zweitens\n\nText."
pruefe("Liste: eigenstaendige Liste bleibt flach",
       layout.listen_verschachteln(eigen) == (eigen, 0))

# Luecken in der Buchstabenfolge sind kein Beleg.
lueckig = "1. Eins\n- a. Alpha\n- c. Gamma\n2. Zwei"
pruefe("Liste: luecken in der Buchstabenfolge aendern nichts",
       layout.listen_verschachteln(lueckig) == (lueckig, 0))

print()
print("Alle Pruefungen bestanden." if _fehler == 0 else f"{_fehler} Pruefung(en) fehlgeschlagen.")
sys.exit(1 if _fehler else 0)
