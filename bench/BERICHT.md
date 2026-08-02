# Messbericht

Erhoben am 02.08.2026 23:19 · Stand `0758d71` · Dienst https://klartext.it-handwerk-stuttgart.de

Alle Werte von 0 bis 1, größer ist besser. `—` heißt: im Dokument kommt diese Eigenschaft nicht vor.

## digital

| Dokument | Text | Überschr. | Listen | Tab-Struktur | Tab-Inhalt | Reihenfolge |
|---|---|---|---|---|---|---|
| 01-gliederung | 0.971 | 1.000 | 1.000 | — | — | 1.000 |
| 02-rechnung | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 03-formular | 1.000 | 1.000 | 1.000 | 1.000 | 0.917 | — |
| 04-laborbefund | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 05-vertrag | 0.999 | 1.000 | 1.000 | — | — | 1.000 |
| 06-zweispaltig | 1.000 | 1.000 | 1.000 | — | — | 1.000 |
| 07-tabelle-umbruch | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — |
| 08-seitenelemente | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 09-preisliste | 0.991 | 1.000 | 1.000 | 0.952 | 0.941 | — |
| 10-protokoll | 0.940 | 1.000 | 1.000 | 1.000 | 1.000 | — |
| 11-zeichensatz | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 12-mehrstufiger-kopf | 0.989 | 1.000 | 1.000 | 0.933 | 0.817 | — |
| **Mittel** | 0.991 | 1.000 | 1.000 | 0.987 | 0.964 | 1.000 |

## scan

| Dokument | Text | Überschr. | Listen | Tab-Struktur | Tab-Inhalt | Reihenfolge |
|---|---|---|---|---|---|---|
| 01-gliederung | 0.952 | 1.000 | 1.000 | — | — | 1.000 |
| 02-rechnung | 1.000 | 0.250 | 1.000 | 1.000 | 1.000 | 1.000 |
| 03-formular | 0.947 | 0.167 | 0.333 | 1.000 | 0.917 | — |
| 04-laborbefund | 0.979 | 0.250 | 1.000 | 1.000 | 0.889 | 1.000 |
| 05-vertrag | 0.936 | 0.143 | 1.000 | — | — | 1.000 |
| 06-zweispaltig | 1.000 | 0.500 | 1.000 | — | — | 1.000 |
| 07-tabelle-umbruch | 0.999 | 1.000 | 1.000 | 1.000 | 0.984 | — |
| 08-seitenelemente | 0.897 | 0.105 | 0.000 | 1.000 | 1.000 | 1.000 |
| 09-preisliste | 0.994 | 1.000 | 1.000 | 1.000 | 0.952 | — |
| 10-protokoll | 0.940 | 0.167 | 1.000 | 1.000 | 1.000 | — |
| 11-zeichensatz | 0.937 | 0.167 | 1.000 | 1.000 | 1.000 | 1.000 |
| 12-mehrstufiger-kopf | 0.976 | 1.000 | 1.000 | 0.915 | 0.678 | — |
| **Mittel** | 0.963 | 0.479 | 0.861 | 0.991 | 0.935 | 1.000 |

## Wie das gemessen wird

Die Prüfdokumente in `bench/quellen/` sind selbst geschrieben; die Wahrheit wird aus ihnen berechnet (`bench/bauen.py`), nicht von Hand gepflegt. Gemessen wird das Markdown, das der laufende Dienst ausliefert — also die Datei, die Nutzer herunterladen.

Abschnitte, die der Dienst selbst anfügt (Verweisliste, wiederkehrende Seitenelemente), bleiben außen vor: sie stehen nicht in der Vorlage und sollen die Messung weder heben noch senken.
