#!/usr/bin/env python3
"""Korpus-Lauf: einen Ordner voller Dokumente durch den Dienst jagen.

Aufruf:  python3 tests/korpus.py ORDNER [BASIS-URL]

Warum es das gibt: Die e2e-Suite prüft Abläufe mit wenigen bekannten Dateien.
Dieser Lauf prüft die Lesequalität in der Breite — echte PDFs, Office-Dateien,
Fotos und bewusste Grenzfälle. Er meldet Konvertierungsfehler und bekannte
Artefaktmuster im Ergebnis, damit Regressionen auffallen, bevor Nutzer sie
finden.

Nutzt das juengste Demo-Konto (klartext-demo-…) statt einer Neuregistrierung —
die Registrier-Ratenbremse bleibt unangetastet. Legt den Bericht als
korpus-bericht.md neben den Ordner.
"""

from __future__ import annotations

import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from e2e import Client, login, psql  # noqa: E402

MIME = {
    ".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".tif": "image/tiff", ".tiff": "image/tiff",
    ".webp": "image/webp", ".bmp": "image/bmp", ".html": "text/html",
    ".md": "text/markdown",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

# Artefaktmuster im Markdown-Ergebnis. Jedes ist ein bekannter Fehlertyp.
PRUEFUNGEN = [
    ("html-entitaet", re.compile(r"&(?:amp|lt|gt|quot|#\d+);")),
    ("seitenzahl-inline", re.compile(r"\b(?:SEITE|Seite|PAGE|Page)\s+\d+\s+(?:VON|von|OF|of)\s+\d+\b")),
    ("base64-blob", re.compile(r"[A-Za-z0-9+/]{400,}")),
    ("ersatzzeichen", re.compile("�")),
    ("bild-platzhalter", re.compile(r"<!--\s*image\s*-->")),
    ("null-byte", re.compile("\x00")),
]
DOPPEL_LEER = re.compile(r"(?<=\S)[ ]{2,}(?=\S)")


def doppelleer_ausserhalb_tabellen(text: str) -> int:
    return sum(
        1 for z in text.split("\n")
        if "|" not in z and not z.startswith(("    ", "\t")) and DOPPEL_LEER.search(z)
    )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    ordner = pathlib.Path(sys.argv[1])
    dateien = sorted(p for p in ordner.iterdir() if p.suffix.lower() in MIME)
    if not dateien:
        print("Keine unterstuetzten Dateien in", ordner)
        return 2

    konto = psql("SELECT email_norm FROM users WHERE email_norm LIKE 'klartext-demo-%' "
                 "ORDER BY created_at DESC LIMIT 1")
    if not konto:
        print("Kein Demo-Konto gefunden (klartext-demo-…). Erst eines anlegen.")
        return 2
    print(f"Konto: {konto} | Dateien: {len(dateien)}")

    c = Client()
    login(c, konto)
    csrf = c.csrf("/app")

    # Hochladen in Fuenferpaketen (Upload-Grenze des Dienstes).
    abgelehnt: list[tuple[str, str]] = []
    hochgeladen: list[str] = []
    for i in range(0, len(dateien), 5):
        paket = dateien[i:i + 5]
        teile = [("files", p.name, p.read_bytes(), MIME[p.suffix.lower()]) for p in paket]
        status, _, body = c.post_multipart("/app/upload", {"csrf": csrf}, teile)
        text = body.decode(errors="replace")
        if status != 200:
            for p in paket:
                abgelehnt.append((p.name, f"HTTP {status}: {text[:100]}"))
            continue
        import json as _json
        antwort = _json.loads(text)
        for a in antwort.get("abgelehnt", []):
            abgelehnt.append((a.get("name", "?"), a.get("grund", a.get("reason", "?"))))
        namen = {p.name for p in paket} - {a for a, _ in abgelehnt}
        hochgeladen.extend(sorted(namen))
        print(f"  Paket {i // 5 + 1}: {len(namen)} angenommen, "
              f"{len(paket) - len(namen)} abgelehnt")

    # Warten, bis nichts mehr in Arbeit ist.
    print("Warte auf Verarbeitung …")
    frist = time.time() + 60 * 45
    import json as _json
    jobs: list[dict] = []
    while time.time() < frist:
        status, _, body = c.get("/api/jobs", headers={"Accept": "application/json"})
        if status == 200:
            jobs = _json.loads(body)["jobs"]
            offen = [j for j in jobs if j["status"] in ("queued", "processing")]
            if not offen:
                break
            print(f"  … {len(offen)} offen")
        time.sleep(10)

    je_name = {j["name"]: j for j in jobs}

    # Ergebnisse einsammeln und pruefen.
    zeilen_fehler: list[str] = []
    zeilen_auffaellig: list[str] = []
    zeilen_sauber: list[str] = []
    for name in hochgeladen:
        j = je_name.get(name)
        if j is None:
            zeilen_fehler.append(f"| {name} | — | nicht in der Auftragsliste |")
            continue
        if j["status"] != "done":
            grund = (j.get("error") or j.get("fehler") or j["status"])
            zeilen_fehler.append(f"| {name} | {j['status']} | {str(grund)[:90]} |")
            continue
        st, _, md = c.get(f"/app/job/{j['id']}/download/md")
        if st != 200:
            zeilen_fehler.append(f"| {name} | done | Download HTTP {st} |")
            continue
        text = md.decode(errors="replace")
        befunde = [k for k, muster in PRUEFUNGEN if muster.search(text)]
        n_doppel = doppelleer_ausserhalb_tabellen(text)
        if n_doppel:
            befunde.append(f"doppel-leer×{n_doppel}")
        if len(text) < 40:
            befunde.append("fast-leer")
        eintrag = f"| {name} | {len(text)} B | {', '.join(befunde) or '—'} |"
        (zeilen_auffaellig if befunde else zeilen_sauber).append(eintrag)

    bericht = ordner.parent / "korpus-bericht.md"
    with open(bericht, "w", encoding="utf-8") as f:
        f.write(f"# Korpus-Bericht — {len(dateien)} Dateien\n\n")
        f.write(f"Angenommen: {len(hochgeladen)} · Abgelehnt: {len(abgelehnt)} · "
                f"Fehlgeschlagen: {len(zeilen_fehler)} · "
                f"Auffällig: {len(zeilen_auffaellig)} · Sauber: {len(zeilen_sauber)}\n\n")
        if abgelehnt:
            f.write("## Beim Upload abgelehnt (gewollt bei Grenzfaellen)\n\n")
            f.write("| Datei | Grund |\n|---|---|\n")
            for name, grund in abgelehnt:
                f.write(f"| {name} | {grund} |\n")
            f.write("\n")
        for titel, zeilen in [("Fehlgeschlagen", zeilen_fehler),
                              ("Auffällig", zeilen_auffaellig),
                              ("Sauber", zeilen_sauber)]:
            f.write(f"## {titel}\n\n")
            if zeilen:
                f.write("| Datei | Größe/Status | Befund |\n|---|---|---|\n")
                f.write("\n".join(zeilen) + "\n\n")
            else:
                f.write("—\n\n")
    print(f"\nBericht: {bericht}")
    print(f"Fehlgeschlagen: {len(zeilen_fehler)} | Auffällig: {len(zeilen_auffaellig)} "
          f"| Sauber: {len(zeilen_sauber)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
