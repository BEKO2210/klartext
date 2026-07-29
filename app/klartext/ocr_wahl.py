"""Auswahl der Erkennungs-Engine.

Heute liefert die Auswahl immer die eingestellte Standard-Engine. Der Ort ist
trotzdem schon getrennt, weil hier spaeter eine Auswahl nach Dokumentart hin
soll — und weil die Entscheidung dann an einer Stelle steht statt verteilt im
Worker.

Messstand vom 29.07.2026, drei Dokumente (zwei hochaufloeste Laborfotos,
eine grobe Rechnung mit 574x822 Bildpunkten):

    Engine      Einheiten richtig   Messwerte richtig
    RapidOCR         0 / 10              27 / 27
    EasyOCR          4 / 10              19 / 27
    Tesseract        0 / 10          verliert ganze Zeilen

EasyOCR liest die Einheiten der Laborfotos besser, verliert dafuer alle acht
Betraege der groben Rechnung. Deshalb bleibt RapidOCR die Voreinstellung: die
Zahlenwerte sind das, worauf es ankommt. Auffaellig ist, dass EasyOCR nur bei
der **grob** aufgeloesten Vorlage abfaellt — eine Auswahl nach Bildgroesse
waere also der naheliegende naechste Schritt. Drei Dokumente sind dafuer aber
zu duenn, zumal beide Laborfotos aus derselben Kamera und derselben Vorlage
stammen, also eigentlich nur ein Fall sind.

Damit ein spaeterer Vergleich auf echten Daten fussen kann, wird die tatsaechlich
verwendete Engine je Auftrag in ``jobs.ocr_engine`` festgehalten.
"""

from __future__ import annotations

from .config import CONFIG


def engine_fuer(mime: str, groesse_bytes: int, bildmasse: tuple[int, int] | None = None) -> str:
    """Liefert die Engine fuer genau diesen Auftrag.

    Die Parameter werden heute nicht ausgewertet. Sie stehen bereits in der
    Signatur, damit eine spaetere Auswahl nach Dokumentart oder Bildgroesse
    nichts an den Aufrufern aendern muss.
    """
    return CONFIG.ocr_engine
