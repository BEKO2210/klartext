# Hinweise für KI-Agenten

Diese Datei gilt für alle automatischen Änderungen an diesem Projekt. Sie ist
verbindlich — auch dann, wenn eine Aufgabenstellung etwas anderes nahelegt.

## Was dieses Projekt ist

**Klartext** wandelt Dokumente, Scans und Fotos in Markdown und strukturtreues JSON.
Öffentlich registrierbar, dauerhaft kostenlos, mehrbenutzerfähig. Läuft unter
`klartext.it-handwerk-stuttgart.de` auf einem privaten Heimserver, auf dem parallel
rund zwanzig weitere produktive Dienste laufen.

Vier Container: `klartext-web`, `klartext-worker`, `klartext-db`, `klartext-docling`.
Details in [ARCHITECTURE.md](ARCHITECTURE.md), Betrieb in [DEPLOYMENT.md](DEPLOYMENT.md).

## Absolute Grenzen

**Nichts außerhalb von `/home/belkis/klartext` anfassen.** Auf dem Server laufen
Jellyfin, Appwrite, Matrix, mehrere Next.js-Anwendungen und ein Minecraft-Server.
Kein fremder Container, kein fremdes Volume, kein fremdes Netz, kein
`docker system prune`, kein nginx, keine Firewallregel, kein Serverneustart.

**Cloudflare-Tunnel:** Die Ingress-Liste enthält über 40 Hostnames für alle anderen
Dienste. Die API kennt kein „anhängen" — sie ersetzt die gesamte Konfiguration. Wer
sie nicht vorher liest und unverändert übernimmt, nimmt alle anderen Dienste vom Netz.
Die Catch-all-Regel muss die letzte bleiben.

**Keine Zugangsdaten in Dateien, Logs oder Commits.** Secrets liegen ausschließlich im
Vault des Knowledge-Hubs. `.env` und `backups/` sind von Git ausgeschlossen und müssen
es bleiben — in `backups/` liegen Datenbankabzüge und `.env`-Kopien im Klartext.

## Was das Produkt verspricht — und niemals brechen darf

**Dokumentinhalte verlassen den Server nicht.** Keine Weitergabe an OpenAI, Anthropic,
Google, externe OCR- oder Vision-Dienste, Analyse- oder Fehlerprotokoll-Anbieter. In
Docling sind alle Anreicherungen abgeschaltet, die Inhalte durch ein Modell *erzeugen*
statt sie zu *lesen* (Bildbeschreibung, Diagrammauswertung, Code- und
Formel-Anreicherung). Wer eine davon einschaltet, bricht das Kernversprechen.

**Keine Dokumentinhalte und keine Dateinamen in Protokolle.** Der Worker meldet
ausschließlich Fehlerart, Dauer und Seitenzahl.

**Verlustarm heißt wörtlich:** nichts zusammenfassen, nichts umformulieren, nichts
korrigieren, nichts erfinden.

**Kostenlos heißt kostenlos.** Kein Billing-Datenmodell, keine Tarife, keine
gesperrten Funktionen, keine Wörter wie Upgrade, Premium, Pro oder Credits. Die
vorhandenen Grenzen sind reiner Serverschutz.

## Technische Fallstricke

**Strenge CSP ohne `unsafe-inline`.** `style="..."`-Attribute und Inline-`<script>`
werden vom Browser stillschweigend verworfen — das Layout sitzt dann daneben, ohne
dass man dem Code etwas ansieht. Genau das ist hier schon einmal mit 33 Attributen
passiert. Ausnahme: `<script type="application/ld+json">` ist zulässig.
Keine externen Ressourcen, kein CDN, keine Webfonts, kein Tracking.

**Diese Namen hängen am JavaScript und dürfen sich nicht ändern:**
`upload-form`, `file-input`, `dropzone`, `file-list`, `upload-button`,
`clear-button`, `upload-message`, `job-list`, `zip-button`, `usage-line`,
`empty-state`, `markdown-source`, `copy-button`, `copy-status`, sowie die
Formularfelder `csrf` und `files`.

**URLs bleiben ASCII** (`/loeschen`, `?geaendert=1`). Sichtbarer Text dagegen mit
korrekten Umlauten. Eine blinde Umlaut-Ersetzung hat hier schon einmal die Route
umbenannt und alle Löschknöpfe auf 404 laufen lassen.

**Cloudflare cacht `/static/*` vier Stunden.** Statische Verweise tragen deshalb eine
Inhalts-Kennung über `web_helpers.asset()`. Wer sie umgeht, liefert nach jedem Deploy
stundenlang altes JavaScript aus.

**Grenzwerte nie fest eintippen.** Immer `limits.*` und `usage.*` verwenden. Eine
eingetippte Zahl ist falsch, sobald jemand die Grenze im Admin-Bereich ändert.

**httpx 0.28 und Multipart:** `data=` muss ein Dict sein, Mehrfachwerte als Liste.
Eine Liste von Tupeln führt zu `Attempted to send an sync request with an
AsyncClient instance` — und damit läuft keine einzige Konvertierung.

**Starlette 1.3:** `TemplateResponse(request, name, context)`, nicht die alte Reihenfolge.

**Tests dürfen nichts verändern, was Besucher sehen.** `app_settings` ist global und
wirkt sofort auf der öffentlichen Startseite.

## Oberfläche

Zielgruppe sind **keine Entwickler**: Handwerksbetriebe, Büros, Selbstständige,
Studierende. Fachjargon ist ein Fehler. Der Betreiber arbeitet fast ausschließlich am
Handy — **jede Änderung bei 412 px prüfen**, auch im Admin-Bereich.

**Kurz halten.** Lange Erklärabsätze werden nicht gelesen. Wo etwas ausführlich sein
muss, gehört es hinter ein `<details>` oder ins FAQ.

Alle Symbole und Illustrationen sind selbst gezeichnete Inline-SVGs mit
`stroke="currentColor"`. Keine Icon-Bibliothek, keine Emoji als Symbole, keine
Rasterbilder für Grafiken — sie brechen den Dunkelmodus und wiegen ein Vielfaches.
Stile: `static/app.css`, darüber die Gestaltungsebene `static/ui.css`.

## Vor jeder Freigabe

```bash
cd /home/belkis/klartext
docker compose build web && docker compose up -d --force-recreate web
python3 tests/e2e.py          # 59 Prüfungen, alle müssen bestehen
```

Der Testlauf prüft auch, dass die anderen Dienste des Servers weiterhin erreichbar
sind. Cloudflare weist Anfragen ohne echten Browser-User-Agent mit 403 ab — das ist
Bot-Schutz, kein Ausfall.

**Nichts als bestanden melden, was nicht tatsächlich ausgeführt wurde.** Screenshots
ansehen, nicht nur erzeugen. Berechnete Werte messen, statt sie aus dem Code
abzuleiten — Selektor-Spezifität und CSS-Reihenfolge haben hier mehrfach anders
gewirkt als erwartet.

## Was von außen sichtbar sein darf

Ausschließlich die Weboberfläche. Datenbank und Docling-API haben kein Port-Mapping,
die eigene API-Dokumentation ist abgeschaltet, der Admin-Bereich antwortet
Unbefugten mit 404 statt mit einer Weiterleitung. Fremde Aufträge liefern 404, nicht
403 — es wird nicht einmal bestätigt, dass eine Kennung existiert.
