# Messstand

Klartext behauptet, verlustarm umzuwandeln. Bisher war das eine Sammlung von
Einzelbeobachtungen („bei einer Testrechnung 18 statt 10 Beträge richtig"). Der
Messstand macht daraus Zahlen, die sich zwischen zwei Ständen vergleichen
lassen — ohne Zahl ist jede Verbesserung nur ein Eindruck.

## Der Kniff: die Wahrheit wird nicht gepflegt, sondern berechnet

Die Prüfdokumente in `quellen/` sind selbst geschriebene HTML-Dateien. Aus jeder
entsteht

* die digitale PDF, wie sie aus einem Textprogramm käme,
* dieselben Seiten als **Bild-PDF ohne Textebene** — der Weg über die
  Texterkennung, wie bei einem Kopierer,
* und die **Wahrheit** (`gold/*.json`): Überschriften mit Ebene, Absätze,
  Listenpunkte mit Tiefe, Tabellenzellen mit Zeilen- und Spaltenverbünden.

Die Wahrheit wird aus der Quelle abgeleitet, nicht von Hand eingetragen. Ein
neues Prüfdokument kostet damit nur die Zeit, es zu schreiben, und die Messung
kann nicht heimlich veralten.

## Gemessen wird der Dienst, nicht die Bibliothek

Die Dateien laufen über die normale Weboberfläche durch den laufenden Dienst und
werden als Markdown wieder abgeholt. Bewertet wird also genau die Datei, die
Nutzer herunterladen — Docling **plus** Nachbearbeitung **plus** Layouttreue.

Abschnitte, die der Dienst selbst anfügt (Verweisliste, wiederkehrende
Seitenelemente), bleiben außen vor: sie stehen nicht in der Vorlage und sollen
die Messung weder heben noch senken.

## Kennzahlen

| Kennzahl | Was sie misst |
|---|---|
| `text` | Anteil des Quelltextes, der im Ergebnis wiederkehrt |
| `ueberschriften` | F1 über Ebene und Text; Ebenen relativ, `#` gegen `##` ist kein Fehler |
| `listen` | F1 über Listenpunkte samt Verschachtelungstiefe |
| `tabellen_struktur` | F1 über das Zellraster **mit** Verbünden |
| `tabellen_inhalt` | dasselbe, zusätzlich mit übereinstimmendem Zelltext |
| `reihenfolge` | Kendalls Tau der Absatzreihenfolge — die Lesereihenfolge |

Alle Werte von 0 bis 1, größer ist besser. `—` heißt: kommt im Dokument nicht vor.

Aufzählungsmarken (`a.`, `[x]`) werden vor dem Vergleich entfernt — sie sind
Marke, keine Aussage. Der Haken selbst (`☒` gegen `☐`) bleibt stehen, denn
angekreuzt oder nicht ist der Inhalt eines Formulars.

## Benutzung

```bash
python3 bench/bauen.py                    # Dokumente + Wahrheit erzeugen
python3 bench/messen.py                   # digitale Fassungen messen
python3 bench/messen.py --variante scan   # über die Texterkennung
python3 bench/messen.py --variante beide
```

`bauen.py` braucht chromium, `pdftoppm` (poppler-utils) und Pillow.
`messen.py` meldet sich am jüngsten Demo-Konto an, wie der Korpuslauf auch.

Jeder Lauf schreibt `BERICHT.md` neu und hängt eine Zeile an `verlauf.jsonl`.
Der Verlauf ist der eigentliche Wert: er zeigt, ob eine Änderung am Dienst die
Qualität gehoben oder etwas anderes kaputtgemacht hat.

## Grenzen, die man kennen muss

* Die Prüfdokumente sind **selbst geschrieben**. Sie decken Aufbau, Tabellen und
  Zeichensatz ab, aber keinen echten Kopierer mit Staub, Knick und Schieflage.
  Die Scanfassung ist ein sauberer 200-dpi-Scan, kein Handyfoto bei Kunstlicht.
* `text` ist kein echtes Levenshtein, sondern der Anteil gemeinsamer Blöcke.
  Für die Frage „geht Text verloren?" reicht das; für eine exakte
  Zeichenfehlerrate nicht.
* Zwölf Dokumente sind eine Stichprobe, keine Statistik. Ein Sprung um 0,01 im
  Mittel ist Rauschen; ein Einbruch bei einem einzelnen Dokument ist ein Hinweis.
