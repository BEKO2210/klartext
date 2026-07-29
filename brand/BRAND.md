# Klartext — Marke

Eigenstaendige Marke. Kein Bezug zu IBM oder Docling, keine fremden Logos, keine
fremden Wortmarken. Docling ist ausschliesslich die technische Engine im Hintergrund
und wird nirgends als Absender oder Herkunft dargestellt.

## Name

**Klartext** — deutsch fuer „unverschluesselter, klar lesbarer Text". Beschreibt exakt,
was das Produkt tut: aus einem Dokument wird lesbarer, strukturierter Text.

## Bildmarke

Ein Blatt mit abgeschnittener Ecke. Innen oben zwei kurze, ungleich lange Zeilen
(das unstrukturierte Ausgangsdokument), unten zwei exakt gleich lange, buendige Zeilen
(das aufgeraeumte Ergebnis). Die Aussage steckt in Laenge und Ausrichtung, nicht in
Farbe — die Marke funktioniert deshalb einfarbig, invertiert und im Druck.

- Konstruktion: 32er-Raster, Strichstaerke 2, runde Enden und Ecken
- `stroke="currentColor"` — die Marke uebernimmt immer die Textfarbe des Kontexts
- Zwei optische Groessen:
  - `app/klartext/static/logo.svg` — ab 24 px, mit dem vollen Zeilen-Kontrast
  - `app/klartext/static/favicon.svg` — 16–32 px, reduziert, dickere Striche, Vollflaeche

### Entstehung

Vier Erstentwuerfe und drei Verfeinerungen wurden mit Higgsfield (`nano_banana_pro`)
generiert und liegen unter `brand/explorations/`. Sie dienten der Richtungsfindung und
haben zwei Dinge belegt: das Blatt-plus-Zeilenrhythmus-Motiv wird sofort verstanden, und
dicke Striche mit runden Enden ueberstehen kleine Groessen. Keiner der Entwuerfe wurde
uebernommen — die Erstrunde war bei 24 px unleserlicher Matsch, die Verfeinerungsrunde
sauber, aber ein austauschbares Standard-Datei-Icon ohne eigene Aussage. Die ausgelieferte
Marke ist deshalb von Hand als SVG gezeichnet: rasterfrei, wenige hundert Byte, in hellem
und dunklem Modus korrekt, bis 16 px lesbar.

## Farben

| Rolle | Hell | Dunkel | Verwendung |
|---|---|---|---|
| Primaer | `#1E3A5F` | `#7FA6D4` | Marke, Ueberschriften, primaere Flaechen |
| Akzent | `#15803D` | `#22C55E` | genau eine primaere Aktion je Seite, Erfolgszustand |
| Hintergrund | `#FFFFFF` | `#0F172A` | Seitenhintergrund |
| Flaeche | `#F6F8FB` | `#152238` | Karten, Panels |
| Text | `#0F172A` | `#E7EDF5` | Fliesstext |
| Text gedaempft | `#51607A` | `#94A3B8` | Sekundaertext, Hinweise |
| Rahmen | `#DCE3ED` | `#25344C` | Linien, Trenner |
| Fehler | `#B42318` | `#F87171` | Fehlerzustaende |

Alle Text-auf-Flaeche-Paare erreichen mindestens 4,5:1; Sekundaertext mindestens 4,5:1
auf der jeweiligen Flaeche. Zustaende werden nie allein ueber Farbe transportiert —
jeder Status hat zusaetzlich Text und Form.

## Schrift

System-Schriftstapel (`system-ui` / San Francisco / Segoe UI / Roboto). Bewusst **keine**
Webfonts: kein CDN, kein externer Request, kein Tracking, kein FOIT, keine zusaetzliche
Ladezeit. Fuer Markdown-Ausgaben der System-Monospace-Stapel.

- Fliesstext 16 px, Zeilenhoehe 1.6
- Skala: 12 / 14 / 16 / 18 / 22 / 28 / 38
- Gewichte: 400 Fliesstext, 500 Labels, 600–650 Ueberschriften

## Haltung

Ruhig, sachlich, ohne Marketinglaerm. Keine Verlaufsflaechen, keine Glasoptik, keine
dekorativen Animationen, keine Emoji als Symbole. Bewegung nur dort, wo sie einen
Zustandswechsel erklaert (150–250 ms), und immer unter `prefers-reduced-motion` abschaltbar.
