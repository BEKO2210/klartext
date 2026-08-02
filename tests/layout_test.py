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
