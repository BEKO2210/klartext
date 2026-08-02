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

## Ergebnis (offline gemessen, Zweig `layouttreue/ueberschriften-und-spalten`)

| Variante | Text | Überschr. | Listen | Tab-Struktur | Tab-Inhalt | Reihenfolge |
|---|---|---|---|---|---|---|
| digital vorher | 0,981 | 0,395 | 1,000 | 0,987 | 0,964 | 0,976 |
| **digital nachher** | **0,991** | **1,000** | 1,000 | 0,987 | 0,964 | **1,000** |
| scan vorher | 0,943 | 0,382 | 0,781 | 0,993 | 0,897 | 0,900 |
| **scan nachher** | **0,953** | **0,423** | 0,781 | 0,993 | 0,897 | **1,000** |

* **A erledigt** für die digitale Fassung (0,395 → 1,000). Für Scans **nicht
  erreichbar** — siehe unten, die Messlatte war dort falsch angesetzt.
* **B erledigt**: zweispaltiges Dokument von Reihenfolge 0,833 auf 1,000
  (digital) und 0,600 auf 1,000 (Scan), Text dort 0,877 → 1,000.
* **C und D** liegen nicht in der Nachbearbeitung — Begründung unten.
* Keine Kennzahl ist gefallen.

## Arbeitspakete

### A — Überschriftenebenen ohne Nummer  ▸ erledigt (digital)

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

**Ergebnis.** Digital 1,000 — erreicht. **Scan 0,423 — nicht erreicht, und die
Messlatte war dort falsch angesetzt.** Die Zeilenhöhe misst bei einem Scan die
Ausdehnung der erkannten Buchstaben, nicht die Schriftgröße: im Beleg ist die
Überschrift „Zahlungsbedingungen" (h2, mit Unterlängen) *höher* als der Titel
darüber. Aus diesem Signal ist auf Scans keine Ebene abzuleiten, und die Regel
verweigert dort korrekt die Arbeit. Nummerierte Gliederungen greifen weiterhin
auch auf Scans (Prüfdokument 01: 0,833). Ein besseres Signal müsste aus der
Erkennung selbst kommen (Schriftgrad statt Bounding-Box) — eigenes Paket,
eigene Messung.

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

**Ergebnis.** Erreicht: Reihenfolge 1,000 in beiden Varianten, Text beim
zweispaltigen Dokument 0,877 → 1,000 (digital) und 0,854 → 0,979 (Scan).
Umgesetzt als Spaltenzone: der Bereich, in dem **beide** Spalten Text tragen,
wird spaltenweise sortiert; was darunter steht (etwa eine Zwischenüberschrift),
bleibt dahinter. Zusätzlich werden Absätze wieder zusammengefügt, die ein
Spalten- oder Seitenumbruch zerschnitten hat — Erkennungsmerkmal: der erste
Teil endet ohne Satzzeichen, der zweite beginnt klein.

Abgesichert: Seiten mit Tabellen, Listen oder Bildern werden nicht umgestellt,
ebenso wenig Seiten ohne echten Spaltensatz. Sobald sich ein Block nicht
eindeutig zuordnen lässt, bleibt der Abschnitt unberührt.

### C — Mehrstufige Tabellenköpfe  ▸ liegt nicht bei uns

Tab-Inhalt 0,817 digital und 0,733 im Scan beim dreizeiligen Kopf. Untersucht:
Das Tabellenmodell (TableFormer) setzt die Kopfzellen um eine Spalte versetzt —
die Zelle „Anlage" landet in Zeile 1 statt 0, die beiden „Halbjahr"-Verbünde
rutschen eine Spalte nach links, die letzte Spalte der Kopfzeile bleibt leer.
Der **Inhalt ist vollständig**, nur die Rasterzuordnung stimmt nicht.

Das im Nachhinein zu reparieren hieße, die Zuordnung des Modells zu erraten.
Genau das ist ausgeschlossen. Wenn hier etwas passiert, dann über die Engine
(anderes `table_mode`, neuere Docling-Fassung) — und das ist ein eigenes Paket
mit eigener Messung, weil es alle Werte verschiebt.

### D — Listen im Scanweg  ▸ Grenze der Texterkennung

Untersucht, was der Scanweg tatsächlich liefert:

* Das leere Kästchen `☐` wird gar nicht gelesen, das angekreuzte `☒` als `⊠`.
  Welche Kästchen angekreuzt sind, geht damit verloren. Ein Kreuz zu **raten**
  ist ausgeschlossen — ein falsch angekreuztes Formularfeld ist schlimmer als
  eine sichtbare Lücke.
* Wörter verschmelzen („mitgenommenwerden", „Treppenhausliegt"). Das trifft
  Listen wie Fließtext und ist eine Eigenschaft der Texterkennung.
* Eine Überschrift wurde als Listenpunkt gelesen und mit der Fußzeile
  verklebt — ein Einzelfall des Layoutmodells.

Im Messstand wurde nur die Bewertung fair gemacht (`⊠` gilt als `☒`, gleiches
Zeichen, anderer Codepunkt). Am Dienst wurde nichts geändert. Der ehrliche
Umgang damit gehört in den FAQ-Text, nicht in eine Regel.

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
