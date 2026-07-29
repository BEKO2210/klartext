# Betrieb und Deployment

## Eckdaten

| | |
|---|---|
| Projektpfad | `/home/belkis/klartext` |
| Öffentliche Adresse | https://klartext.it-handwerk-stuttgart.de |
| Host-Port | `127.0.0.1:8160` (nur lokal gebunden) |
| Docker-Projekt | `klartext` |
| Docker-Netz | `klartext-internal` |
| Container | `klartext-web`, `klartext-worker`, `klartext-db`, `klartext-docling` |
| Volumes | `klartext-db`, `klartext-docling-scratch` |
| Bind-Mounts | `./data/uploads`, `./data/results`, `./ocr/tessdata/deu.traineddata` (ro) |
| Docling | `quay.io/docling-project/docling-serve-cpu:v1.28.0` |
| Datenbank | `postgres:16.11-alpine` |
| Anwendungs-Image | `klartext-app:1.0.0` (lokal gebaut) |

Container laufen als UID 1000, damit die Bind-Mounts unter `data/` dem Benutzer
`belkis` gehören und sich ohne `sudo` sichern lassen.

## Öffentlicher Zugang

Der Zugriff läuft über den bestehenden Cloudflare-Tunnel (Container `cloudflared`,
Image `wisdomsky/cloudflared-web:2025.2.1`). Der Tunnel wird **remote im
Cloudflare-Dashboard verwaltet** — es gibt keine lokale Ingress-Datei.

Eingerichtet wurde:

1. **Ingress-Regel** im Tunnel `a4860871-56b1-41f4-9620-f8f0cbf2f0f2`
   (Account `32b93e37e2b1c69f6aba1ff65878507d`):
   `klartext.it-handwerk-stuttgart.de` → `http://localhost:8160`.
   Eingefügt **vor** der Catch-all-Regel; alle 42 vorhandenen Regeln blieben
   unverändert. Sicherung des Zustands davor:
   `backups/cloudflare-tunnel-config-20260729-002341.json`.
2. **DNS-Eintrag** in der Zone `it-handwerk-stuttgart.de`
   (`a281908bd08d6fd8ca9e1febd40595b9`):
   `CNAME klartext → a4860871-56b1-41f4-9620-f8f0cbf2f0f2.cfargotunnel.com`, proxied.

Es wurde **kein** nginx angefasst und **kein** zweiter Reverse Proxy installiert.

### Falls die Ingress-Regel wiederhergestellt werden muss

```bash
CF_TOKEN='<Token aus dem Vault: Cloudflare_API>'
ACC=32b93e37e2b1c69f6aba1ff65878507d
TUN=a4860871-56b1-41f4-9620-f8f0cbf2f0f2

# aktuellen Stand lesen und sichern
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$ACC/cfd_tunnel/$TUN/configurations" \
  > backups/cloudflare-tunnel-$(date +%Y%m%d-%H%M%S).json

# eine gesicherte Fassung zurückspielen
python3 - <<'PY'
import json, os, urllib.request
cfg = json.load(open('backups/cloudflare-tunnel-config-20260729-002341.json'))['result']['config']
req = urllib.request.Request(
    "https://api.cloudflare.com/client/v4/accounts/%s/cfd_tunnel/%s/configurations" % (
        "32b93e37e2b1c69f6aba1ff65878507d", "a4860871-56b1-41f4-9620-f8f0cbf2f0f2"),
    data=json.dumps({"config": cfg}).encode(), method="PUT",
    headers={"Authorization": "Bearer " + os.environ["CF_TOKEN"],
             "Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req))["success"])
PY
```

**Wichtig:** Die Catch-all-Regel (`http_status:404`, ohne `hostname`) muss immer die
letzte bleiben. Neue Regeln immer davor einfügen, nie die Liste ersetzen.

## Start, Stopp, Neustart

```bash
cd /home/belkis/klartext

docker compose up -d                    # alles starten
docker compose stop                     # alles anhalten (Daten bleiben)
docker compose restart web worker       # nur die Anwendung
docker compose down                     # Container entfernen, Volumes bleiben
docker compose ps
```

`docker compose down -v` würde die Datenbank löschen — nicht verwenden, außer das ist
ausdrücklich gewollt.

## Protokolle

```bash
docker compose logs -f web
docker compose logs -f worker
docker compose logs --since 1h docling
docker compose logs --tail 200 db
```

Es werden bewusst keine Dokumentinhalte und keine Dateinamen protokolliert. Der
Worker meldet nur Fehlerart, Dauer und Seitenzahl.

## Konfiguration ändern

Alle Werte stehen in `.env` (Rechte 600, nicht in Git). Vorlage: `.env.example`.

```bash
nano .env
docker compose up -d web worker         # übernimmt die Änderung
```

Die Fair-Use-Grenzen lassen sich zusätzlich **ohne Neustart** im Admin-Bereich unter
`/admin` ändern; diese Werte liegen in der Tabelle `app_settings` und haben Vorrang
vor `.env`. Ein Wert lässt sich auf die `.env`-Vorgabe zurücksetzen, indem die Zeile
in `app_settings` gelöscht wird:

```bash
docker exec klartext-db psql -U klartext -d klartext \
  -c "DELETE FROM app_settings WHERE key = 'max_pages'"
```

## Benutzerverwaltung

Der **erste registrierte Account wird automatisch Admin.** Weitere Admins nur direkt
in der Datenbank:

```bash
docker exec klartext-db psql -U klartext -d klartext \
  -c "UPDATE users SET is_admin = TRUE WHERE email_norm = 'adresse@example.com'"
```

Konto deaktivieren (beendet auch alle laufenden Sitzungen) geht über `/admin`.
Konto samt allen Dateien löschen:

```bash
docker exec klartext-db psql -U klartext -d klartext \
  -c "DELETE FROM users WHERE email_norm = 'adresse@example.com'"
```

Achtung: Der Datenbankeintrag kaskadiert auf Sitzungen, Aufträge, Dateien und
Verbrauchszähler, aber die Dateien auf der Platte räumt in diesem Fall erst der
nächste Aufräumlauf des Workers weg (spätestens nach fünf Minuten). Der Weg über
„Konto löschen" in der Oberfläche löscht beides sofort.

## Sicherung

Zu sichern sind: Datenbank, `.env`, die Tunnel-Konfiguration und der Projektstand.
Temporäre Uploads und Ergebnisse **nicht** — sie werden ohnehin automatisch gelöscht.

```bash
cd /home/belkis/klartext
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backups

# Datenbank
docker exec klartext-db pg_dump -U klartext -d klartext --clean --if-exists \
  | gzip > "backups/db-$STAMP.sql.gz"

# Konfiguration und Secrets (Rechte beibehalten!)
tar czf "backups/config-$STAMP.tar.gz" .env docker-compose.yml
chmod 600 "backups/config-$STAMP.tar.gz"

# Tunnel-Konfiguration
CF_TOKEN='<Token aus dem Vault>' \
curl -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/32b93e37e2b1c69f6aba1ff65878507d/cfd_tunnel/a4860871-56b1-41f4-9620-f8f0cbf2f0f2/configurations" \
  > "backups/cloudflare-tunnel-$STAMP.json"
```

Die Sicherungen enthalten mit `.env` echte Zugangsdaten und mit dem Dump
Argon2id-Hashes. Passwörter liegen nirgends im Klartext — weder in der Datenbank
noch in einer Sicherung. Sicherungsdateien trotzdem nur mit Rechten 600 ablegen und
nicht in Git aufnehmen (`.gitignore` deckt `.env` ab; `backups/` sollte ebenfalls
nicht eingecheckt werden).

## Wiederherstellung

```bash
cd /home/belkis/klartext
docker compose stop web worker            # keine Schreibzugriffe während des Einspielens
gunzip -c backups/db-20260729-004500.sql.gz \
  | docker exec -i klartext-db psql -U klartext -d klartext
docker compose up -d web worker
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8160/healthz
```

Der Dump wurde mit `--clean --if-exists` erzeugt, spielt sich also über einen
bestehenden Stand ein. Getestet wurde die Wiederherstellung gegen eine
Wegwerf-Datenbank, nicht gegen die Produktivdatenbank — ein Einspielen dort
überschreibt echte Konten.

## Update

Keine `latest`-Tags im Betrieb. Alle Versionen sind in `docker-compose.yml` und
`app/requirements.txt` fest angegeben.

Vor einem Docling-Update:

1. Release Notes lesen: https://github.com/docling-project/docling-serve/releases
2. Prüfen, ob sich Modelle geändert haben — Modelle können andere Lizenzen haben als
   die Software. `THIRD_PARTY_LICENSES.md` entsprechend neu prüfen.
3. Datenbank sichern (siehe oben).
4. Neue Version in `docker-compose.yml` eintragen und testen:

```bash
docker compose pull docling
docker compose up -d docling
docker compose logs -f docling            # bis „healthy"
python3 tests/e2e.py                      # kompletter Testlauf
```

Bei Problemen zurück auf die alte Version:

```bash
# alten Tag in docker-compose.yml eintragen
docker compose up -d docling
```

Anwendungsupdate:

```bash
docker compose build web
docker compose up -d web worker
python3 tests/e2e.py
```

## Rollback der Anwendung

Das Image ist mit `klartext-app:1.0.0` versioniert. Vor einer größeren Änderung das
laufende Image festhalten:

```bash
docker tag klartext-app:1.0.0 klartext-app:vor-update
# im Fehlerfall:
docker tag klartext-app:vor-update klartext-app:1.0.0
docker compose up -d web worker
```

## Datenlöschung

- Quelldateien: zehn Minuten nach Abschluss der Verarbeitung
- Ergebnisse und Auftrag: nach `RETENTION_HOURS` (Vorgabe 24 Stunden)
- Sitzungen: nach Ablauf, spätestens beim nächsten Aufräumlauf
- Rate-Limit-Zähler: nach zwei Tagen
- Verbrauchszähler: nach 30 Tagen
- Audit-Protokoll: nach 90 Tagen

Der Aufräumlauf im Worker läuft alle fünf Minuten.

## Cloudflare cacht statische Dateien

Cloudflare cacht `/static/*` standardmäßig **vier Stunden** (`cf-cache-status: HIT`,
`cache-control: max-age=14400`). Ohne Gegenmaßnahme bekämen Besucher nach einem
Update stundenlang das alte JavaScript — mit neuem HTML kombiniert ergibt das
schwer auffindbare Fehler.

Deshalb tragen alle statischen Verweise eine Inhalts-Kennung:

```html
<link rel="stylesheet" href="/static/app.css?v=ab0ee22261">
```

Die Kennung ist die ersten zehn Stellen des SHA-256 über den Dateiinhalt und wird
beim ersten Zugriff berechnet (`web_helpers.asset`). Ändert sich die Datei, ändert
sich die URL — der Cache greift dann nicht mehr, unveränderte Dateien bleiben aber
weiterhin gecacht. Ein manuelles Leeren des Caches ist nicht nötig.

Falls doch einmal ein Purge gebraucht wird: der Token `Cloudflare_API` aus dem Vault
hat dafür **keine** Berechtigung (`Authentication error`, Code 10000). Dann entweder
im Cloudflare-Dashboard purgen oder einen Token mit `Cache Purge` anlegen.

## Fehlersuche

| Symptom | Prüfung |
|---|---|
| Nach einem Update ist die alte Oberfläche zu sehen | Sollte nicht mehr vorkommen: CSS und JS werden mit Inhalts-Kennung ausgeliefert (`app.css?v=…`). Falls doch, im Browser hart neu laden und prüfen, ob die Kennung sich geändert hat. |
| Seite antwortet mit 403 | Cloudflare blockt Nicht-Browser-User-Agents. Mit echtem Browser-User-Agent testen oder direkt `http://127.0.0.1:8160` verwenden. |
| Aufträge bleiben in der Warteschlange | `docker compose logs worker`; steht dort „Docling nicht erreichbar", dann `docker compose ps docling` und `docker compose restart docling`. |
| „Permission denied" beim Upload | Rechte auf `data/uploads` und `data/results` prüfen — sie müssen UID 1000 gehören. |
| Anmeldung schlägt trotz richtigem Passwort fehl | Sitzungscookies haben `Secure`. Über `http://` ohne TLS funktioniert die Anmeldung nicht — immer über HTTPS testen. |
| Nach mehreren Fehlversuchen kommt 429 | Brute-Force-Schutz. 15 Minuten warten oder `DELETE FROM rate_limits WHERE bucket LIKE 'login-acct:%'`. |
| Konvertierung bricht mit Zeitüberschreitung ab | `DOCLING_DOC_TIMEOUT` erhöhen oder Seitenlimit senken. Große gescannte PDFs sind CPU-gebunden. |
| Datenbank nicht erreichbar | `docker compose ps db`, `docker compose logs db`. Der Web-Container wartet beim Start bis zu 60 Sekunden auf die Datenbank. |

## Was auf diesem Server bewusst nicht angefasst wurde

- kein bestehender Container gestoppt, entfernt oder umkonfiguriert
- kein bestehendes Volume oder Netz angefasst
- kein `docker system prune`
- nginx unverändert (läuft weiter mit nur der Default-Site)
- kein vorhandenes Redis und keine vorhandene Datenbank mitbenutzt
- keine bestehende Ingress-Regel und kein bestehender DNS-Eintrag verändert
- keine Firewallregel geändert, kein Neustart des Servers
