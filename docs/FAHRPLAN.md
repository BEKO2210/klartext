# Fahrplan Layouttreue — intern

Arbeitspapier, kein Nutzertext. Es hält fest, **was als Nächstes gebaut wird,
woran gemessen wird und wann etwas live gehen darf**. Der Messstand (`bench/`)
ist die Entscheidungsgrundlage; ohne Zahl gilt nichts als erledigt.

Stand beim Anlegen: 02.08.2026, Commit `b269fa1`, live ist 1.2.0.

## Ausgangslage (erste Messung, Stand `24b2158`)

| Variante | Text | Überschr. | Listen | Tab-Struktur | Tab-Inhalt | Reihenfolge |
|---|---|---|---|---|---|---|
| digital | 0,981 | **0,395** | 1,000 | 0,987 | 0,964 | 0,976 |
| scan | 0,943 | **0,382** | 0,781 | 0,993 | 0,897 | 0,900 |

Tabellen sitzen. Die Lücken liegen bei den Überschriften, bei mehrspaltigem
Text und im Scanweg bei den Listen.

## Arbeitspakete

### A — Überschriftenebenen ohne Nummer  ▸ größter Hebel

**Problem.** Die Layouttreue von 1.2.0 leitet die Ebene aus der Nummer der
Vorlage ab. Ein Dokument ohne Gliederungsnummern — Titel, darunter Abschnitte —
bleibt vollständig flach: alles `##`. Betrifft 9 von 12 Prüfdokumenten, also
den Normalfall.

**Ansatz.** Die Zeilenhöhe steht in der JSON-Struktur (`texts[].prov[].bbox`)
und trennt sauber: im Rechnungsbeispiel Titel 7,19 · Abschnitt 6,07 ·
Fließtext 4,94. Die Überschriften eines Dokuments werden nach Höhe gruppiert,
die Gruppen ergeben die Ebenen. Zusätzlich prüfen, was `texts[].formatting`
hergibt (fett/kursiv) — falls belastbar, als zweites Merkmal.

**Selbstprüfung, sonst bleibt alles wie es ist.**
* Nur wenn mindestens drei Überschriften vorliegen.
* Nur wenn die Höhengruppen sich deutlich trennen (Abstand größer als die
  Streuung innerhalb einer Gruppe) — sonst ist es eine Ebene, keine Hierarchie.
* Nummerierte Gliederungen behalten Vorrang: die Nummer ist die härtere Aussage
  als eine gemessene Schriftgröße.
* Höchstens drei abgeleitete Ebenen. Wer feiner unterteilt, rät.

**Messlatte.** Überschriften digital ≥ 0,90 · scan ≥ 0,85, ohne Verlust bei
den übrigen Kennzahlen (Toleranz 0,005).

### B — Lesereihenfolge bei mehrspaltigem Satz

**Problem.** Zweispaltiger Fachtext: Reihenfolge 0,833 digital und 0,600 im
Scan, Text 0,877/0,854. Absätze aus der rechten Spalte landen zwischen denen
der linken. Steht seit jeher als Grenze im README — jetzt ist sie beziffert.

**Ansatz.** Aus den Bounding-Boxen der Textblöcke je Seite die Spalten
erkennen (Häufung der linken Kanten, Lücke dazwischen) und die Blöcke
spaltenweise sortieren. Nur eingreifen, wenn die Spalten sich klar trennen und
die Blöcke sich nicht über die Spaltengrenze ziehen.

**Messlatte.** Reihenfolge zweispaltig digital ≥ 0,95 · scan ≥ 0,85, Text
zweispaltig ≥ 0,95 digital.

**Risiko.** Höher als A: Wer die Reihenfolge falsch umbaut, macht ein bisher
brauchbares Dokument unbrauchbar. Deshalb nach A und nur mit deutlicher
Trennung.

### C — Mehrstufige Tabellenköpfe

Tab-Inhalt 0,817 digital und 0,733 im Scan beim dreizeiligen Kopf. Struktur
stimmt weitgehend (0,933), der Text einzelner Kopfzellen nicht. Erst nach A
und B ansehen — kleiner Hebel, aber sauber messbar.

### D — Listen im Scanweg

Listen fallen von 1,000 (digital) auf 0,781 (Scan). Zwei Ausreißer: das
Formular mit Kreuzchen und der Prüfbericht. Ursache noch nicht untersucht.
Zuerst nachsehen, was der Scanweg tatsächlich liefert, dann entscheiden — es
kann gut sein, dass hier die Wahrheit im Korpus zu streng ist und nicht der
Dienst falsch liegt.

## Vorgehen

1. **Entwicklungsschleife ohne Live-Dienst.** Die Nachbearbeitung wird als
   eigene Funktion aus dem Worker herausgezogen, damit Worker und Messstand
   denselben Code verwenden. Der Messstand speichert die Docling-Rohergebnisse
   je Prüfdokument einmal zwischen und rechnet die Nachbearbeitung danach
   offline — Sekunden statt Minuten, kein Auftrag, keine Fair-Use-Grenze,
   keine Belastung des laufenden Dienstes.
2. **Eigener Zweig.** Kein Bauen und kein Neustart der Live-Container, solange
   ein Paket nicht fertig gemessen ist.
3. **Messen nach jeder Änderung**, offline. Erst wenn die Messlatte steht:
   ein vollständiger Lauf über den Dienst auf einer Probeinstanz oder — falls
   nicht anders möglich — ein Lauf gegen live **nach** Freigabe.

## Freigabe: erst dann geht etwas live

Alle Punkte müssen erfüllt sein, keiner ist verhandelbar:

* [ ] Messlatte des Pakets erreicht, offline gemessen
* [ ] Keine Kennzahl schlechter als in `bench/verlauf.jsonl` (Toleranz 0,005)
* [ ] `python3 tests/layout_test.py` bestanden, neue Regeln durch neue
      Prüfungen abgedeckt
* [ ] `python3 tests/e2e.py` vollständig bestanden (73/73)
* [ ] Korpuslauf über `tests/fixtures` ohne neue Befunde
* [ ] Auftragsseite und betroffene Seiten bei 412 px gemessen
* [ ] CHANGELOG-Eintrag geschrieben, Version gesetzt, ARCHITECTURE ergänzt
* [ ] Belkis hat zugestimmt

Erst danach: `docker compose build`, `up -d`, vollständiger Messlauf gegen
live, Ergebnis in `bench/verlauf.jsonl`.

## Nicht-Ziele

* **Kein Sprachmodell** zum Aufräumen der Ausgabe. Bricht das Kernversprechen.
* **Keine externen Dienste**, auch nicht für Layouterkennung.
* **Keine Änderung der Docling-Parameter** nebenbei — jede würde alle
  Messwerte verschieben und wäre ein eigenes Paket mit eigener Messung.
* **Keine neuen Ausgabeformate.** Markdown und JSON reichen, solange sie nicht
  die Messlatte reißen.
