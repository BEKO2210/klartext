"""Struktur aus HTML und aus Markdown lesen — und beide vergleichen.

Der Messstand vergleicht nicht Zeichenketten, sondern Strukturen: Überschriften
mit ihrer Ebene, Tabellenzellen mit ihren Verbünden, Listenpunkte mit ihrer
Tiefe, den Fließtext als Ganzes. Aus der Quelle (HTML) kommt die Wahrheit, aus
dem Ergebnis (Markdown) die Messung — beide werden mit demselben Code in
dieselbe Form gebracht, damit der Vergleich nicht am Parser hängt.

Bewusst ohne fremde Bibliotheken: der Messstand soll auf jedem Rechner laufen,
auf dem der Dienst läuft.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from html.parser import HTMLParser

# ---------------------------------------------------------------- Normalisieren

_WEICH = {
    " ": " ", " ": " ", " ": " ", " ": " ",
    "„": '"', "“": '"', "”": '"', "»": '"', "«": '"', "‟": '"',
    "‘": "'", "’": "'", "‚": "'",
    "–": "-", "—": "-", "‑": "-", "−": "-",
    "…": "...", "×": "x", "·": " ",
    # Die Texterkennung liest das angekreuzte Kästchen gern als mathematisches
    # Zeichen. Dasselbe Symbol, anderer Codepunkt — kein Lesefehler.
    "⊠": "☒", "⊡": "☐", "□": "☐", "■": "☒",
}


def normal(text: str) -> str:
    """Vereinheitlicht, was für die Bewertung keinen Unterschied macht.

    Anführungszeichen, Strichlängen und Leerzeichenarten sind Geschmack der
    Vorlage, kein Erkennungsfehler. Umlaute, Ziffern und Einheiten bleiben
    unangetastet — dort zählt jedes Zeichen.
    """
    text = unicodedata.normalize("NFC", text or "")
    for alt, neu in _WEICH.items():
        text = text.replace(alt, neu)
    return re.sub(r"\s+", " ", text).strip()


def schluessel(text: str) -> str:
    """Vergleichsform: zusätzlich ohne Groß-/Kleinschreibung und Randzeichen."""
    return normal(text).lower().strip(" .:;|-")


# ------------------------------------------------------------------ Datenmodell


def leere_struktur() -> dict:
    return {"ueberschriften": [], "absaetze": [], "listen": [], "tabellen": [],
            "volltext": ""}


def _tabelle(zellen: list[dict]) -> dict:
    zeilen = max((z["z"] + z["zs"] for z in zellen), default=0)
    spalten = max((z["s"] + z["ss"] for z in zellen), default=0)
    return {"zeilen": zeilen, "spalten": spalten, "zellen": zellen}


# ------------------------------------------------------------------ HTML lesen


class _HtmlLeser(HTMLParser):
    """Liest die Quelldokumente. Sie sind selbst geschrieben und schlicht:
    Überschriften, Absätze, Listen, Tabellen — mehr kommt nicht vor."""

    BLOCK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.aus = leere_struktur()
        self._text: list[str] = []
        # Blockelemente können ineinander stehen: ein Listenpunkt trägt eine
        # eigene Unterliste. Ohne Stapel ginge der äußere Punkt verloren.
        self._stapel: list[tuple[str, int, list[str]]] = []
        self._listentiefe = 0
        self._ueberspringen = 0        # Kopf-/Fußzeile: wiederkehrendes Seitenelement
        self._tabellen: list[list[dict]] = []
        self._belegt: list[set[tuple[int, int]]] = []
        self._zeile = -1
        self._offene_zelle: dict | None = None
        self._volltext: list[str] = []

    # -- Hilfen ------------------------------------------------------------
    def _text_uebernehmen(self) -> str:
        text = normal("".join(self._text))
        self._text = []
        return text

    def _naechste_spalte(self) -> int:
        belegt = self._belegt[-1]
        spalte = 0
        while (self._zeile, spalte) in belegt:
            spalte += 1
        return spalte

    # -- Ereignisse --------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        werte = dict(attrs)
        klassen = (werte.get("class") or "").split()
        if "kopfzeile" in klassen or "fusszeile" in klassen:
            self._ueberspringen += 1
            return
        if self._ueberspringen:
            return

        if tag == "table":
            self._tabellen.append([])
            self._belegt.append(set())
            self._zeile = -1
        elif tag == "tr" and self._tabellen:
            self._zeile += 1
        elif tag in ("td", "th") and self._tabellen:
            spalte = self._naechste_spalte()
            hoch = max(1, int(werte.get("rowspan", 1) or 1))
            breit = max(1, int(werte.get("colspan", 1) or 1))
            for z in range(self._zeile, self._zeile + hoch):
                for s in range(spalte, spalte + breit):
                    self._belegt[-1].add((z, s))
            self._offene_zelle = {"z": self._zeile, "s": spalte, "zs": hoch,
                                  "ss": breit, "kopf": tag == "th", "text": ""}
            self._text = []
        elif tag in ("ol", "ul"):
            self._listentiefe += 1
        elif tag in self.BLOCK:
            self._stapel.append((tag, max(0, self._listentiefe - 1), []))

    def handle_endtag(self, tag):
        if tag in ("div", "span") and self._ueberspringen:
            self._ueberspringen -= 1
            return
        if self._ueberspringen:
            return

        if tag == "table" and self._tabellen:
            zellen = self._tabellen.pop()
            self._belegt.pop()
            if zellen:
                self.aus["tabellen"].append(_tabelle(zellen))
        elif tag in ("td", "th") and self._offene_zelle is not None:
            text = self._text_uebernehmen()
            self._offene_zelle["text"] = text
            self._tabellen[-1].append(self._offene_zelle)
            self._offene_zelle = None
            if text:
                self._volltext.append(text)
        elif tag in ("ol", "ul"):
            self._listentiefe = max(0, self._listentiefe - 1)
        elif tag in self.BLOCK and self._stapel and self._stapel[-1][0] == tag:
            _, tiefe, teile = self._stapel.pop()
            text = normal("".join(teile))
            if not text:
                return
            self._volltext.append(text)
            if tag.startswith("h") and len(tag) == 2:
                self.aus["ueberschriften"].append({"stufe": int(tag[1]), "text": text})
            elif tag == "li":
                self.aus["listen"].append({"tiefe": tiefe, "text": text})
            else:
                self.aus["absaetze"].append(text)

    def handle_data(self, data):
        if self._ueberspringen:
            return
        if self._offene_zelle is not None:
            self._text.append(data)
        elif self._stapel:
            self._stapel[-1][2].append(data)


def aus_html(quelle: str) -> dict:
    leser = _HtmlLeser()
    leser.feed(quelle)
    leser.close()
    leser.aus["volltext"] = normal(" ".join(leser._volltext))
    return leser.aus


# -------------------------------------------------------------- Markdown lesen

_MD_UEBERSCHRIFT = re.compile(r"^(#{1,6})[ \t]+(\S.*?)[ \t]*$")
_MD_TRENNZEILE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")
_MD_LISTE = re.compile(r"^([ \t]*)(?:[-*+]|\d{1,3}[.)])[ \t]+(\S.*)$")
_MD_BILD = re.compile(r"^!\[[^\]]*\]\([^)]*\)\s*$")
# Ankreuzfeld ("- [x] …") und Aufzählungsmarke innerhalb eines Punktes
# ("- a. …"). Beides ist Marke, nicht Inhalt: in der Quelle steht sie gar nicht,
# dort trägt das <li> sie implizit. Der Haken selbst (☒/☐) bleibt stehen —
# angekreuzt oder nicht ist Inhalt.
_MD_HAKEN = re.compile(r"^\[[ xX]\][ \t]+")
_MD_MARKE_IM_PUNKT = re.compile(r"^(?:[a-z]|[ivx]{1,4}|\d{1,3})[.)][ \t]+(?=\S)")
_MD_MARKE = re.compile(r"^(?:<!--.*-->|---+)\s*$")
# Abschnitte, die der Dienst selbst anfügt — sie stehen nicht in der Vorlage und
# dürfen die Messung weder verbessern noch verschlechtern.
_ZUSATZ = ("verweise im dokument", "links in the document",
           "wiederkehrende seitenelemente", "repeating page elements")


class _TabellenLeser(HTMLParser):
    """Liest die HTML-Tabellen, die der Dienst für verbundene Zellen schreibt."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tabellen: list[dict] = []
        self._zellen: list[dict] = []
        self._belegt: set[tuple[int, int]] = set()
        self._zeile = -1
        self._offen: dict | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        werte = dict(attrs)
        if tag == "table":
            self._zellen, self._belegt, self._zeile = [], set(), -1
        elif tag == "tr":
            self._zeile += 1
        elif tag in ("td", "th"):
            spalte = 0
            while (self._zeile, spalte) in self._belegt:
                spalte += 1
            hoch = max(1, int(werte.get("rowspan", 1) or 1))
            breit = max(1, int(werte.get("colspan", 1) or 1))
            for z in range(self._zeile, self._zeile + hoch):
                for s in range(spalte, spalte + breit):
                    self._belegt.add((z, s))
            self._offen = {"z": self._zeile, "s": spalte, "zs": hoch, "ss": breit,
                           "kopf": tag == "th", "text": ""}
            self._text = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._offen is not None:
            self._offen["text"] = normal("".join(self._text))
            self._zellen.append(self._offen)
            self._offen = None
            self._text = []
        elif tag == "table" and self._zellen:
            self.tabellen.append(_tabelle(self._zellen))
            self._zellen = []

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and self._offen is not None:
            self._text.append(" ")

    def handle_data(self, data):
        if self._offen is not None:
            self._text.append(data)


def _gfm_tabelle(zeilen: list[str]) -> dict:
    zellen: list[dict] = []
    zeilennummer = 0
    for nummer, zeile in enumerate(zeilen):
        if _MD_TRENNZEILE.match(zeile):
            continue
        teile = [normal(t) for t in zeile.strip().strip("|").split("|")]
        for spalte, text in enumerate(teile):
            zellen.append({"z": zeilennummer, "s": spalte, "zs": 1, "ss": 1,
                           "kopf": nummer == 0, "text": text})
        zeilennummer += 1
    return _tabelle(zellen)


def aus_markdown(markdown: str) -> dict:
    aus = leere_struktur()
    zeilen = markdown.split("\n")
    volltext: list[str] = []
    absatz: list[str] = []
    i = 0
    im_zusatz = False

    def absatz_schliessen():
        if absatz:
            text = normal(" ".join(absatz))
            absatz.clear()
            if text:
                aus["absaetze"].append(text)
                volltext.append(text)

    while i < len(zeilen):
        zeile = zeilen[i]

        # HTML-Tabelle des Dienstes
        if zeile.lstrip().startswith("<table"):
            absatz_schliessen()
            block = []
            while i < len(zeilen):
                block.append(zeilen[i])
                if "</table>" in zeilen[i]:
                    i += 1
                    break
                i += 1
            leser = _TabellenLeser()
            leser.feed("\n".join(block))
            leser.close()
            for tab in leser.tabellen:
                if not im_zusatz:
                    aus["tabellen"].append(tab)
                    volltext.extend(z["text"] for z in tab["zellen"] if z["text"])
            continue

        # Markdown-Tabelle
        if zeile.startswith("|") and i + 1 < len(zeilen) and _MD_TRENNZEILE.match(zeilen[i + 1]):
            absatz_schliessen()
            block = [zeilen[i]]
            i += 1
            while i < len(zeilen) and zeilen[i].startswith("|"):
                block.append(zeilen[i])
                i += 1
            tab = _gfm_tabelle(block)
            if not im_zusatz:
                aus["tabellen"].append(tab)
                volltext.extend(z["text"] for z in tab["zellen"] if z["text"])
            continue

        kopf = _MD_UEBERSCHRIFT.match(zeile)
        if kopf:
            absatz_schliessen()
            text = normal(kopf.group(2))
            im_zusatz = schluessel(text) in _ZUSATZ
            if not im_zusatz:
                aus["ueberschriften"].append({"stufe": len(kopf.group(1)), "text": text})
                volltext.append(text)
            i += 1
            continue

        if not zeile.strip() or _MD_MARKE.match(zeile.strip()) or _MD_BILD.match(zeile.strip()):
            absatz_schliessen()
            i += 1
            continue

        punkt = _MD_LISTE.match(zeile)
        if punkt:
            absatz_schliessen()
            if not im_zusatz:
                einzug = punkt.group(1).replace("\t", "   ")
                text = _MD_HAKEN.sub("", normal(punkt.group(2)))
                text = _MD_MARKE_IM_PUNKT.sub("", text)
                aus["listen"].append({"tiefe": min(3, len(einzug) // 2), "text": text})
                volltext.append(text)
            i += 1
            continue

        if not im_zusatz:
            absatz.append(zeile)
        i += 1

    absatz_schliessen()
    aus["volltext"] = normal(" ".join(volltext))
    return aus


# --------------------------------------------------------------------- Messen


def _f1(soll: list, ist: list) -> tuple[float, int, int, int]:
    """F1 über zwei Mengen mit Mehrfachvorkommen."""
    if not soll and not ist:
        return 1.0, 0, 0, 0
    rest = list(ist)
    treffer = 0
    for eintrag in soll:
        if eintrag in rest:
            rest.remove(eintrag)
            treffer += 1
    fehlend = len(soll) - treffer
    zuviel = len(ist) - treffer
    if treffer == 0:
        return 0.0, treffer, fehlend, zuviel
    genauigkeit = treffer / len(ist)
    vollstaendigkeit = treffer / len(soll)
    return (2 * genauigkeit * vollstaendigkeit / (genauigkeit + vollstaendigkeit),
            treffer, fehlend, zuviel)


def _stufen_normalisieren(kopfe: list[dict]) -> list[tuple[int, str]]:
    """Ebenen relativ zur obersten vorkommenden Ebene.

    Ob der Dienst mit ``#`` oder ``##`` beginnt, ist Geschmack. Ob 1.1 eine
    Ebene unter 1 steht, ist Struktur.
    """
    if not kopfe:
        return []
    kleinste = min(k["stufe"] for k in kopfe)
    return [(k["stufe"] - kleinste, schluessel(k["text"])) for k in kopfe]


def _tabellen_paaren(soll: list[dict], ist: list[dict]) -> list[tuple[dict, dict | None]]:
    """Ordnet Soll-Tabellen den erkannten zu — über den Textinhalt, nicht die
    Reihenfolge: eine übersehene Tabelle darf nicht alle folgenden verschieben."""
    frei = list(range(len(ist)))
    paare = []
    for tabelle in soll:
        soll_text = {schluessel(z["text"]) for z in tabelle["zellen"] if z["text"]}
        bester, beste_guete = None, 0.0
        for index in frei:
            ist_text = {schluessel(z["text"]) for z in ist[index]["zellen"] if z["text"]}
            if not soll_text or not ist_text:
                continue
            guete = len(soll_text & ist_text) / len(soll_text | ist_text)
            if guete > beste_guete:
                bester, beste_guete = index, guete
        if bester is not None and beste_guete >= 0.3:
            frei.remove(bester)
            paare.append((tabelle, ist[bester]))
        else:
            paare.append((tabelle, None))
    return paare


def _zell_struktur(tabelle: dict) -> list[tuple[int, int, int, int]]:
    return [(z["z"], z["s"], z["zs"], z["ss"]) for z in tabelle["zellen"]]


def _zell_inhalt(tabelle: dict) -> list[tuple[int, int, int, int, str]]:
    return [(z["z"], z["s"], z["zs"], z["ss"], schluessel(z["text"]))
            for z in tabelle["zellen"]]


def _reihenfolge(soll_absaetze: list[str], ist_volltext: str) -> float | None:
    """Kendalls Tau der Absatzreihenfolge — misst die Lesereihenfolge.

    Verglichen wird über die ersten Wörter jedes Absatzes; sie sind lang genug,
    um eindeutig zu sein, und kurz genug, um einen Erkennungsfehler weiter
    hinten zu überstehen.
    """
    stellen = []
    text = schluessel(ist_volltext)
    for absatz in soll_absaetze:
        anfang = schluessel(absatz)[:40]
        if len(anfang) < 12:
            continue
        stelle = text.find(anfang)
        if stelle >= 0:
            stellen.append(stelle)
    if len(stellen) < 3:
        return None
    gleich = ungleich = 0
    for i in range(len(stellen)):
        for j in range(i + 1, len(stellen)):
            if stellen[j] == stellen[i]:
                continue
            if stellen[j] > stellen[i]:
                gleich += 1
            else:
                ungleich += 1
    gesamt = gleich + ungleich
    return (gleich - ungleich) / gesamt if gesamt else None


def _textguete(soll: str, ist: str) -> float:
    """Anteil des Quelltextes, der sich im Ergebnis wiederfindet (0 bis 1).

    Kein echtes Levenshtein: der Vergleich läuft über die längsten gemeinsamen
    Blöcke. Das ist schnell genug für lange Dokumente und für den Zweck genau
    genug — gemessen wird, ob Text verloren geht oder dazukommt.
    """
    a, b = schluessel(soll), schluessel(ist)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    gleich = sum(block.size for block in
                 difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    return 2 * gleich / (len(a) + len(b))


def vergleiche(soll: dict, ist: dict) -> dict:
    """Vergleicht Wahrheit und Ergebnis. Alle Werte 0 bis 1, größer ist besser."""
    kopf_f1, kopf_treffer, kopf_fehlt, kopf_zuviel = _f1(
        _stufen_normalisieren(soll["ueberschriften"]),
        _stufen_normalisieren(ist["ueberschriften"]))

    listen_f1, *_ = _f1([(l["tiefe"], schluessel(l["text"])) for l in soll["listen"]],
                        [(l["tiefe"], schluessel(l["text"])) for l in ist["listen"]])

    struktur_werte, inhalt_werte = [], []
    tabellen_gefunden = 0
    for soll_tab, ist_tab in _tabellen_paaren(soll["tabellen"], ist["tabellen"]):
        if ist_tab is None:
            struktur_werte.append(0.0)
            inhalt_werte.append(0.0)
            continue
        tabellen_gefunden += 1
        struktur_werte.append(_f1(_zell_struktur(soll_tab), _zell_struktur(ist_tab))[0])
        inhalt_werte.append(_f1(_zell_inhalt(soll_tab), _zell_inhalt(ist_tab))[0])

    mittel = lambda werte: round(sum(werte) / len(werte), 4) if werte else None  # noqa: E731

    return {
        "text": round(_textguete(soll["volltext"], ist["volltext"]), 4),
        "ueberschriften": round(kopf_f1, 4),
        "ueberschriften_fehlend": kopf_fehlt,
        "ueberschriften_zuviel": kopf_zuviel,
        "listen": round(listen_f1, 4),
        "tabellen_struktur": mittel(struktur_werte),
        "tabellen_inhalt": mittel(inhalt_werte),
        "tabellen_soll": len(soll["tabellen"]),
        "tabellen_gefunden": tabellen_gefunden,
        "reihenfolge": _reihenfolge(soll["absaetze"], ist["volltext"]),
    }
