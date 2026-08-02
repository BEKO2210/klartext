"""Layouttreue: Gliederung, Tabellen und Lesereihenfolge der Vorlage erhalten.

Fuenf Dinge gehen auf dem Weg nach Markdown verloren, obwohl die Vorlage sie
klar hergibt:

1. **Die Gliederungstiefe bei nummerierten Ueberschriften.** Das Layoutmodell
   erkennt Ueberschriften, aber keine Ebenen — "1", "1.1" und "1.1.1" kommen
   alle als ``##`` heraus. Die Nummer steht im Text und nennt die Ebene selbst;
   daraus wird sie zurueckgerechnet. Die Nummer bleibt dabei unveraendert
   stehen, sie gehoert zur Vorlage.

2. **Die Gliederungstiefe ohne Nummern.** Titel, darunter Abschnitte: Ohne
   Nummer bleibt alles auf einer Ebene. Dann sagt die Schriftgroesse die Ebene
   — sie steckt als Zeilenhoehe in der Struktur. Nur wenn die Groessen sich
   klar trennen; bei einem Scan schwanken sie mit Ober- und Unterlaengen und
   sagen nichts, dort bleibt alles unveraendert.

3. **Verbundene Zellen.** Markdown kennt kein ``rowspan``. Docling fuellt jede
   ueberdeckte Rasterstelle mit demselben Text — aus einer Zelle "Zwischensumme"
   ueber vier Spalten werden vier gleiche Zellen, aus einer zweizeiligen
   Kopfzelle zwei. Genau das macht Rechnungen und Formulare unbrauchbar.
   Solche Tabellen werden deshalb als HTML-Tabelle geschrieben: Markdown
   erlaubt HTML, jeder gaengige Betrachter stellt es dar, und die Struktur
   bleibt erhalten. Tabellen ohne verbundene Zellen bleiben unveraendert im
   gewohnten Markdown-Raster.

4. **Die Lesereihenfolge bei Spaltensatz.** Bei zwei Spalten haengt das
   Layoutmodell die rechte Spalte gern hinter alles andere. Aus der Lage der
   Bloecke auf der Seite laesst sich die Reihenfolge zurueckgewinnen — und ein
   Absatz, den der Spalten- oder Seitenumbruch zerschnitten hat, wieder
   zusammensetzen.

5. **Verschachtelte Listen.** Eine Unterliste ("a., b.") landet auf derselben
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


# ------------------------------------- Gliederung ohne Nummern (Schriftgröße)

# Innerhalb einer Ebene darf die Zeilenhöhe so weit streuen ...
_STUFE_STREUUNG = 0.02
# ... und zwischen zwei Ebenen muss mindestens so viel Abstand liegen.
_STUFE_ABSTAND = 0.08
# Mehr Ebenen als das leitet niemand mehr aus einer Schriftgröße ab.
_STUFE_HOECHSTZAHL = 4
# Zwei Überschriften reichen hier — anders als bei den Nummern, wo drei
# Treffer nötig sind, damit aus Zufallszahlen keine Gliederung wird. Die
# Absicherung ist bei dieser Regel die Trennschärfe, nicht die Menge: ein
# Größensprung von acht Prozent ist eine Stufe der Vorlage, kein Rauschen.
_MINDEST_FUER_GROESSE = 2


def _kopfhoehen(struktur: dict | None) -> dict[str, float]:
    """Zeilenhöhe je Überschrift aus der Docling-Struktur.

    Die Höhe der Bounding-Box ist das einzige Maß für die Schriftgröße, das die
    Struktur hergibt. Bei einer Textebene ist sie exakt; bei einem Scan misst
    sie die Ausdehnung der erkannten Buchstaben und schwankt mit Ober- und
    Unterlängen — dort trägt sie keine Aussage. Genau dafür sind die
    Trennschärfe-Prüfungen unten da.
    """
    hoehen: dict[str, float] = {}
    if not isinstance(struktur, dict):
        return hoehen
    for eintrag in (struktur.get("texts") or []):
        if not isinstance(eintrag, dict) or eintrag.get("label") not in ("section_header", "title"):
            continue
        text = re.sub(r"\s+", " ", (eintrag.get("text") or "")).strip().lower()
        if not text:
            continue
        for stelle in (eintrag.get("prov") or []):
            kasten = (stelle or {}).get("bbox") or {}
            oben, unten = kasten.get("t"), kasten.get("b")
            if isinstance(oben, (int, float)) and isinstance(unten, (int, float)):
                hoehe = abs(oben - unten)
                if hoehe > 0:
                    hoehen[text] = max(hoehen.get(text, 0.0), hoehe)
                break
    return hoehen


def _gruppieren(hoehen: list[float]) -> list[list[float]] | None:
    """Teilt die Höhen in Ebenen — oder gibt nichts zurück, wenn es nicht trägt.

    Getrennt wird an jeder Lücke, die größer ist als der erlaubte Abstand.
    Danach muss jede Gruppe in sich eng sein: eine Gruppe, die selbst weit
    streut, ist keine Ebene, sondern Zufall.
    """
    sortiert = sorted(hoehen, reverse=True)
    gruppen: list[list[float]] = [[sortiert[0]]]
    for hoehe in sortiert[1:]:
        vorherige = gruppen[-1][-1]
        if (vorherige - hoehe) / vorherige > _STUFE_ABSTAND:
            gruppen.append([hoehe])
        else:
            gruppen[-1].append(hoehe)

    if len(gruppen) < 2 or len(gruppen) > _STUFE_HOECHSTZAHL:
        return None
    for gruppe in gruppen:
        if (gruppe[0] - gruppe[-1]) / gruppe[0] > _STUFE_STREUUNG:
            return None
    return gruppen


def ueberschriften_nach_groesse(markdown: str, struktur: dict | None) -> tuple[str, int]:
    """Leitet die Gliederungsebene aus der Schriftgröße ab.

    Für Dokumente ohne Gliederungsnummern — Titel, darunter Abschnitte. Ohne
    diesen Schritt steht dort jede Überschrift auf derselben Stufe, weil das
    Layoutmodell zwar Überschriften erkennt, aber keine Ebenen vergibt.

    Es wird nur eingegriffen, wenn die Größen sich klar in Ebenen trennen: jede
    Ebene in sich eng, zwischen den Ebenen ein deutlicher Sprung. Bei einem Scan
    ist das nie der Fall — dort bleibt alles, wie es ist, statt zu raten.
    """
    hoehen = _kopfhoehen(struktur)
    if not hoehen:
        return markdown, 0

    zeilen = markdown.split("\n")
    im_zaun = False
    treffer: list[tuple[int, int, float]] = []   # Zeile, Stufe, Höhe
    stufen: set[int] = set()
    ohne_hoehe = 0

    for i, zeile in enumerate(zeilen):
        if zeile.lstrip().startswith(_ZAUN):
            im_zaun = not im_zaun
            continue
        if im_zaun:
            continue
        kopf = _UEBERSCHRIFT.match(zeile)
        if not kopf:
            continue
        stufen.add(len(kopf.group(1)))
        text = re.sub(r"\s+", " ", kopf.group(2)).strip().lower()
        hoehe = hoehen.get(text)
        if hoehe is None:
            ohne_hoehe += 1
            continue
        treffer.append((i, len(kopf.group(1)), hoehe))

    if len(treffer) < _MINDEST_FUER_GROESSE or len(stufen) != 1:
        return markdown, 0
    # Wenn ein nennenswerter Teil der Überschriften in der Struktur nicht
    # wiederzufinden ist, stimmt die Zuordnung nicht — dann lieber nichts tun.
    if ohne_hoehe * 4 > len(treffer):
        return markdown, 0

    gruppen = _gruppieren([h for *_, h in treffer])
    if gruppen is None:
        return markdown, 0

    ebene_von_hoehe: dict[float, int] = {}
    for nummer, gruppe in enumerate(gruppen):
        for hoehe in gruppe:
            ebene_von_hoehe[hoehe] = nummer

    basis = stufen.pop()
    geaendert = 0
    for i, stufe, hoehe in treffer:
        neu = min(6, basis + ebene_von_hoehe[hoehe])
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


# ------------------------------------------------- Lesereihenfolge in Spalten

_SEITENMARKE = "<!-- seitenumbruch -->"
# So viele Blöcke muss jede Spalte tragen, damit von Spaltensatz die Rede ist.
_MINDEST_JE_SPALTE = 2


def _textbloecke(struktur: dict | None) -> dict[str, dict]:
    """Fließtext und Überschriften mit ihrer Lage auf der Seite."""
    bloecke: dict[str, dict] = {}
    if not isinstance(struktur, dict):
        return bloecke
    for eintrag in (struktur.get("texts") or []):
        if not isinstance(eintrag, dict):
            continue
        if eintrag.get("label") not in ("text", "section_header", "title"):
            continue
        text = re.sub(r"\s+", " ", (eintrag.get("text") or "")).strip().lower()
        if not text or text in bloecke:
            continue
        stelle = (eintrag.get("prov") or [{}])[0] or {}
        kasten = stelle.get("bbox") or {}
        try:
            links, rechts = float(kasten["l"]), float(kasten["r"])
            oben, unten = float(kasten["t"]), float(kasten["b"])
        except (KeyError, TypeError, ValueError):
            continue
        # Docling liefert je nach Quelle den Ursprung oben oder unten links.
        # Wir rechnen einheitlich "größer heißt weiter oben".
        if str(kasten.get("coord_origin", "")).upper() == "TOPLEFT":
            oben, unten = -oben, -unten
        bloecke[text] = {"l": links, "r": rechts, "t": max(oben, unten),
                         "b": min(oben, unten)}
    return bloecke


def _spaltenfolge(bloecke: list[dict]) -> list[int] | None:
    """Sortiert die Blöcke einer Seite spaltenweise.

    Vorgehen wie beim Lesen: Ein Block, der über die Seitenmitte reicht, gilt
    als durchgehend und schließt die offenen Spalten ab. Alles andere sammelt
    sich in seiner Spalte, bis eine Spalte endet — dann wird von links nach
    rechts ausgegeben.

    Gibt nichts zurück, wenn die Seite gar nicht zweispaltig gesetzt ist.
    """
    if len(bloecke) < 4:
        return None
    mitte = (min(b["l"] for b in bloecke) + max(b["r"] for b in bloecke)) / 2

    def band(block: dict) -> str:
        if block["l"] < mitte < block["r"]:
            return "durch"
        return "links" if block["r"] <= mitte else "rechts"

    if sum(1 for b in bloecke if band(b) == "links") < _MINDEST_JE_SPALTE:
        return None
    if sum(1 for b in bloecke if band(b) == "rechts") < _MINDEST_JE_SPALTE:
        return None

    # Von oben nach unten; bei gleicher Höhe zuerst die linke Spalte.
    folge = sorted(range(len(bloecke)), key=lambda i: (-bloecke[i]["t"], bloecke[i]["l"]))

    def zone_ordnen(teil: list[int]) -> list[int]:
        """Ordnet einen Abschnitt zwischen zwei durchgehenden Blöcken.

        Die eigentliche Spaltenzone ist der Bereich, in dem **beide** Spalten
        Text tragen. Was darüber oder darunter steht, gehört nicht dazu — etwa
        eine Zwischenüberschrift unterhalb beider Spalten, die sonst mitten in
        den Spaltentext geriete.
        """
        links = [i for i in teil if band(bloecke[i]) == "links"]
        rechts = [i for i in teil if band(bloecke[i]) == "rechts"]
        if not links or not rechts:
            return teil

        oben = min(max(bloecke[i]["t"] for i in links),
                   max(bloecke[i]["t"] for i in rechts))
        unten = max(min(bloecke[i]["b"] for i in links),
                    min(bloecke[i]["b"] for i in rechts))
        if unten >= oben:
            # Die Spalten überlappen sich gar nicht — dann steht die eine unter
            # der anderen, und das ist kein Spaltensatz.
            return teil

        darueber = [i for i in teil if bloecke[i]["b"] >= oben]
        darunter = [i for i in teil if bloecke[i]["t"] <= unten]
        kern = [i for i in teil if i not in darueber and i not in darunter]
        return (darueber
                + [i for i in kern if band(bloecke[i]) == "links"]
                + [i for i in kern if band(bloecke[i]) == "rechts"]
                + darunter)

    ergebnis: list[int] = []
    abschnitt: list[int] = []
    for i in folge:
        if band(bloecke[i]) == "durch":
            ergebnis.extend(zone_ordnen(abschnitt))
            abschnitt = []
            ergebnis.append(i)
            continue
        abschnitt.append(i)
    ergebnis.extend(zone_ordnen(abschnitt))
    return ergebnis


def _bloecke_zerlegen(zeilen: list[str]) -> list[dict]:
    """Zerlegt Markdown in Blöcke: Überschrift, Absatz, Tabelle, Liste, Sonstiges."""
    bloecke: list[dict] = []
    i = 0
    im_zaun = False
    while i < len(zeilen):
        zeile = zeilen[i]
        if zeile.lstrip().startswith(_ZAUN):
            im_zaun = not im_zaun
            bloecke.append({"art": "sonst", "zeilen": [zeile]})
            i += 1
            continue
        if im_zaun:
            bloecke.append({"art": "sonst", "zeilen": [zeile]})
            i += 1
            continue
        if not zeile.strip():
            bloecke.append({"art": "leer", "zeilen": [zeile]})
            i += 1
            continue
        if zeile.strip().startswith("<!--"):
            # Seitenmarke und andere Kommentare sind keine Absätze; sie dürfen
            # zwei zusammengehörende Textteile nicht trennen.
            bloecke.append({"art": "sonst", "zeilen": [zeile]})
            i += 1
            continue
        if zeile.lstrip().startswith("<table"):
            block = []
            while i < len(zeilen):
                block.append(zeilen[i])
                if "</table>" in zeilen[i]:
                    i += 1
                    break
                i += 1
            bloecke.append({"art": "tabelle", "zeilen": block})
            continue
        if zeile.startswith("|"):
            block = []
            while i < len(zeilen) and zeilen[i].startswith("|"):
                block.append(zeilen[i])
                i += 1
            bloecke.append({"art": "tabelle", "zeilen": block})
            continue
        kopf = _UEBERSCHRIFT.match(zeile)
        if kopf:
            bloecke.append({"art": "ueberschrift", "zeilen": [zeile],
                            "text": re.sub(r"\s+", " ", kopf.group(2)).strip().lower()})
            i += 1
            continue
        if _ZIFFERNPUNKT.match(zeile) or zeile.lstrip().startswith(("- ", "* ", "+ ")):
            block = []
            while i < len(zeilen) and zeilen[i].strip():
                block.append(zeilen[i])
                i += 1
            bloecke.append({"art": "liste", "zeilen": block})
            continue
        block = []
        while i < len(zeilen) and zeilen[i].strip() and not zeilen[i].startswith("|"):
            block.append(zeilen[i])
            i += 1
        text = re.sub(r"\s+", " ", " ".join(block)).strip().lower()
        bloecke.append({"art": "absatz", "zeilen": block, "text": text})
    return bloecke


def lesereihenfolge_spalten(markdown: str, struktur: dict | None) -> tuple[str, int]:
    """Bringt zweispaltig gesetzte Seiten in die Reihenfolge, in der man liest.

    Bei zwei Spalten hängt das Layoutmodell die rechte Spalte gern hinter alles
    andere, statt sie an der richtigen Stelle einzufügen. Aus der Lage der
    Blöcke auf der Seite lässt sich die Reihenfolge zurückgewinnen.

    Angefasst wird nur, was sich zweifelsfrei zuordnen lässt: Seiten mit
    Tabellen, Listen oder Bildern bleiben unberührt — dort ist der mögliche
    Schaden größer als der Gewinn.
    """
    lage = _textbloecke(struktur)
    if not lage:
        return markdown, 0

    abschnitte = markdown.split(_SEITENMARKE)
    verschoben = 0
    neue_abschnitte: list[str] = []

    for abschnitt in abschnitte:
        bloecke = _bloecke_zerlegen(abschnitt.split("\n"))
        inhalt = [b for b in bloecke if b["art"] not in ("leer", "sonst")]
        # Nur reiner Fließtext: sobald Tabellen oder Listen im Spiel sind,
        # müsste ihre Lage mitgerechnet werden — dafür ist die Zuordnung zu
        # unsicher.
        if not inhalt or any(b["art"] not in ("absatz", "ueberschrift") for b in inhalt):
            neue_abschnitte.append(abschnitt)
            continue
        stellen = [lage.get(b["text"]) for b in inhalt]
        if any(s is None for s in stellen):
            neue_abschnitte.append(abschnitt)
            continue

        folge = _spaltenfolge([s for s in stellen if s])
        if folge is None or folge == list(range(len(inhalt))):
            neue_abschnitte.append(abschnitt)
            continue

        sortiert = [inhalt[i] for i in folge]
        verschoben += sum(1 for alt, neu in zip(inhalt, sortiert) if alt is not neu)

        # Der Abschnitt wird aus den sortierten Blöcken neu gesetzt; die
        # Leerzeilen dazwischen stellt Markdown ohnehin selbst her.
        text = "\n\n".join("\n".join(b["zeilen"]) for b in sortiert)
        neue_abschnitte.append(f"\n{text}\n")

    if not verschoben:
        return markdown, 0
    return _SEITENMARKE.join(neue_abschnitte), verschoben


# Ein Absatz, der am Spalten- oder Seitenumbruch zerschnitten wurde: der erste
# Teil endet ohne Satzzeichen, der zweite beginnt klein. Im Deutschen wie im
# Englischen faengt kein Satz mit einem Kleinbuchstaben an — deshalb traegt
# dieses Merkmal.
_ENDET_OFFEN = re.compile(r"[\w,;–-]$")
_BEGINNT_KLEIN = re.compile(r"^[a-zäöüß]")


def getrennte_absaetze_verbinden(markdown: str) -> tuple[str, int]:
    """Fügt Absätze wieder zusammen, die ein Umbruch zerschnitten hat."""
    zeilen = markdown.split("\n")
    bloecke = _bloecke_zerlegen(zeilen)
    ergebnis: list[dict] = []
    verbunden = 0

    for block in bloecke:
        if (block["art"] == "absatz" and ergebnis):
            # Zwischen den beiden dürfen nur Leerzeilen oder eine Seitenmarke
            # stehen — sonst gehören sie nicht zusammen.
            zwischen = []
            j = len(ergebnis) - 1
            while j >= 0 and ergebnis[j]["art"] in ("leer", "sonst"):
                zwischen.append(ergebnis[j])
                j -= 1
            harmlos = all(b["art"] == "leer"
                          or b["zeilen"] == [_SEITENMARKE] for b in zwischen)
            if (j >= 0 and ergebnis[j]["art"] == "absatz" and harmlos
                    and _ENDET_OFFEN.search(ergebnis[j]["zeilen"][-1].rstrip())
                    and _BEGINNT_KLEIN.match(block["zeilen"][0].lstrip())):
                ergebnis[j]["zeilen"][-1] = (ergebnis[j]["zeilen"][-1].rstrip() + " "
                                             + block["zeilen"][0].lstrip())
                ergebnis[j]["zeilen"].extend(block["zeilen"][1:])
                verbunden += 1
                continue
        ergebnis.append(block)

    if not verbunden:
        return markdown, 0
    return "\n".join(zeile for block in ergebnis for zeile in block["zeilen"]), verbunden


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
