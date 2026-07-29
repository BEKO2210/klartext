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
