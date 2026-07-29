<div align="center">

<img src="app/klartext/static/icon-192.png" alt="" width="88" height="88">

# Klartext

**Dokumente, Scans und Fotos werden sauberes Markdown.**
Selbst gehostet, ohne KI-Anbieter, dauerhaft kostenlos.

[![Tests](https://img.shields.io/badge/Tests-59%2F59-15803D)](tests/e2e.py)
[![Engine](https://img.shields.io/badge/Engine-Docling%20v1.28.0-1E3A5F)](THIRD_PARTY_LICENSES.md)
[![OCR](https://img.shields.io/badge/OCR-RapidOCR%20lokal-15803D)](THIRD_PARTY_LICENSES.md)
[![Datenschutz](https://img.shields.io/badge/Verarbeitung-nur%20eigener%20Server-1E3A5F)](SECURITY.md)
[![Status](https://img.shields.io/badge/Status-im%20Betrieb-15803D)](https://klartext.it-handwerk-stuttgart.de)

[Live ansehen](https://klartext.it-handwerk-stuttgart.de) ·
[Architektur](ARCHITECTURE.md) ·
[Betrieb](DEPLOYMENT.md) ·
[Sicherheit](SECURITY.md) ·
[Lizenzen](THIRD_PARTY_LICENSES.md)

</div>

---

PDF, Foto, Scan, Word, Excel oder PowerPoint hochladen — heraus kommen zwei Dateien:
lesbares **Markdown** zum Weiterverwenden und strukturtreues **JSON** für die
maschinelle Weiterverarbeitung. Die Umwandlung läuft vollständig auf dem eigenen
Server. Es gehen keine Inhalte an OpenAI, Anthropic, Google oder einen anderen KI-,
OCR- oder Cloud-Dienst.

![Vorher und nachher](app/klartext/static/og.png)

Dauerhaft kostenlos: keine Tarife, keine Zahlung, keine gesperrten Funktionen. Alle
Konten haben denselben Funktionsumfang. Die vorhandenen Grenzen sind reine
Fair-Use-Grenzen zum Schutz des Servers.

## Was es kann

- Registrierung, Anmeldung, Abmeldung, Passwort ändern, Passwort vergessen,
  E-Mail-Bestätigung, Konto vollständig löschen
- Mehrere Dateien gleichzeitig per Drag-and-Drop hochladen
- Live-Status je Auftrag: Warteschlange, Verarbeitung, Fertig, Fehler
- Markdown ansehen, kopieren, als `.md` herunterladen
- Strukturierte `.json`-Ausgabe herunterladen (vollständige `DoclingDocument`-Struktur)
- Mehrere Ergebnisse gesammelt als ZIP
- Automatische Löschung nach einer einstellbaren Aufbewahrungszeit (Vorgabe 24 Stunden)
- Admin-Bereich: Konten sehen und deaktivieren, Auslastung, fehlgeschlagene Aufträge,
  alle technischen Grenzen zur Laufzeit ändern

## Unterstützte Formate

Getestet und freigegeben: **PDF, PNG, JPG/JPEG, TIFF, WEBP, BMP, DOCX, XLSX, PPTX,
HTML, MD**.

Ausgabe je Dokument: `originalname.md` und `originalname.json`.

Markdown kann bestimmte Layoutmerkmale technisch nicht abbilden — mehrspaltige
Seiten, beliebig verbundene Tabellenzellen, exakte Positionen. Die JSON-Ausgabe ist
deshalb die strukturtreuere Variante. Ein pixelgenaues Abbild des Originals ist
Markdown nicht und kann es auch nicht sein; das wird in der Oberfläche auch so gesagt.

## Texterkennung

Für Fotos und Scans läuft **RapidOCR**. Ausgewählt nach einer Messung über vier
Testbilder mit 45 einzeln geprüften Pflichtangaben (Namen, Straßen, Artikelnummern,
Beträge, Umlaute, Gradzeichen):

| Engine | Treffer | Quote |
|---|---|---|
| **RapidOCR** | 44 / 45 | **98 %** |
| EasyOCR | 34 / 45 | 76 % |
| Tesseract (deu+eng) | 19 / 45 | 42 % |

EasyOCR verlor reproduzierbar Beträge (`8,40` → `8,4C`), Tesseract scheiterte an
Tabellen in Bildern fast vollständig. Tesseract inklusive deutschem Sprachpaket
bleibt als Alternative eingerichtet (`OCR_ENGINE=tesseract`).

**Die Auflösung der Vorlage entscheidet mit.** Ein Foto mit zu kleinem Text verliert
Umlaute und ganze Tabellenzeilen; auch der einzige Fehltreffer von RapidOCR — eine
Telefonnummer mit Leerzeichen und Schrägstrich — trat nur im niedrig aufgelösten
Bild auf. Bei Handyfotos also nah genug herangehen und nicht künstlich verkleinern.

## Verlustarm heißt hier

Kein Zusammenfassen, kein Umformulieren, keine Rechtschreibkorrektur, keine
erfundenen Inhalte. Alle Docling-Anreicherungen, die Inhalte durch ein Modell
*erzeugen* statt sie zu *lesen*, sind abgeschaltet (Bildbeschreibung,
Diagrammauswertung, Code- und Formel-Anreicherung). Erhalten bleiben Originaltext,
Schreibweise, Zahlen, Währungen, Datumsangaben, Namen, Überschriften, Absätze,
Listen, Tabellen samt Struktur, Lesereihenfolge und Seitenstruktur.

## Oberfläche

Serverseitig gerendertes HTML, kein Frontend-Framework. Das ausgelieferte JavaScript
ist eigener Code und dient nur dem Upload-Fortschritt, der Statusaktualisierung und
dem Kopieren. Die Seite funktioniert ohne JavaScript, nur ohne Live-Aktualisierung.

- Stile in `static/app.css` und `static/ui.css` (Gestaltungsebene darüber)
- Alle Symbole und Illustrationen sind selbst gezeichnete Inline-SVGs, keine
  Bilddateien und kein Icon-Paket. Sie übernehmen die Farben des Themas und
  funktionieren dadurch in hell und dunkel.
- Statische Dateien tragen eine Inhalts-Kennung (`app.css?v=…`), weil Cloudflare
  `/static/*` vier Stunden cacht
- Startbildschirm-Symbole für iOS, Android und Desktop plus `site.webmanifest` mit
  `display: browser` — bewusst **kein** PWA: kein Service Worker, keine
  Installationsaufforderung
- `static/og.png` als Vorschaubild beim Teilen (1200×630)

## Technik in einem Absatz

FastAPI mit serverseitig gerenderten Jinja2-Vorlagen, PostgreSQL 16, ein eigener
Worker-Prozess und Docling Serve als Konvertierungs-Engine — alles in vier
Docker-Containern in einem eigenen Netz. Kein Frontend-Framework, kein CDN, keine
Webfonts, kein Tracking. Details in [ARCHITECTURE.md](ARCHITECTURE.md).

## Betrieb

```bash
cd /home/belkis/klartext

docker compose ps                      # Zustand
docker compose up -d                   # starten
docker compose stop                    # anhalten
docker compose restart web worker      # Anwendung neu starten
docker compose logs -f web             # Protokoll Weboberfläche
docker compose logs -f worker          # Protokoll Verarbeitung
```

Vollständige Anleitung inklusive Update, Sicherung, Wiederherstellung und
Rollback: [DEPLOYMENT.md](DEPLOYMENT.md).

## Tests

```bash
python3 tests/e2e.py                   # gegen die öffentliche Adresse
python3 tests/e2e.py http://127.0.0.1:8160
```

Der Test legt eigene Konten an, konvertiert die Dateien aus `tests/fixtures`, prüft
Benutzerisolation, Limits, Sicherheits-Header und räumt am Ende auf.

## Sicherheit

Argon2id für Passwörter, Sitzungstoken nur als Hash gespeichert, HttpOnly- und
Secure-Cookies, CSRF-Schutz, strenge Content-Security-Policy ohne `unsafe-inline`,
Inhaltstypprüfung statt Dateiendungsvertrauen, zufällige interne Dateinamen, jede
Ressource serverseitig an eine `user_id` gebunden. Details und durchgeführter Review:
[SECURITY.md](SECURITY.md).

## Lizenzen

Eingesetzte Fremdkomponenten mit Version, Lizenz und Urheberrechtsvermerk:
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md), im Dienst öffentlich unter
`/lizenzen`.

Klartext ist ein eigenständiger Dienst und steht in keiner Verbindung zu IBM oder
zum Docling-Projekt. Docling ist ausschließlich die technische Engine im Hintergrund.

## Marke

Name, Logo und Gestaltung sind eigenständig: [brand/BRAND.md](brand/BRAND.md).

## Lizenz dieses Projekts

Noch nicht festgelegt. Ohne Lizenzdatei gilt das gesetzliche Urheberrecht: alle Rechte
vorbehalten. Für ein privates Repository ist das der sichere Ausgangszustand. Soll der
Code weitergegeben werden, gehört eine Lizenzdatei dazu — MIT wäre die naheliegende
Wahl, weil auch die eingesetzten Fremdkomponenten unter MIT und Apache-2.0 stehen.

Die Lizenzen der **verwendeten** Fremdkomponenten sind davon unberührt und vollständig
in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) dokumentiert.
