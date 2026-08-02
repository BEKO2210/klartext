# Changelog

Was wann veröffentlicht wurde. Die Versionsnummer ist zugleich der Tag des
Docker-Images (`klartext-app:<Version>`), das auf dem Server läuft.

**Aktuell live: 1.2.0** (seit 02.08.2026)

---

## 1.3.0 — vorbereitet, noch nicht live

Zwei Lücken, die der neue Messstand beziffert hat: Überschriften ohne
Gliederungsnummer landeten alle auf derselben Ebene, und bei zweispaltigem Satz
stand die rechte Spalte hinter allem anderen.

### Neu

* **Gliederungstiefe auch ohne Nummern.** Titel, darunter Abschnitte — bisher
  alles `##`. Die Ebene kommt jetzt aus der Schriftgröße, die als Zeilenhöhe in
  der Struktur steht. Nur bei klarer Trennung: jede Ebene in sich eng, zwischen
  den Ebenen ein deutlicher Sprung. Auf Scans misst dieses Maß Ober- und
  Unterlängen statt der Schriftgröße — dort bleibt die Gliederung unangetastet,
  statt geraten zu werden.
* **Lesereihenfolge bei Spaltensatz.** Die Spalten werden über die Seitenmitte
  bestimmt, an durchgehenden Blöcken getrennt und in der Zone, in der beide
  Spalten Text tragen, spaltenweise sortiert. Eine Zwischenüberschrift unter
  den Spalten bleibt dahinter. Seiten mit Tabellen, Listen oder Bildern werden
  nicht umgestellt.
* **Zerschnittene Absätze** werden wieder zusammengefügt, wenn der erste Teil
  ohne Satzzeichen endet und der zweite klein beginnt — auch über den
  Seitenumbruch hinweg.

### Gemessen (bench/, zwölf Prüfdokumente)

| Variante | Text | Überschr. | Listen | Tab-Struktur | Tab-Inhalt | Reihenfolge |
|---|---|---|---|---|---|---|
| digital vorher | 0,981 | 0,395 | 1,000 | 0,987 | 0,964 | 0,976 |
| **digital jetzt** | **0,991** | **1,000** | 1,000 | 0,987 | 0,964 | **1,000** |
| scan vorher | 0,943 | 0,382 | 0,781 | 0,993 | 0,897 | 0,900 |
| **scan jetzt** | **0,953** | **0,423** | 0,781 | 0,993 | 0,897 | **1,000** |

Keine Kennzahl ist gefallen.

### Technisch

* Die Nachbearbeitung liegt jetzt vollständig in `nachbearbeitung.py`. Worker
  und Messstand rufen dieselbe Funktion auf — vorher hätte der Messstand nur
  eine Nachbildung messen können.
* `bench/offline.py` rechnet gesicherte Docling-Rohergebnisse in Sekunden
  durch, in einem Wegwerfcontainer aus dem gebauten Abbild und ohne jedes
  Datenverzeichnis. Damit ist eine Änderung an einer Regel sofort messbar,
  ohne Aufträge und ohne den laufenden Dienst anzufassen.
* `tests/layout_test.py` deckt die neuen Regeln mit zwölf weiteren Prüfungen ab
  (33 insgesamt), darunter die Fälle, in denen bewusst **nichts** passieren darf.

### Nicht angefasst

* **Mehrstufige Tabellenköpfe** (Tab-Inhalt 0,817): Das Tabellenmodell setzt die
  Kopfzellen um eine Spalte versetzt. Der Inhalt ist vollständig, nur die
  Rasterzuordnung stimmt nicht — das im Nachhinein zu reparieren hieße raten.
* **Kreuzchen auf Scans:** Die Texterkennung liest `☐` gar nicht und `☒` als
  `⊠`. Welche Kästchen angekreuzt sind, geht verloren. Ein Kreuz zu raten ist
  ausgeschlossen: ein falsch angekreuztes Formularfeld ist schlimmer als eine
  sichtbare Lücke.

---

## 1.2.0 — 02.08.2026

Layouttreue. Zwei Rückmeldungen auf Product Hunt: die Ausgabe flacht das Original
ein, und Markdown kann eine verbundene Zelle gar nicht ausdrücken — was passiert
also damit?

### Neu

* **Tabellen mit verbundenen Zellen bleiben verbunden.** Bisher füllte Docling
  jede überdeckte Rasterstelle mit demselben Text: aus „Zwischensumme" über vier
  Spalten wurden vier gleiche Zellen. Solche Tabellen stehen jetzt als
  HTML-Tabelle mit `rowspan`/`colspan` in der Markdown-Datei. Tabellen ohne
  Verbünde bleiben unverändert im Markdown-Raster, die JSON-Ausgabe trug die
  Struktur ohnehin schon. Abschaltbar mit `MERGED_TABLES=raster`.
* **Gliederungstiefe aus der Nummer.** Das Layoutmodell kennt Überschriften,
  aber keine Ebenen — `1`, `1.1` und `1.1.1` kamen alle als `##` heraus. Die
  Ebene wird jetzt aus der Nummer der Vorlage hergeleitet; die Nummer selbst
  bleibt Zeichen für Zeichen stehen.
* **Verschachtelte Listen** werden eingerückt, wenn ein lückenloser
  Buchstabenblock zwischen zwei nummerierten Punkten steht.
* Zwei neue Fragen im FAQ (verbundene Zellen, Überschriften-Nummern) und ein
  Hinweis auf der Auftragsseite, wenn Tabellen als HTML erhalten wurden.

### Technisch

* Neues Modul `app/klartext/layout.py`, im Worker vor bzw. nach den Textregeln.
  Jede Regel prüft sich selbst und lässt das Dokument unverändert, sobald die
  Belege nicht reichen (Elternprüfung bei Nummern, Kopfzeilen-Abgleich bei
  Tabellen). Zellentext wird beim HTML-Bau maskiert.
* Migration `006_layouttreue.sql`: `jobs.table_count`, `jobs.merged_table_count`.
* `tests/layout_test.py` — 21 Prüfungen gegen nachgebaute Docling-Strukturen,
  ohne Netz und Datenbank; läuft auch in `tests/e2e.py` als Prüfung 43c.

---

## 1.1.2 — 31.07.2026

Commit [`07dce48`](https://github.com/BEKO2210/klartext/commit/07dce48) · Tag `v1.1.2`

### Behoben

* **Auftrag und Quelldatei entstehen in einer Anweisung.** Beide Einfügungen
  liefen bisher getrennt, jede mit eigenem Commit. Dazwischen stand der Auftrag
  auf `queued` und war für den Worker sichtbar, während der Verweis auf die
  Quelldatei noch fehlte. Am 31.07. ist ein Worker vier Millisekunden nach dem
  Anlegen in diese Lücke gefahren und hat den Auftrag als `conversion_failed`
  abgelegt, ohne dass Docling je gefragt wurde. Ein Auftrag betroffen.
* **Zweites Netz im Worker:** Ein Auftrag ohne Quelldatei, jünger als 30
  Sekunden und mit weniger als drei Versuchen, geht zurück in die
  Warteschlange statt in den Fehler.

---

## 1.1.1 — 31.07.2026

Commit [`b73b93a`](https://github.com/BEKO2210/klartext/commit/b73b93a) · Tag `v1.1.1`

### Geändert

* **Kopfzeile neu.** Am Handy eine Zeile statt zwei (61 px statt ~120 px).
  Sprache als DE/EN-Segment mit sichtbar gesetzter aktueller Sprache, am Handy
  kurze Knopfbeschriftung, unter 380 px weicht die Wortmarke dem Zugang — das
  Symbol bleibt und der Name bleibt für Screenreader lesbar. Sticky mit Blur,
  mit Rückfall auf deckend, wo der Browser das nicht kann.
* Navigation im angemeldeten Bereich als flache Reiterzeile mit Marker auf der
  aktuellen Seite.

---

## 1.1.0 — 31.07.2026

Enthalten in Commit [`b73b93a`](https://github.com/BEKO2210/klartext/commit/b73b93a)
und [`4fcdd30`](https://github.com/BEKO2210/klartext/commit/4fcdd30)

### Neu

* **Englisch ist die Standardsprache.** Englisch liegt auf den blanken Pfaden,
  Deutsch unter `/de` (`/login` und `/de/anmelden`). Der Zulauf kommt
  überwiegend aus dem englischsprachigen Raum, deutsche Bestandsnutzer
  verlieren nichts.
* Sprachwahl je Anfrage: Pfad schlägt Sprachcookie, Cookie schlägt
  `Accept-Language`. Wer laut Browser Deutsch bevorzugt und noch nichts
  gewählt hat, wird einmalig auf `/de/…` geschickt; der Umschalter beendet die
  Automatik.
* Alle Texte übersetzt: Oberfläche, Fehlermeldungen, Mailtexte, Browser-Texte,
  Rechtstexte (englisch mit Hinweis, dass die deutsche Fassung maßgeblich ist).
* `jobs.lang` (Migration `005_sprache.sql`): Hinweise und Zusatzabschnitte im
  erzeugten Markdown stehen in der Sprache, in der der Auftrag eingestellt
  wurde.
* Suchmaschinen: `hreflang` samt `x-default`, beide Fassungen in der Sitemap,
  `Vary: Accept-Language, Cookie` auf allen HTML-Antworten.
* Datums- und Zahlenformat je Sprache; die deutsche Fassung zeigt weiter
  deutsche Ortszeit, die englische UTC mit Zonenkürzel.

### Behoben

* **Aufräumen bricht bei fremder Datenbank ab.** Der Aufräumlauf des Workers
  löscht Dateien ohne Eintrag in seiner Datenbank. Zeigt ein Worker
  versehentlich auf eine andere Datenbank — etwa eine Probeinstanz mit den
  echten Datenverzeichnissen — gilt der gesamte Bestand als verwaist. Genau das
  ist am 31.07. passiert: 37 Dateien aus vier fertigen Aufträgen waren weg.
  Der Fund wird jetzt auf Plausibilität geprüft; im Zweifel wird nichts
  gelöscht und der Grund landet als Fehler im Log.

### Umgezogen

Alte deutsche Adressen antworten dauerhaft mit 301, Formularpfade mit 308:

| alt | neu |
| --- | --- |
| `/anmelden` | `/de/anmelden` |
| `/registrieren` | `/de/registrieren` |
| `/passwort-vergessen` | `/de/passwort-vergessen` |
| `/passwort-neu` | `/de/passwort-neu` |
| `/bestaetigung` | `/de/bestaetigung` |
| `/impressum` | `/de/impressum` |
| `/datenschutz` | `/de/datenschutz` |
| `/nutzungsbedingungen` | `/de/nutzungsbedingungen` |
| `/lizenzen` | `/de/lizenzen` |
| `/konto` | `/account` |
| `/konto/passwort` | `/account/password` |
| `/konto/loeschen` | `/account/delete` |
| `/abmelden` | `/logout` |
| `/app/auftrag/<id>` | `/app/job/<id>` |
| `/app/auftrag/<id>/bild/<nr>` | `/app/job/<id>/image/<nr>` |
| `/app/auftrag/<id>/loeschen` | `/app/job/<id>/delete` |
| `/admin/nutzer/<id>/status` | `/admin/users/<id>/status` |

---

## 1.0.0 — 29.07.2026

Erste Fassung im Betrieb: Upload und Konvertierung über Docling, Konten mit
E-Mail-Bestätigung, Fair-Use-Grenzen, Verwaltungsbereich, Rechtstexte,
Reichweitenmessung über die eigene Domain. Rückfallimage dieses Stands liegt
als `klartext-app:1.0.0-vor-i18n` auf dem Server.
