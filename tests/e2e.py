#!/usr/bin/env python3
"""Klartext — End-to-End-Test gegen eine laufende Instanz.

Aufruf:  python3 tests/e2e.py [BASIS-URL]
Vorgabe: https://klartext.it-handwerk-stuttgart.de

Der Test legt eigene Konten mit Zufallsadressen an und raeumt sie am Ende
wieder ab. Es werden ausschliesslich die Testdateien aus tests/fixtures
verwendet.
"""

from __future__ import annotations

import io
import json
import pathlib
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.cookiejar import CookieJar

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://klartext.it-handwerk-stuttgart.de").rstrip("/")
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
PASSWORD = "Testpasswort-2026!x"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""), flush=True)
    return ok


class Client:
    """Minimaler Browser: Cookies, Formulare, Multipart."""

    def __init__(self) -> None:
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar), NoRedirect()
        )

    # Cloudflare weist unbekannte Clients ab; ein echter Browser-User-Agent ist
    # nötig, damit der Test überhaupt bis zur Anwendung durchkommt.
    UA = ("Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36")

    def request(self, method, path, data=None, headers=None, follow=False):
        url = path if path.startswith("http") else BASE + path
        merged = {"User-Agent": self.UA,
                  "Accept-Language": "de-DE,de;q=0.9",
                  "Accept": "text/html,application/xhtml+xml"}
        merged.update(headers or {})
        req = urllib.request.Request(url, data=data, method=method, headers=merged)
        try:
            resp = self.opener.open(req, timeout=120)
        except urllib.error.HTTPError as exc:
            resp = exc
        body = resp.read()
        if follow and resp.status in (301, 302, 303, 307, 308):
            return self.request("GET", resp.headers["Location"], follow=True)
        return resp.status, resp.headers, body

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post_form(self, path, fields, **kw):
        body = urllib.parse.urlencode(fields).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        headers.update(kw.pop("headers", {}))
        return self.request("POST", path, data=body, headers=headers, **kw)

    def post_multipart(self, path, fields, files, **kw):
        boundary = "----klartext" + secrets.token_hex(12)
        buf = io.BytesIO()

        def w(text):
            buf.write(text.encode("utf-8") if isinstance(text, str) else text)

        for key, value in fields.items():
            w(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n")
        for key, filename, content, ctype in files:
            w(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; "
              f"filename=\"{filename}\"\r\nContent-Type: {ctype}\r\n\r\n")
            w(content)
            w("\r\n")
        w(f"--{boundary}--\r\n")
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}",
                   "Accept": "application/json"}
        headers.update(kw.pop("headers", {}))
        return self.request("POST", path, data=buf.getvalue(), headers=headers, **kw)

    def csrf(self, path="/anmelden"):
        _, _, body = self.get(path)
        match = re.search(rb'name="csrf" value="([^"]+)"', body)
        return match.group(1).decode() if match else ""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def psql(sql: str) -> str:
    """Direkter Datenbankzugriff fuer Testvorbereitung (E-Mail-Bestaetigung)."""
    out = subprocess.run(
        ["docker", "exec", "klartext-db", "psql", "-U", "klartext", "-d", "klartext",
         "-tAc", sql],
        capture_output=True, text=True, timeout=30,
    )
    return out.stdout.strip()


def register(client: Client, email: str, verify_directly=True) -> None:
    csrf = client.csrf("/registrieren")
    client.post_form("/registrieren", {
        "csrf": csrf, "email": email, "password": PASSWORD,
        "password2": PASSWORD, "accept": "ja",
    })
    if verify_directly:
        psql(f"UPDATE users SET email_verified = TRUE WHERE email_norm = '{email.lower()}'")


def login(client: Client, email: str, password: str = PASSWORD):
    csrf = client.csrf("/anmelden")
    return client.post_form("/anmelden", {"csrf": csrf, "email": email, "password": password})


def wait_for_jobs(client: Client, expected: int, timeout: int = 420):
    deadline = time.time() + timeout
    jobs: list[dict] = []
    while time.time() < deadline:
        status, _, body = client.get("/api/jobs", headers={"Accept": "application/json"})
        if status != 200:
            time.sleep(3)
            continue
        jobs = json.loads(body)["jobs"]
        pending = [j for j in jobs if j["status"] in ("queued", "processing")]
        if len(jobs) >= expected and not pending:
            return jobs
        time.sleep(4)
    return jobs


def upload(client: Client, names: list[str], csrf: str, override=None):
    files = []
    for name in names:
        path = FIXTURES / name
        ctype = {
            ".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
            ".tiff": "image/tiff", ".webp": "image/webp",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }.get(path.suffix, "application/octet-stream")
        files.append(("files", override or name, path.read_bytes(), ctype))
    return client.post_multipart("/app/upload", {"csrf": csrf}, files)


def main() -> int:
    suffix = secrets.token_hex(4)
    mail_a = f"klartext-test-a-{suffix}@example.invalid"
    mail_b = f"klartext-test-b-{suffix}@example.invalid"

    print(f"Basis-URL: {BASE}\n")

    # 1 Registrierung ------------------------------------------------------
    a = Client()
    csrf = a.csrf("/registrieren")
    status, _, body = a.post_form("/registrieren", {
        "csrf": csrf, "email": mail_a, "password": PASSWORD,
        "password2": PASSWORD, "accept": "ja"})
    check("01 Registrierung", status in (200, 303), f"HTTP {status}")

    exists = psql(f"SELECT COUNT(*) FROM users WHERE email_norm = '{mail_a.lower()}'")
    check("01b Konto in der Datenbank", exists == "1", f"count={exists}")

    hashed = psql(f"SELECT password_hash FROM users WHERE email_norm = '{mail_a.lower()}'")
    check("01c Passwort als Argon2id gespeichert",
          hashed.startswith("$argon2id$") and PASSWORD not in hashed,
          hashed[:22])

    # 2 Anmeldung vor Bestaetigung soll scheitern --------------------------
    status, _, _ = login(a, mail_a)
    check("02 Anmeldung ohne E-Mail-Bestaetigung abgelehnt", status == 403, f"HTTP {status}")

    psql(f"UPDATE users SET email_verified = TRUE WHERE email_norm = '{mail_a.lower()}'")

    # 3 Falsches Passwort --------------------------------------------------
    wrong = Client()
    status, _, _ = login(wrong, mail_a, "voellig-falsches-passwort")
    check("03 Falsches Passwort abgelehnt", status == 401, f"HTTP {status}")

    # 4 Anmeldung ----------------------------------------------------------
    status, headers, _ = login(a, mail_a)
    cookie = headers.get("set-cookie", "")
    check("04 Anmeldung", status == 303, f"HTTP {status}")
    low = cookie.lower()
    check("04b Sitzungscookie HttpOnly + Secure + SameSite",
          "httponly" in low and "secure" in low and "samesite=lax" in low,
          cookie.split(";", 1)[-1].strip()[:60])

    # 5 Geschuetzte Seite ohne Anmeldung -----------------------------------
    anon = Client()
    status, headers, _ = anon.get("/app")
    check("05 Dashboard ohne Anmeldung leitet zur Anmeldung",
          status == 303 and headers.get("Location") == "/anmelden", f"HTTP {status}")
    status, _, _ = anon.get("/api/jobs", headers={"Accept": "application/json"})
    check("05b Job-Schnittstelle ohne Anmeldung gesperrt", status == 401, f"HTTP {status}")

    # 6 Sicherheits-Header --------------------------------------------------
    _, headers, _ = anon.get("/")
    csp = headers.get("Content-Security-Policy", "")
    check("06 Security-Header vollstaendig",
          all([
              "default-src 'self'" in csp,
              "frame-ancestors 'none'" in csp,
              "'unsafe-inline'" not in csp,
              headers.get("X-Content-Type-Options") == "nosniff",
              headers.get("Referrer-Policy") == "same-origin",
              "Strict-Transport-Security" in headers,
              headers.get("X-Frame-Options") == "DENY",
              "Permissions-Policy" in headers,
          ]),
          "CSP ohne unsafe-inline, HSTS, nosniff, DENY")

    # 7 CSRF ----------------------------------------------------------------
    status, _, _ = a.post_form("/app/upload", {"csrf": "gefaelscht"})
    check("07 CSRF-Schutz greift", status == 400, f"HTTP {status}")

    dash_csrf = a.csrf("/app")

    # 8-13 Konvertierungen --------------------------------------------------
    status, _, body = upload(a, ["test-text.png"], dash_csrf)
    check("08 PNG mit Text angenommen", status == 200, f"HTTP {status}")

    status, _, _ = upload(a, ["test-text.jpg"], dash_csrf)
    check("09 JPEG mit Text angenommen", status == 200, f"HTTP {status}")

    status, _, _ = upload(a, ["test-table.png"], dash_csrf)
    check("10 Bild mit Tabelle angenommen", status == 200, f"HTTP {status}")

    status, _, _ = upload(a, ["test-multipage.pdf"], dash_csrf)
    check("11 Mehrseitige PDF angenommen", status == 200, f"HTTP {status}")

    status, _, _ = upload(a, ["test.docx", "test.xlsx"], dash_csrf)
    check("12 DOCX + XLSX gleichzeitig angenommen (Mehrfach-Upload)",
          status == 200, f"HTTP {status}")

    print("\n  ... warte auf die Verarbeitung ...\n", flush=True)
    jobs = wait_for_jobs(a, 6)
    done = {j["name"]: j for j in jobs if j["status"] == "done"}
    check("13 Alle sechs Auftraege fertig",
          len(done) == 6, f"fertig={len(done)}/{len(jobs)} " +
          ", ".join(f"{j['name']}:{j['status']}" for j in jobs))

    # 14 Inhaltstreue -------------------------------------------------------
    def markdown_of(name):
        job = done.get(name)
        if not job:
            return ""
        status, _, body = a.get(f"/app/auftrag/{job['id']}/download/md")
        return body.decode("utf-8") if status == 200 else ""

    png_md = markdown_of("test-text.png")
    check("14 OCR erkennt Text im PNG",
          "4711" in png_md and ("1.849,50" in png_md or "1.849" in png_md),
          f"{len(png_md)} Zeichen")
    check("14b Umlaute und Sonderzeichen erhalten",
          any(t in png_md for t in ("Bäckerei", "Böblingen", "Özdemir", "Grün")),
          "Umlaute im OCR-Ergebnis")

    table_md = markdown_of("test-table.png")
    check("15 Tabelle im Bild vollstaendig als Markdown-Tabelle",
          all(t in table_md for t in ("Artikelnummer", "A-1001", "A-1002", "B-2010",
                                      "C-3300", "Wärmemengenzähler", "189,00")),
          f"{len(table_md)} Zeichen")

    pdf_md = markdown_of("test-multipage.pdf")
    check("16 PDF-Inhalt vollstaendig",
          all(t in pdf_md for t in ("Prüfbericht", "Öztürk", "64,2", "wirkungsgrad")),
          f"{len(pdf_md)} Zeichen")
    check("16b PDF-Tabelle erhalten", "Messpunkt" in pdf_md and "|" in pdf_md)
    pdf_job = done.get("test-multipage.pdf")
    check("16c Seitenzahl erkannt", bool(pdf_job) and pdf_job["pages"] == 3,
          f"Seiten={pdf_job['pages'] if pdf_job else 'kein Ergebnis'}")
    if not pdf_job:
        print("\nAbbruch: ohne fertige PDF sind die folgenden Prüfungen sinnlos.")
        failed = [name for name, ok, _ in results if not ok]
        print(f"{len(results) - len(failed)} von {len(results)} bestanden")
        return 1

    docx_md = markdown_of("test.docx")
    check("17 DOCX-Inhalt inkl. Tabelle",
          "Rechnung 2026-0815" in docx_md and "899,00" in docx_md and "|" in docx_md,
          f"{len(docx_md)} Zeichen")

    xlsx_md = markdown_of("test.xlsx")
    check("18 XLSX-Inhalt inkl. zweitem Blatt",
          "13890.75" in xlsx_md.replace(",", ".") or "13890" in xlsx_md,
          f"{len(xlsx_md)} Zeichen")

    check("19 Keine Zusammenfassung oder Umformulierung",
          len(pdf_md) > 600 and "Zusammenfassung" not in pdf_md,
          "Rohtext, keine erfundenen Abschnitte")

    # 20 JSON ---------------------------------------------------------------
    job = pdf_job
    status, headers, body = a.get(f"/app/auftrag/{job['id']}/download/json")
    payload = json.loads(body) if status == 200 else {}
    check("20 JSON-Download mit Docling-Struktur",
          status == 200 and payload.get("schema_name") == "DoclingDocument"
          and len(payload.get("pages", {})) == 3,
          f"HTTP {status}, Seiten={len(payload.get('pages', {}))}")
    # Der Zeitpunkt der Umwandlung steckt im Namen, damit zwei Umwandlungen
    # derselben Vorlage im Download-Ordner nicht als "-2" landen.
    verfuegung = headers.get("Content-Disposition", "")
    check("20b Dateiname im Download korrekt",
          re.search(r'filename="test-multipage_\d{4}-\d{2}-\d{2}_\d{4}\.json"', verfuegung)
          is not None, verfuegung)

    # 21 ZIP ----------------------------------------------------------------
    ids = ",".join(j["id"] for j in done.values())
    status, headers, body = a.get(f"/app/download/zip?ids={ids}")
    names: list[str] = []
    if status == 200:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = archive.namelist()
    # Bei mehreren Auftraegen bekommt jeder einen eigenen Ordner: nur so stimmen
    # die Bildverweise im Markdown nach dem Entpacken.
    check("21 ZIP-Download mit .md und .json je Auftrag",
          status == 200 and len(names) == 12
          and all(n.count("/") == 1 for n in names)
          and not any(n.startswith(("/", "..")) or ".." in n for n in names),
          f"{len(names)} Eintraege")

    # 22 Ungewoehnliche Dateinamen -----------------------------------------
    tricky = "Rechnung Müller & Söhne – 50 % Rabatt (Kopie).png"
    status, _, _ = upload(a, ["test-text.png"], dash_csrf, override=tricky)
    check("22 Unicode-Dateiname akzeptiert", status == 200, f"HTTP {status}")

    status, _, _ = upload(a, ["test-text.png"], dash_csrf,
                          override="../../../../etc/passwd.png")
    check("23 Path-Traversal-Dateiname akzeptiert, aber entschaerft",
          status == 200, f"HTTP {status}")

    # 24 Falscher MIME-Typ --------------------------------------------------
    status, _, body = a.post_multipart(
        "/app/upload", {"csrf": dash_csrf},
        [("files", "getarnt.pdf", (FIXTURES / "test-text.png").read_bytes(),
          "application/pdf")])
    check("24 PNG-Inhalt mit .pdf-Endung abgelehnt", status == 400, f"HTTP {status}")

    status, _, _ = a.post_multipart(
        "/app/upload", {"csrf": dash_csrf},
        [("files", "schadcode.exe", b"MZ\x90\x00" + b"A" * 500,
          "application/octet-stream")])
    check("24b Nicht unterstuetztes Format abgelehnt", status == 400, f"HTTP {status}")

    # 25 Groessenlimit ------------------------------------------------------
    big = b"%PDF-1.4\n" + secrets.token_bytes(26 * 1024 * 1024)
    status, _, _ = a.post_multipart(
        "/app/upload", {"csrf": dash_csrf},
        [("files", "riesig.pdf", big, "application/pdf")])
    check("25 Datei ueber dem Groessenlimit abgelehnt", status == 413, f"HTTP {status}")

    # 26 Seitenlimit --------------------------------------------------------
    # Bewusst ueber eine zu lange PDF statt ueber eine abgesenkte Grenze:
    # app_settings ist global und auf der oeffentlichen Startseite sichtbar —
    # ein Test darf Besuchern keine falschen Werte zeigen.
    status, _, _ = upload(a, ["test-101-seiten.pdf"], dash_csrf)
    check("26 PDF ueber dem Seitenlimit abgelehnt", status == 400, f"HTTP {status}")

    # 27 Benutzerisolation --------------------------------------------------
    b = Client()
    register(b, mail_b)
    login(b, mail_b)
    victim = pdf_job["id"]

    status, _, _ = b.get(f"/app/auftrag/{victim}")
    check("27 Benutzer B sieht Auftrag von A nicht", status == 404, f"HTTP {status}")

    status, _, _ = b.get(f"/app/auftrag/{victim}/download/md")
    check("28 Benutzer B kann Ergebnis von A nicht laden", status == 404, f"HTTP {status}")

    status, _, body = b.get(f"/app/download/zip?ids={victim}")
    check("28b Benutzer B kann Auftrag von A nicht als ZIP ziehen",
          status == 404, f"HTTP {status}")

    status, _, body = b.get("/api/jobs", headers={"Accept": "application/json"})
    b_jobs = json.loads(body)["jobs"] if status == 200 else []
    check("28c Auftragsliste von B ist leer", b_jobs == [], f"{len(b_jobs)} Eintraege")

    csrf_b = b.csrf("/app")
    status, _, _ = b.post_form(f"/app/auftrag/{victim}/loeschen", {"csrf": csrf_b})
    check("28d Benutzer B kann Auftrag von A nicht loeschen", status == 404, f"HTTP {status}")

    still_there = psql(f"SELECT status FROM jobs WHERE public_id = '{victim}'")
    check("28e Auftrag von A unveraendert vorhanden", still_there == "done", still_there)

    # 29 Admin-Bereich ------------------------------------------------------
    status, _, _ = b.get("/admin")
    check("29 Admin-Bereich fuer normale Konten nicht sichtbar", status == 404, f"HTTP {status}")

    status, _, _ = b.post_form("/admin/limits", {"csrf": csrf_b, "max_pages": "99999"})
    check("29b Admin-Aktion fuer normale Konten gesperrt", status == 404, f"HTTP {status}")

    # 30 Abmelden -----------------------------------------------------------
    csrf_b = b.csrf("/app")
    status, _, _ = b.post_form("/abmelden", {"csrf": csrf_b})
    check("30 Abmelden", status == 303, f"HTTP {status}")
    status, _, _ = b.get("/api/jobs", headers={"Accept": "application/json"})
    check("30b Sitzung nach Abmelden ungueltig", status == 401, f"HTTP {status}")

    # 31 Passwort aendern beendet alle Sitzungen ----------------------------
    c = Client()
    login(c, mail_a)
    csrf_c = c.csrf("/konto")
    new_password = PASSWORD + "-neu"
    status, _, _ = c.post_form("/konto/passwort", {
        "csrf": csrf_c, "current": PASSWORD,
        "password": new_password, "password2": new_password})
    check("31 Passwort geaendert", status == 303, f"HTTP {status}")
    status, _, _ = a.get("/api/jobs", headers={"Accept": "application/json"})
    check("31b Alte Sitzung nach Passwortwechsel ungueltig", status == 401, f"HTTP {status}")

    # 32 Brute-Force --------------------------------------------------------
    blocked = False
    for _ in range(14):
        attacker = Client()
        status, _, _ = login(attacker, mail_a, "falsch-falsch-falsch")
        if status == 429:
            blocked = True
            break
    check("32 Brute-Force-Schutz bei der Anmeldung", blocked, "429 nach mehreren Versuchen")

    # 33 Aufraeumen und Kontoloeschung --------------------------------------
    files_before = psql(f"SELECT COUNT(*) FROM files f JOIN users u ON u.id = f.user_id "
                        f"WHERE u.email_norm = '{mail_a.lower()}'")
    keys = psql(f"SELECT f.storage_key FROM files f JOIN users u ON u.id = f.user_id "
                f"WHERE u.email_norm = '{mail_a.lower()}' LIMIT 3").splitlines()

    csrf_c = c.csrf("/konto")
    status, _, _ = c.post_form("/konto/loeschen", {"csrf": csrf_c, "confirm": "LOESCHEN"})
    check("33 Konto geloescht", status == 303, f"HTTP {status}")

    left = psql(f"SELECT COUNT(*) FROM users WHERE email_norm = '{mail_a.lower()}'")
    check("33b Konto aus der Datenbank entfernt", left == "0", f"count={left}")
    files_after = psql(f"SELECT COUNT(*) FROM files f JOIN users u ON u.id = f.user_id "
                       f"WHERE u.email_norm = '{mail_a.lower()}'")
    check("33c Auftragsdaten kaskadierend geloescht",
          files_after == "0", f"vorher={files_before}, nachher={files_after}")

    on_disk = []
    for key in keys:
        if not key:
            continue
        found = subprocess.run(
            ["docker", "exec", "klartext-web", "sh", "-c",
             f"test -f /data/results/{key} -o -f /data/uploads/{key} && echo da || echo weg"],
            capture_output=True, text=True).stdout.strip()
        on_disk.append(found)
    check("33d Dateien auch von der Platte entfernt",
          all(v == "weg" for v in on_disk) and on_disk, f"{on_disk}")

    # 34 Aufraeumen Benutzer B ----------------------------------------------
    psql(f"DELETE FROM users WHERE email_norm = '{mail_b.lower()}'")

    # 35 Interne Dienste nicht oeffentlich ----------------------------------
    exposed = subprocess.run(
        ["bash", "-c",
         "ss -tlnp 2>/dev/null | grep -E ':(5432|5001|6379)\\s' | grep -v '127.0.0.1' | wc -l"],
        capture_output=True, text=True).stdout.strip()
    check("34 Datenbank und Docling-API nicht auf dem Host gebunden",
          exposed == "0", f"{exposed} offene Ports")

    for path in ("/v1/convert/file", "/docs", "/openapi.json", "/redoc", "/ui"):
        status, _, _ = anon.get(path)
        if not check(f"35 Kein Durchgriff auf {path}", status in (404, 405), f"HTTP {status}"):
            break

    # 37 Hinweis auf zu grobe Vorlagen ---------------------------------------
    # test-grob.jpg ist ein Foto mit 574 x 822 Bildpunkten; die Schrift darin
    # ist rund 11 Bildpunkte hoch und wird stellenweise falsch gelesen.
    # Eigenes Konto: das Konto aus den vorherigen Pruefungen hat die
    # Tagesgrenze fuer Konvertierungen weitgehend aufgebraucht.
    d = Client()
    mail_d = f"klartext-test-d-{suffix}@example.invalid"
    register(d, mail_d)
    login(d, mail_d)
    d_csrf = d.csrf("/app")

    def alle_jobs_d():
        _, _, roh = d.get("/api/jobs", headers={"Accept": "application/json"})
        try:
            return json.loads(roh)["jobs"]
        except (ValueError, KeyError):
            print(f"      /api/jobs lieferte: {roh[:120]!r}")
            return []

    status, _, _ = upload(d, ["test-grob.jpg", "test-text.png"], d_csrf)
    grob = None
    jobs_jetzt = []
    if status == 200:
        wait_for_jobs(d, 2)
        jobs_jetzt = alle_jobs_d()
        for eintrag in jobs_jetzt:
            if eintrag["name"] == "test-grob.jpg":
                grob = eintrag
                break
    check("37 Grobe Vorlage wird gemeldet",
          grob is not None and bool(grob.get("note")),
          f"HTTP {status}, " + ((grob or {}).get("note") or "kein Hinweis"))

    # Das sauber lesbare Testbild darf keinen Hinweis bekommen — sonst waere
    # die Meldung Rauschen und wuerde ignoriert.
    sauber = [j for j in jobs_jetzt if j["name"] == "test-text.png"]
    check("38 Sauberes Bild bleibt ohne Hinweis",
          bool(sauber) and not any(j.get("note") for j in sauber),
          f"{len(sauber)} Auftraege geprueft")

    if grob:
        status, _, body = d.get(f"/app/download/zip?ids={grob['id']}")
        namen = []
        if status == 200:
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                namen = archive.namelist()
        check("39 Hinweis liegt dem ZIP bei",
              any(n.endswith("hinweis.txt") for n in namen), ", ".join(namen[:4]))

    psql(f"DELETE FROM users WHERE email_norm = '{mail_d.lower()}'")

    # 40 Kein Versand an Adressen, die keine Post annehmen koennen ------------
    # Sonst erzeugt jede Testregistrierung einen Unzustellbarkeitsbericht im
    # Postfach des Betreibers — genau das ist frueher passiert.
    probe = subprocess.run(
        ["docker", "exec", "klartext-web", "python", "-c",
         "from klartext.mail import unzustellbar as u;"
         "print(all(u(a) for a in ['x@example.invalid','y@example.com','z@sub.example.org',"
         "'q@a.test','r@localhost']) and not any(u(a) for a in ['a@gmail.com',"
         "'b@it-handwerk-stuttgart.de','c@myexample.com']))"],
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    check("40 Kein Mailversand an nicht zustellbare Adressen",
          probe == "True", probe or "keine Antwort")

    # 41 Reichweitenmessung ueber die eigene Domain ---------------------------
    status, headers, body = anon.get("/js/script.js?v=1")
    check("41 Zaehlskript ueber die eigene Domain",
          status == 200 and len(body) > 500
          and "javascript" in headers.get("Content-Type", ""),
          f"HTTP {status}, {len(body)} Bytes")

    status, _, _ = anon.post_form("/api/event", {})
    check("41b Zaehlaufruf wird angenommen", status in (202, 400), f"HTTP {status}")

    # Im angemeldeten Bereich darf nicht gemessen werden: dort stehen
    # Auftragskennungen in der Adresse.
    def hat_zaehler(rohtext) -> bool:
        text = rohtext.decode("utf-8", "replace") if isinstance(rohtext, bytes) else rohtext
        return "data-domain=" in text

    _, _, oeffentlich = anon.get("/")
    _, _, angemeldet = a.get("/app")
    check("42 Keine Messung im angemeldeten Bereich",
          hat_zaehler(oeffentlich) and not hat_zaehler(angemeldet),
          f"oeffentlich={'ja' if hat_zaehler(oeffentlich) else 'nein'}, "
          f"angemeldet={'ja' if hat_zaehler(angemeldet) else 'nein'}")

    # 36 Bestehende Dienste -------------------------------------------------
    others = {
        "fokus": "https://fokus.it-handwerk-stuttgart.de/",
        "nox": "https://nox.it-handwerk-stuttgart.de/",
        "music": "https://music.it-handwerk-stuttgart.de/",
        "apex": "https://it-handwerk-stuttgart.de/",
        "southside-media": "https://southside-media.de/",
    }
    ok_all = True
    for label, url in others.items():
        try:
            # Cloudflare weist Anfragen ohne Browser-User-Agent ab (403) — das ist
            # der Bot-Schutz, kein Ausfall des Dienstes.
            req = urllib.request.Request(url, headers={"User-Agent": Client.UA})
            with urllib.request.urlopen(req, timeout=25) as resp:
                ok_all &= resp.status == 200
        except Exception as exc:  # noqa: BLE001
            ok_all = False
            print(f"      {label}: {exc}")
    check("36 Bestehende Dienste weiterhin erreichbar", ok_all, ", ".join(others))

    # Ergebnis --------------------------------------------------------------
    failed = [name for name, ok, _ in results if not ok]
    print(f"\n{'=' * 62}")
    print(f"{len(results) - len(failed)} von {len(results)} Pruefungen bestanden")
    if failed:
        print("Nicht bestanden:")
        for name in failed:
            print(f"  - {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
