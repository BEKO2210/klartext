# Architektur

## Überblick

```
Browser (Handy / Desktop)
   │  HTTPS
   ▼
Cloudflare (Proxy, TLS, Bot-Schutz)
   │  Cloudflare-Tunnel (cloudflared, dashboard-verwaltet)
   ▼
127.0.0.1:8160                      ← einziger öffentlich erreichbarer Punkt
   │
   ▼
klartext-web  (FastAPI, Jinja2)     Docker-Netz „klartext-internal"
   │  ├── Auth, Sitzungen, CSRF, Rate-Limits
   │  ├── Upload-Prüfung (Endung + echter Inhaltstyp)
   │  ├── Fair-Use-Kontrolle
   │  └── legt Job an, schreibt Datei auf Platte
   │
   ├──────────────► klartext-db (PostgreSQL 16)   kein Host-Port
   │                 users, sessions, jobs, files, usage_events,
   │                 rate_limits, app_settings, audit_log
   │
   ▼
klartext-worker (eigener Prozess, 2 parallel)
   │  holt Jobs per FOR UPDATE SKIP LOCKED
   │
   ▼
klartext-docling (docling-serve-cpu v1.28.0)     kein Host-Port
   │  X-Api-Key erforderlich, Gradio-UI aus, URL-Import aus
   ▼
lokale Modelle im Image (Layout, TableFormer, Tesseract)
```

Nur `klartext-web` ist von außen erreichbar, und auch nur an `127.0.0.1` gebunden.
Datenbank und Docling-API haben **kein** Port-Mapping auf den Host — sie sind
ausschließlich innerhalb des Docker-Netzes `klartext-internal` ansprechbar.

## Warum diese Aufteilung

**Eigener Web-Layer statt Docling-UI.** Die mitgelieferte Gradio-Oberfläche von
Docling Serve ist eine Demo ohne Benutzerkonten, ohne Mandantentrennung und ohne
Limits. Sie ist per `DOCLING_SERVE_ENABLE_UI=false` abgeschaltet. Die öffentliche
Oberfläche ist vollständig eigener Code.

**Warteschlange in PostgreSQL statt Redis.** Es gibt bereits ein produktives Redis
auf dem Server (Appwrite, Asto-Finance). Das wird bewusst nicht mitbenutzt. Ein
eigenes Redis wäre ein weiterer Container für eine Aufgabe, die PostgreSQL mit
`SELECT ... FOR UPDATE SKIP LOCKED` sauber und dauerhaft erledigt — inklusive
Neustart-Festigkeit, die eine reine In-Memory-Queue nicht hat. Weniger bewegliche
Teile, gleiche Garantien.

**Worker getrennt vom Web-Prozess.** Eine Konvertierung dauert Sekunden bis Minuten
und belegt CPU. Läge sie im Web-Prozess, würde eine große PDF die Oberfläche für
alle blockieren. Getrennt bleibt die Weboberfläche jederzeit bedienbar, und der
Worker lässt sich unabhängig neu starten.

**Eigene Datenbank statt der vorhandenen Appwrite-Instanz.** Appwrite ist produktiv
für andere Projekte im Einsatz. Ein neues Schema dort anzulegen hätte fremde
Produktivdaten berührt. Die eigene PostgreSQL-Instanz ist vollständig isoliert und
kann ohne Rücksicht auf andere Dienste gesichert, migriert oder gelöscht werden.

## Datenfluss einer Konvertierung

1. Browser sendet Multipart-Upload an `POST /app/upload` inklusive CSRF-Feld.
2. Middleware prüft: Rate-Limit pro IP, Sitzung, `Content-Length` gegen das Body-Limit.
3. Route prüft je Datei: Endung erlaubt, tatsächlicher Inhaltstyp (libmagic) passt zur
   Endung, PDF-Kopf vorhanden, Seitenzahl (pypdf) unter dem Limit.
4. Fair-Use-Prüfung für den gesamten Stapel — erst danach wird irgendetwas geschrieben.
5. Datei landet unter `/data/uploads/<2 Hex>/<32 Hex>` — zufälliger Name ohne Endung,
   Rechte 0600. Der Originalname existiert nur als Datenbankfeld.
6. Job-Zeile mit `status='queued'` und `expires_at = now() + Aufbewahrungszeit`.
7. Worker reserviert den Job, sendet die Datei an Docling Serve
   (`POST /v1/convert/file`, `to_formats=md,json`).
8. Ergebnis wird als zwei Dateien unter `/data/results/...` abgelegt, Job auf `done`
   gesetzt, Seitenzahl und Dauer festgehalten, Verbrauch gezählt.
9. Die Quelldatei wird zehn Minuten nach Abschluss gelöscht — sie wird nicht mehr
   gebraucht.
10. Nach Ablauf der Aufbewahrungszeit räumt der Worker Ergebnisse und Job weg.

## Verlustarme Umwandlung

Die Docling-Aufrufparameter sind bewusst gesetzt (`docling_client.py`):

| Parameter | Wert | Grund |
|---|---|---|
| `do_table_structure` | true | Tabellen bleiben Tabellen |
| `table_mode` | accurate | genauere Zellzuordnung, dafür langsamer |
| `do_ocr` | true, `force_ocr` false | OCR nur wo nötig; eingebetteter Text wird direkt übernommen |
| `pdf_backend` | docling_parse | Lesereihenfolge und Textpositionen |
| `pipeline` | standard | keine VLM-Pipeline, kein Sprachmodell |
| `do_code_enrichment` | false | kein Modell schreibt Code um |
| `do_formula_enrichment` | false | keine Formel-Neuinterpretation |
| `do_picture_description` | false | keine erfundenen Bildbeschreibungen |
| `do_chart_extraction` | false | keine geratenen Diagrammwerte |

Alle Anreicherungen, die Inhalte durch ein Modell *erzeugen* statt *lesen*, sind aus.
Damit gibt es keine Zusammenfassung, keine Umformulierung und keine erfundenen Inhalte.

`md_page_break_placeholder` setzt eine Seitenmarke ins Markdown, damit die
Seitenstruktur nachvollziehbar bleibt. Die JSON-Ausgabe enthält die vollständige
`DoclingDocument`-Struktur mit Seiten, Blöcken, Bounding-Boxen und Tabellenzellen.

## Layouttreue (`layout.py`)

Drei Dinge gibt die Vorlage her, die auf dem Weg nach Markdown verloren gehen.
Sie werden im Worker vor bzw. nach den Textregeln wiederhergestellt — immer nur
im Markdown, die JSON-Ausgabe wird nicht angefasst.

| Verlust | Was passiert | Regel |
|---|---|---|
| Gliederungstiefe (nummeriert) | Das Layoutmodell erkennt Überschriften, aber keine Ebenen: `1`, `1.1` und `1.1.1` kommen alle als `##` heraus | Ebene aus der Nummer der Vorlage herleiten (`1` → `##`, `1.1` → `###`). Der Text bleibt Zeichen für Zeichen stehen |
| Gliederungstiefe (ohne Nummer) | Titel und Abschnitte landen auf derselben Ebene | Ebene aus der Zeilenhöhe (`texts[].prov[].bbox`) ableiten: Gruppen bilden, nur bei klarer Trennung anwenden. Auf Scans misst die Höhe Ober- und Unterlängen statt der Schriftgröße — dort greift die Regel nie |
| Verbundene Zellen | Markdown kennt kein `rowspan`; Docling füllt jede überdeckte Rasterstelle mit demselben Text — aus einer Zelle über vier Spalten werden vier gleiche Zellen | Tabellen **mit** Verbund werden als HTML-Tabelle (`rowspan`/`colspan`, `thead`/`tbody`) ins Markdown geschrieben. Tabellen ohne Verbund bleiben im Markdown-Raster |
| Lesereihenfolge bei Spaltensatz | Die rechte Spalte hängt hinter allem anderen | Spaltenbänder über die Seitenmitte bestimmen, an durchgehenden Blöcken trennen, die Zone mit Text in **beiden** Spalten spaltenweise sortieren. Nur bei reinem Fließtext im Abschnitt |
| Zerschnittene Absätze | Spalten- oder Seitenumbruch trennt einen Satz | Wieder zusammenfügen, wenn der erste Teil ohne Satzzeichen endet und der zweite klein beginnt |
| Verschachtelte Listen | Eine Unterliste („a., b.") landet auf der Ebene der Hauptliste | Einrücken, wenn ein lückenloser Buchstabenblock zwischen zwei Zifferpunkten steht |

Die Kette selbst steht in `nachbearbeitung.py` — dieselbe Funktion nutzen der
Worker und der Messstand in `bench/`. Nur so ist sicher, dass gemessen wird,
was ausgeliefert wird.

Jede Regel prüft sich selbst und lässt das Dokument unverändert, sobald die
Belege nicht reichen: Überschriften nur ab drei nummerierten Treffern, bei nur
einer vorhandenen Ebene und mit Elternprüfung (`1.1` braucht ein `1`); Tabellen
nur, wenn die Kopfzeile des Markdown-Blocks Zelle für Zelle zur Tabelle in der
Struktur passt. Zellentext wird beim HTML-Bau maskiert (`&`, `<`, `>`).

`MERGED_TABLES=raster` schaltet den HTML-Weg ab und lässt alle Tabellen im
flachen Markdown-Raster. Die Verbünde stehen in beiden Fällen vollständig in der
JSON-Ausgabe (`row_span`, `col_span`, `start_row_offset_idx` …).

Geprüft wird das deterministisch gegen nachgebaute Docling-Strukturen:
`python3 tests/layout_test.py` (läuft auch in `tests/e2e.py` als Prüfung 43c).

## Sprachen

Englisch ist die Standardfassung und liegt auf den blanken Pfaden, Deutsch unter
`/de`. Beispiel: `/login` und `/de/anmelden`. Der Zulauf kommt überwiegend aus
dem englischsprachigen Raum, deutsche Bestandsnutzer sollen aber nichts verlieren.

* **Texte:** `strings_en.py` und `strings_de.py`, ein Schlüssel je Satz. Fehlt ein
  deutscher Schlüssel, greift automatisch der englische — nie eine leere Stelle.
* **Auswahl je Anfrage** (`i18n.py`, Middleware in `main.py`): Sprache im Pfad
  schlägt Sprachcookie, Cookie schlägt `Accept-Language`. Wer laut Browser Deutsch
  bevorzugt und noch nichts gewählt hat, wird einmalig von `/…` auf `/de/…`
  geschickt. Der Umschalter in der Kopfzeile setzt `klartext_lang` und beendet
  diese Automatik.
* **Alte deutsche Adressen** (`/anmelden`, `/lizenzen`, `/konto`,
  `/app/auftrag/<id>` …) antworten dauerhaft mit 301, Formularpfade mit 308.
  Suchtreffer und fremde Verweise laufen dadurch nicht ins Leere.
* **Angemeldeter Bereich:** eine Adresse für beide Sprachen (`/app`, `/account`,
  `/admin`). Dort indexiert niemand, und ein Sprachwechsel soll keine
  Auftragsadresse verändern.
* **Suchmaschinen:** `hreflang`-Paare plus `x-default` in jeder öffentlichen
  Seite, beide Fassungen in `sitemap.xml`, `Vary: Accept-Language, Cookie` auf
  allen HTML-Antworten.
* **Ergebnisse:** `jobs.lang` hält fest, in welcher Sprache ein Auftrag
  eingestellt wurde. Der Worker schreibt Hinweise und Zusatzabschnitte im
  Markdown in derselben Sprache.
* **Browser-Texte:** `app.js` und `job.js` lesen ihre Sätze aus einem Datenblock
  in der Seite (`#i18n-daten`). Inline-JavaScript verbietet die Inhaltsrichtlinie.
* **Rechtstexte:** Die deutsche Fassung ist die maßgebliche; die englische trägt
  einen Hinweis darauf.

## Sitzungen

Beim Anmelden wird ein Zufallstoken (32 Byte) erzeugt. Der Browser bekommt es als
Cookie `klartext_session` (HttpOnly, Secure, SameSite=Lax). Gespeichert wird nur der
SHA-256-Hash — wer die Datenbank liest, kann sich damit nicht anmelden.

Kein JWT, nichts im `localStorage`. Jede Anmeldung erzeugt ein neues Token
(kein Session Fixation). Passwortwechsel und Passwort-Reset beenden alle Sitzungen
des Kontos.

CSRF: Angemeldete Formulare tragen das Token der Sitzung. Anonyme Formulare
(Anmelden, Registrieren) nutzen ein Doppel-Cookie-Verfahren. Zusätzlich verhindert
`SameSite=Lax` die meisten fremden Einreichungen bereits im Browser.

## Fair-Use

Grenzen kommen aus `config.py` (Environment) und können vom Admin zur Laufzeit in
`app_settings` überschrieben werden; `settings_store.py` löst beides mit 15 Sekunden
Cache auf. Kein Wert steht fest im Code verteilt.

Es gibt bewusst **kein** Tarif-, Zahlungs- oder Abrechnungsmodell — weder in der
Datenbank noch in der Oberfläche. `usage_events` zählt ausschließlich zur
Serverentlastung.

## Ressourcen

Der Server hat 8 Threads (Xeon E3-1505M v5) und 31 GB RAM und betreibt daneben
Jellyfin, Appwrite, Matrix, mehrere Next.js-Anwendungen und einen Minecraft-Server.
Deshalb konservativ:

- Docling: 2 Engine-Worker × 2 Torch-Threads, CPU-Limit 4.0, Speicherlimit 8 GB
- Worker: 2 gleichzeitige Jobs, Speicherlimit 512 MB
- Web: 512 MB, Datenbank: 768 MB

Die GPU (Quadro M2000M, 4 GB, Maxwell) wird **nicht** verwendet: 4 GB VRAM sind für
die Layout- und Tabellenmodelle knapp, die Architektur ist alt, und die Karte wird
von anderen Diensten mitbenutzt. Stabilität geht vor Geschwindigkeit.

## Was nicht nach außen geht

Es gibt keinen ausgehenden Netzwerkverkehr mit Dokumentinhalten. Die Modelle liegen
fertig im Docling-Image (`/opt/app-root/src/.cache/docling/models`), `HF_HUB_OFFLINE=1`
verhindert Nachladeversuche. `DOCLING_SERVE_ENABLE_REMOTE_SERVICES=false` schließt
externe KI-Dienste aus, `DOCLING_SERVE_ALLOWED_SOURCE_TYPES=["file"]` schließt den
URL-Import und damit SSRF aus.

Ausgehend erreicht der Server nur den SMTP-Server für Bestätigungs- und Reset-Links.
Diese Mails enthalten ausschließlich einen Link — nie Dateinamen, nie Inhalte.
