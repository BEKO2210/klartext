# Sicherheit

## Grundhaltung

Klartext ist öffentlich registrierbar und verarbeitet potenziell hochsensible
Dokumente. Zwei Annahmen liegen dem Entwurf zugrunde:

1. Jeder Benutzer ist ein möglicher Angreifer gegen alle anderen Benutzer.
2. Dokumentinhalte verlassen den Server nicht — auch nicht in Protokolle.

## Authentifizierung

**Passwörter** werden mit **Argon2id** gehasht (`time_cost=3`, `memory_cost=64 MiB`,
`parallelism=2`, 32 Byte Hash, 16 Byte Salt). Es gibt keine Stelle im Code, an der
ein Passwort im Klartext gespeichert, protokolliert oder per E-Mail versendet wird.
Beim Anmelden wird bei Bedarf automatisch neu gehasht (`check_needs_rehash`), sodass
sich die Parameter später verschärfen lassen, ohne Konten zu verlieren.

Gegen **Benutzer-Enumeration**: Existiert ein Konto nicht, wird trotzdem gegen einen
Dummy-Hash geprüft, damit die Antwortzeit gleich bleibt. Registrierung, Anmeldung und
„Passwort vergessen" antworten für vorhandene und nicht vorhandene Adressen identisch.

**Mindestlänge 10 Zeichen**, keine erzwungene Zeichenklassenmischung — Länge schützt
besser als Sonderzeichenzwang und führt zu weniger notierten Passwörtern.

## Sitzungen

- Zufallstoken (32 Byte, `secrets.token_urlsafe`), in der Datenbank nur als
  SHA-256-Hash. Ein Datenbankleck ermöglicht keine Sitzungsübernahme.
- Cookie `klartext_session`: **HttpOnly, Secure, SameSite=Lax, Path=/**, Ablauf 72 h.
- **Kein JWT, nichts im `localStorage`** — JavaScript kommt an das Token nicht heran.
- Jede Anmeldung erzeugt ein neues Token → **kein Session Fixation**.
- Abmelden löscht die Sitzung serverseitig, nicht nur das Cookie.
- Passwortwechsel und Passwort-Reset beenden **alle** Sitzungen des Kontos.
- Deaktiviert ein Admin ein Konto, werden dessen Sitzungen sofort entfernt; zusätzlich
  prüft jeder Sitzungsaufruf `is_active`.

## Autorisierung und Benutzerisolation

Jede Ressource ist über `user_id` an ihren Eigentümer gebunden. Es gibt **keine**
Abfrage, die eine Ressource allein über eine ID lädt: `_owned_job()` filtert immer
zusätzlich nach `user_id`, und die Datei-Abfragen im Download filtern erneut nach
`user_id` und Rolle.

Fremde Aufträge liefern **404, nicht 403** — es wird nicht einmal bestätigt, dass eine
ID existiert. Das gilt auch für den Admin-Bereich gegenüber normalen Konten.

Job-Kennungen sind **UUIDv4**, also nicht erratbar oder hochzählbar. Selbst mit
richtig geratener UUID greift die Eigentümerprüfung.

Der ZIP-Sammel-Download durchläuft für jede angeforderte Kennung dieselbe
Eigentümerprüfung; fremde Kennungen werden übersprungen, nicht beigelegt.

## Dateien

- **Inhaltstyp statt Dateiendung:** Jeder Upload wird mit `libmagic` gesnifft. Endung
  und tatsächlicher Typ müssen zusammenpassen; eine PNG-Datei namens `rechnung.pdf`
  wird abgelehnt. Bei PDF wird zusätzlich der `%PDF-`-Kopf geprüft.
- **Zufällige interne Namen:** `<2 Hex>/<32 Hex>`, ohne Endung, Rechte 0600. Der vom
  Benutzer gelieferte Name landet **nie** in einem Pfad, sondern nur in einer
  Datenbankspalte.
- **Path Traversal** ist doppelt abgesichert: der Storage-Key muss einem strengen
  regulären Ausdruck genügen, und der aufgelöste Pfad muss unterhalb des
  Speicherverzeichnisses liegen (`is_relative_to`). Ein Upload namens
  `../../../../etc/passwd.png` erzeugt lediglich einen Auftrag mit diesem Anzeigenamen.
- **Ablage außerhalb des Webroots:** Es gibt keine statische Auslieferung von
  `data/`. Downloads laufen ausschließlich über authentifizierte Endpunkte.
- **Content-Disposition:** Der Downloadname wird neu gebaut — Steuerzeichen,
  Anführungszeichen, Zeilenumbrüche und Pfadtrenner werden ersetzt. Damit ist keine
  Header-Injektion möglich.
- **ZIP-Slip:** Alle Namen im Archiv erzeugen wir selbst, Dubletten werden
  durchnummeriert. Es gibt keine Pfadtrenner und keine relativen Pfade im Archiv.

## SSRF

Der URL-Import ist für den ersten öffentlichen Release **abgeschaltet**: Docling Serve
läuft mit `DOCLING_SERVE_ALLOWED_SOURCE_TYPES=["file"]`, und die Anwendung bietet
keinen Weg, eine URL zu übergeben. Damit lässt sich der Dienst weder als Proxy
missbrauchen noch dazu bringen, interne Netzwerkziele abzurufen.

Zusätzlich ist `DOCLING_SERVE_ENABLE_REMOTE_SERVICES=false` gesetzt, sodass auch die
Pipeline selbst keine ausgehenden Verbindungen aufbaut.

## Injektion

- **SQL:** ausschließlich parametrisierte Abfragen über asyncpg. Es gibt keine
  Zeichenkettenverkettung mit Benutzereingaben in SQL.
- **Command Injection:** die Anwendung startet keine Unterprozesse. Der Docling-Aufruf
  ist ein HTTP-Aufruf, kein Shell-Aufruf.
- **XSS:** Jinja2 mit aktivem Autoescape. Die Markdown-Vorschau wird bewusst **als
  Text in einem `<pre>`** ausgegeben, nicht als HTML gerendert — konvertierter
  Dokumentinhalt kann also kein Markup einschleusen. Das JavaScript setzt
  ausschließlich `textContent`, nie `innerHTML` mit Serverdaten.

## CSRF

Alle zustandsändernden Aktionen sind POST mit Token. Angemeldete Formulare tragen das
Token der Sitzung, anonyme Formulare ein Doppel-Cookie-Token. Der Vergleich läuft
zeitkonstant (`hmac.compare_digest`). Zusätzlich verhindert `SameSite=Lax` die meisten
fremden Einreichungen bereits im Browser, und `form-action 'self'` in der CSP
unterbindet das Absenden an fremde Ziele.

## Security-Header

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self';
  img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self';
  frame-ancestors 'none'; base-uri 'none'; object-src 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: same-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

Die CSP kommt **ohne `unsafe-inline`** aus. Das ist der Grund, weshalb es im Frontend
keine Inline-Skripte und keine Event-Attribute gibt. `Referrer-Policy: same-origin`
verhindert, dass Bestätigungs- oder Reset-Token über den Referrer nach außen gelangen.

Die Header werden mit `setdefault` gesetzt und überschreiben nichts, was Cloudflare
bereits gesetzt hat — die bestehende Infrastruktur bleibt unberührt.

## Missbrauchsschutz

| Schutz | Umsetzung |
|---|---|
| Anfragen je IP | 240 pro Minute (Zähler in der Datenbank) |
| Anmeldeversuche je Konto | 10 pro 15 Minuten, Zähler wird bei Erfolg zurückgesetzt |
| Anmeldeversuche je IP | dreifaches Kontolimit pro 15 Minuten |
| Registrierungen je IP | 5 pro Stunde |
| Passwort-Reset je IP | 5 pro Stunde |
| Request-Body | serverseitig auf Dateigröße × Dateianzahl + 2 MB begrenzt |
| Gleichzeitige Uploads | höchstens zwei parallel im Web-Container |
| Gleichzeitige Jobs je Konto | im Worker durchgesetzt, nicht nur angezeigt |
| Warteschlange je Konto | begrenzt, global zusätzlich gedeckelt |
| Verbrauchszählung | **beim Einstellen**, nicht bei Erfolg |

Der letzte Punkt war ein echter Befund aus dem Review: Wäre der Verbrauch erst bei
erfolgreicher Konvertierung gebucht worden, hätte man das Tageskontingent durch
absichtlich fehlschlagende Aufträge beliebig umgehen können. Die tatsächliche
Seitenzahl wird nach der Konvertierung nur noch als Differenz nachgetragen.

## Dateien ohne Datenbankeintrag

Alle Löschwege gehen über die Datenbank: Ablauf der Frist, Auftrag löschen, Konto
löschen. Fällt zwischen dem Schreiben einer Datei und dem Anlegen ihres Eintrags
etwas aus, kennt niemand die Datei mehr — sie läge für immer auf der Platte und das
Löschversprechen wäre gebrochen.

Der Worker vergleicht deshalb alle fünf Minuten die Dateien auf der Platte mit den
Einträgen in `files` und `job_images` und entfernt, was zu keinem Eintrag gehört und
älter als eine Stunde ist. Die Altersgrenze verhindert, dass eine gerade
entstehende Datei erwischt wird.

## Netzwerk

Nur `klartext-web` hat ein Port-Mapping — und zwar auf `127.0.0.1:8160`, also nicht
einmal im LAN erreichbar. Von außen kommt man ausschließlich über den
Cloudflare-Tunnel heran.

**Ohne** Host-Port und damit von außen unerreichbar: PostgreSQL, Docling Serve.
Docling verlangt zusätzlich einen `X-Api-Key`, der nur serverseitig existiert und nie
an den Browser ausgeliefert wird. Die Gradio-Demo-UI und die OpenAPI-Oberfläche von
Docling sind abgeschaltet; die FastAPI-Dokumentation der eigenen Anwendung ebenfalls
(`docs_url=None`, `redoc_url=None`, `openapi_url=None`).

## Fehlerausgabe

Benutzer bekommen ausschließlich vorformulierte deutsche Sätze aus einer festen
Meldungstabelle. Es gelangen keine Stacktraces, Dateipfade, Containernamen,
Datenbankdetails oder API-Schlüssel nach außen. Details landen im Container-Protokoll.

## Protokollierung und Datenschutz

Es werden **keine Dokumentinhalte, keine OCR-Ergebnisse und keine Dateinamen**
protokolliert. Der Worker meldet nur Fehlerart, Dauer und Seitenzahl. Die Übersicht
fehlgeschlagener Aufträge im Admin-Bereich zeigt Fehlercode, Zeitpunkt und
Konto-Nummer — keinen Dateinamen.

Es ist kein externer Fehlerprotokoll-Dienst angebunden und kein Analytics-Werkzeug
eingebunden. Die vorhandene Plausible-Instanz auf diesem Server ist bewusst **nicht**
eingebunden.

## Durchgeführter Review

Vor der Freigabe wurde der Code gegen die üblichen Klassen durchgesehen. Die drei
Befunde mit tatsächlicher Auswirkung wurden behoben:

| Befund | Auswirkung | Behebung |
|---|---|---|
| Verbrauch wurde erst bei Erfolg gebucht | Tageskontingent durch absichtlich fehlschlagende Aufträge umgehbar | Buchung beim Einstellen, Differenz danach |
| `max_active_jobs` wurde angezeigt, aber nirgends durchgesetzt | ein Konto konnte alle Worker belegen | Durchsetzung in der Job-Reservierung des Workers |
| Uploads wurden unbegrenzt parallel in den Speicher gelesen | mehrere große Uploads gleichzeitig konnten den Web-Container an sein Speicherlimit treiben | höchstens zwei gleichzeitige Uploads |

Geprüft und ohne Befund: IDOR und Broken Access Control, CSRF, XSS, SSRF, Path
Traversal, unrestricted Upload, ZIP-Slip, Command Injection, SQL-Injektion, Session
Fixation, Brute Force, Secrets Exposure, öffentlich erreichbare interne Ports.

## Bekannte Grenzen

Ehrlich benannt, damit sie nicht mit „geprüft und sicher" verwechselt werden:

- **Aussperren durch Dritte:** Wer die E-Mail-Adresse eines Kontos kennt, kann durch
  wiederholte Fehlversuche dessen Anmeldung 15 Minuten lang blockieren. Das ist der
  Preis eines kontobezogenen Brute-Force-Schutzes ohne CAPTCHA. Ein Passwort-Reset
  bleibt in dieser Zeit möglich.
- **IP-Ermittlung:** Die Anwendung vertraut `CF-Connecting-IP` beziehungsweise
  `X-Forwarded-For`. Das ist korrekt, solange sie ausschließlich über den Tunnel
  erreichbar ist — was durch die Bindung an `127.0.0.1` sichergestellt ist. Wer
  bereits Zugriff auf den Host hat, könnte die Zähler umgehen; wer Zugriff auf den
  Host hat, hat allerdings ohnehin größere Möglichkeiten.
- **Rate-Limit-Fenster:** feste Zeitfenster, kein gleitendes Fenster. An der
  Fenstergrenze ist kurzzeitig die doppelte Rate möglich. Für den Zweck
  (Serverschutz, nicht Abrechnung) ausreichend.
- **Keine Zwei-Faktor-Authentisierung.** Für einen kostenlosen Konvertierungsdienst
  mit 24-Stunden-Aufbewahrung bewusst nicht umgesetzt.
- **Verschlüsselung im Ruhezustand:** Dateien liegen unverschlüsselt auf der Platte
  des Servers, geschützt durch Dateirechte. Wer Zugriff auf den Host hat, kann sie
  lesen. Die kurze Aufbewahrungszeit begrenzt das Zeitfenster.

## Meldung von Sicherheitsproblemen

Sicherheitsprobleme bitte direkt an den Betreiber melden (Kontakt im Impressum),
nicht öffentlich.
