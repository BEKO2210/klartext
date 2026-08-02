"""Die gesamte Nachbearbeitung eines Docling-Ergebnisses an einer Stelle.

Der Worker holte diese Schritte früher einzeln zusammen. Als eigene Funktion
lassen sie sich außerhalb eines Auftrags anwenden — der Messstand in `bench/`
rechnet damit gespeicherte Docling-Rohergebnisse durch, ohne Datenbank,
Warteschlange und Wartezeit. Das ist nicht nur bequem: nur so ist sicher, dass
gemessen wird, was ausgeliefert wird.

Reihenfolge ist Absicht:

1. Bilder herauslösen — sonst stehen Rohdaten im Markdown.
2. Tabellen mit verbundenen Zellen als HTML erhalten, **vor** allen Textregeln,
   damit die folgenden Schritte auch deren Zellen erreichen.
3. Verweise aus der PDF anhängen.
4. Auflösung und Einheiten prüfen (nur melden, nie ändern).
5. Schreibweisen geradeziehen, dann Gliederung und Listen.
6. Wiederkehrende Seitenelemente zuletzt — sie hängen einen Abschnitt oben an.

Die JSON-Ausgabe wird dabei nur an einer Stelle angefasst: die eingebetteten
Bilddaten werden durch Dateinamen ersetzt. Inhalte werden nie entfernt.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import i18n, layout, postprocess
from .config import CONFIG


@dataclass
class Ergebnis:
    markdown: str
    bilder: list[dict] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    hinweis: str | None = None
    funde: list[dict] = field(default_factory=list)
    seitenelemente: list[str] = field(default_factory=list)
    # Zählwerte für Protokoll und Auftragsseite
    tabellen: int = 0
    verbundene_tabellen: int = 0
    geglaettet: int = 0
    gliederung: int = 0
    eingerueckt: int = 0
    umgestellt: int = 0
    verbundene_absaetze: int = 0


def anwenden(markdown: str, struktur: dict | None, quelle: bytes | None,
             mime: str, sprache: str = i18n.DEFAULT_LANG) -> Ergebnis:
    """Wendet die vollständige Nachbearbeitung an.

    `quelle` sind die Originalbytes; ohne sie entfallen die Schritte, die die
    PDF selbst lesen (Verweise, wiederkehrende Seitenelemente, Auflösung).
    """
    daten = struktur if isinstance(struktur, dict) else {}
    ist_pdf = mime == "application/pdf" and quelle is not None

    bilder = postprocess.bilder_ausloesen(daten)
    markdown = postprocess.markdown_bilder_verweisen(markdown, bilder)

    tabellen = len(daten.get("tables") or [])
    verbunden = 0
    if CONFIG.merged_tables == "html":
        markdown, verbunden = layout.verbundene_tabellen_erhalten(markdown, daten)

    # Zweispaltig gesetzte Seiten in Lesereihenfolge bringen und Absätze wieder
    # zusammenfügen, die ein Spalten- oder Seitenumbruch zerschnitten hat.
    # Vor dem Anhängen der Verweise, damit die angehängten Abschnitte nicht
    # mitsortiert werden.
    markdown, umgestellt = layout.lesereihenfolge_spalten(markdown, daten)
    markdown, verbundene_absaetze = layout.getrennte_absaetze_verbinden(markdown)

    links: list[dict] = []
    if ist_pdf and quelle is not None:
        links = postprocess.links_lesen(quelle)
        markdown = postprocess.markdown_links_anhaengen(markdown, links, sprache)

    hinweis = None
    if quelle is not None:
        hinweis = postprocess.aufloesung_pruefen(quelle, mime, daten or None, sprache)

    funde = postprocess.einheiten_pruefen(daten)
    if funde:
        anzahl = len(funde)
        satz = i18n.translate(sprache,
                              "note.units.one" if anzahl == 1 else "note.units.many",
                              count=anzahl)
        meldung = i18n.translate(sprache, "note.units.tail", lead=satz)
        hinweis = f"{hinweis} {meldung}" if hinweis else meldung

    markdown, geglaettet = postprocess.schreibweisen_glaetten(markdown)
    markdown, gliederung = layout.gliederung_wiederherstellen(markdown)
    if gliederung == 0:
        # Keine Gliederungsnummern im Dokument: dann sagt die Schriftgröße die
        # Ebene. Die Nummer hat Vorrang, sie ist die härtere Aussage.
        markdown, gliederung = layout.ueberschriften_nach_groesse(markdown, daten)
    markdown, eingerueckt = layout.listen_verschachteln(markdown)

    elemente: list[str] = []
    if ist_pdf and quelle is not None:
        elemente = postprocess.wiederkehrende_texte(quelle, markdown)
        markdown = postprocess.seitenelemente_zusammenfassen(markdown, elemente, sprache)

    return Ergebnis(markdown=markdown, bilder=bilder, links=links, hinweis=hinweis,
                    funde=funde, seitenelemente=elemente, tabellen=tabellen,
                    verbundene_tabellen=verbunden, geglaettet=geglaettet,
                    gliederung=gliederung, eingerueckt=eingerueckt,
                    umgestellt=umgestellt, verbundene_absaetze=verbundene_absaetze)
