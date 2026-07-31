# Changelog

Was wann veröffentlicht wurde. Die Versionsnummer ist zugleich der Tag des
Docker-Images (`klartext-app:<Version>`), das auf dem Server läuft.

**Aktuell live: 1.1.2** (seit 31.07.2026)

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
