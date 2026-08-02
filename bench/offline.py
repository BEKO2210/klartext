#!/usr/bin/env python3
"""Misst die Nachbearbeitung ohne den Dienst — Sekunden statt Minuten.

Aufruf:
    python3 bench/offline.py --rohdaten     # Docling einmal fragen, Ergebnis sichern
    python3 bench/offline.py                # messen, so oft man will
    python3 bench/offline.py --variante beide --eintragen

Warum das nötig ist: Ein Lauf über den Dienst kostet zwei Dutzend Aufträge,
mehrere Minuten und Fair-Use-Kontingent. Beim Entwickeln an einer Regel will
man nach jeder Änderung messen, nicht nach jeder Kaffeepause.

Der Trick: Docling ist bei gleicher Datei und gleichen Parametern
gleichbleibend. Sein Rohergebnis (Markdown und Struktur) wird einmal gesichert;
danach läuft nur noch die Nachbearbeitung — und genau die wird hier entwickelt.
Gerechnet wird **im Container**, mit demselben Code, den der Worker fährt.

Wichtig: Ändert sich etwas an den Docling-Parametern, sind die Rohdaten
veraltet — dann `--rohdaten` neu laufen lassen. Vor einer Freigabe zählt
ohnehin nur der vollständige Lauf über den Dienst (`bench/messen.py`).
"""

from __future__ import annotations

import argparse
import base64
import datetime
import json
import pathlib
import subprocess
import sys

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import struktur  # noqa: E402
from messen import (BERICHT, KENNZAHLEN, VERLAUF, _mittel, _zeile,  # noqa: E402
                    bericht_schreiben)

DOKUMENTE = HIER / "dokumente"
GOLD = HIER / "gold"
ROHDATEN = HIER / "rohdaten"

# Gerechnet wird in einem Wegwerfcontainer aus dem gebauten Abbild, mit dem
# Quellstand aus dem Arbeitsverzeichnis darübergelegt. Damit läuft der Code, an
# dem gerade gearbeitet wird — ohne die laufenden Container anzufassen.
#
# Bewusst ohne jedes Datenverzeichnis: ein Probecontainer, der die echten
# Datenordner sieht, hat hier schon einmal Nutzerdateien gelöscht.
ABBILD = "klartext-app:1.3.0"
NETZ = "klartext-internal"
QUELLSTAND = HIER.parent / "app" / "klartext"


def _lauf(skript: str, eingabe: str, mit_netz: bool, frist: int) -> subprocess.CompletedProcess:
    befehl = ["docker", "run", "--rm", "-i",
              "-v", f"{QUELLSTAND}:/app/klartext:ro",
              "-e", "PYTHONDONTWRITEBYTECODE=1"]
    if mit_netz:
        umgebung = _docling_umgebung()
        befehl += ["--network", NETZ]
        for name, wert in umgebung.items():
            befehl += ["-e", f"{name}={wert}"]
    befehl += [ABBILD, "python", "-c", skript]
    return subprocess.run(befehl, input=eingabe, capture_output=True, text=True,
                          timeout=frist)


def _docling_umgebung() -> dict[str, str]:
    """Holt Adresse und Schlüssel der Konvertierungs-Engine aus der .env.

    Der Schlüssel wird an den Wegwerfcontainer weitergereicht und sonst
    nirgends hingeschrieben.
    """
    werte = {"DOCLING_URL": "http://docling:5001"}
    datei = HIER.parent / ".env"
    if datei.exists():
        for zeile in datei.read_text(encoding="utf-8").splitlines():
            if zeile.startswith("DOCLING_API_KEY="):
                werte["DOCLING_API_KEY"] = zeile.split("=", 1)[1].strip()
    return werte


_ROHDATEN_SKRIPT = """
import asyncio, base64, json, sys
sys.path.insert(0, '/app')
from klartext.docling_client import DoclingClient

dateien = json.loads(sys.stdin.read())

async def go():
    client = DoclingClient()
    for name, inhalt in dateien.items():
        daten = base64.b64decode(inhalt)
        ergebnis = await client.convert(name, daten, 'application/pdf', 100)
        print('@@' + json.dumps({'name': name, 'markdown': ergebnis['markdown'],
                                 'json': ergebnis['json']}, ensure_ascii=False))
    await client.aclose()

asyncio.run(go())
"""

_MESS_SKRIPT = """
import base64, json, sys
sys.path.insert(0, '/app')
from klartext import nachbearbeitung

for zeile in sys.stdin:
    zeile = zeile.strip()
    if not zeile:
        continue
    satz = json.loads(zeile)
    # Die Quelldatei muss mit: Verweise, wiederkehrende Seitenelemente und die
    # Auflösungspruefung lesen die PDF selbst. Ohne sie wuerde offline etwas
    # anderes gemessen als der Dienst ausliefert.
    quelle = base64.b64decode(satz['quelle']) if satz.get('quelle') else None
    fertig = nachbearbeitung.anwenden(satz['markdown'], satz['json'], quelle,
                                      'application/pdf', 'de')
    print('@@' + json.dumps({'name': satz['name'], 'markdown': fertig.markdown},
                            ensure_ascii=False))
"""


def rohdaten_holen(muster: str) -> None:
    """Schickt jede Prüfdatei einmal durch Docling und sichert das Rohergebnis."""
    dateien = sorted(p for p in DOKUMENTE.glob("*.pdf") if muster in p.name)
    if not dateien:
        print("Keine Dokumente — erst bench/bauen.py laufen lassen.")
        raise SystemExit(2)

    ROHDATEN.mkdir(exist_ok=True)
    # In Paketen, damit ein Fehler nicht die ganze Sammlung kostet.
    for start in range(0, len(dateien), 3):
        paket = dateien[start:start + 3]
        eingabe = json.dumps({p.name: base64.b64encode(p.read_bytes()).decode()
                              for p in paket})
        lauf = _lauf(_ROHDATEN_SKRIPT, eingabe, mit_netz=True, frist=1800)
        if lauf.returncode != 0:
            print(lauf.stderr.strip()[-2000:])
            raise SystemExit("Docling-Aufruf fehlgeschlagen.")
        for zeile in lauf.stdout.splitlines():
            if not zeile.startswith("@@"):
                continue
            satz = json.loads(zeile[2:])
            ziel = ROHDATEN / f"{pathlib.Path(satz['name']).stem}.json"
            ziel.write_text(json.dumps(satz, ensure_ascii=False), encoding="utf-8")
            print(f"  gesichert: {ziel.name} ({len(satz['markdown'])} Zeichen Markdown)")


def nachbearbeiten(saetze: list[dict]) -> dict[str, str]:
    """Lässt die Nachbearbeitung im Container über die Rohdaten laufen."""
    angereichert = []
    for satz in saetze:
        pdf = DOKUMENTE / satz["name"]
        angereichert.append({**satz, "quelle": base64.b64encode(pdf.read_bytes()).decode()
                             if pdf.exists() else None})
    eingabe = "\n".join(json.dumps(s, ensure_ascii=False) for s in angereichert)
    lauf = _lauf(_MESS_SKRIPT, eingabe, mit_netz=False, frist=900)
    if lauf.returncode != 0:
        print(lauf.stderr.strip()[-2000:])
        raise SystemExit("Nachbearbeitung im Container fehlgeschlagen.")
    ergebnis = {}
    for zeile in lauf.stdout.splitlines():
        if zeile.startswith("@@"):
            satz = json.loads(zeile[2:])
            ergebnis[satz["name"]] = satz["markdown"]
    return ergebnis


def main() -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument("--rohdaten", action="store_true",
                          help="Docling einmal fragen und die Rohergebnisse sichern")
    zerleger.add_argument("--variante", default="beide",
                          choices=["digital", "scan", "beide"])
    zerleger.add_argument("--nur", default="")
    zerleger.add_argument("--eintragen", action="store_true",
                          help="Ergebnis in verlauf.jsonl aufnehmen (sonst nur anzeigen)")
    argumente = zerleger.parse_args()

    if argumente.rohdaten:
        rohdaten_holen(argumente.nur)
        return 0

    if not ROHDATEN.is_dir() or not any(ROHDATEN.glob("*.json")):
        print("Keine Rohdaten — erst `python3 bench/offline.py --rohdaten` laufen lassen.")
        return 2

    varianten = (["digital", "scan"] if argumente.variante == "beide"
                 else [argumente.variante])
    laeufe: dict[str, list[dict]] = {}

    for variante in varianten:
        quellen = sorted(p for p in ROHDATEN.glob("*.json")
                         if argumente.nur in p.name
                         and (variante == "scan") == p.stem.endswith("-scan"))
        if not quellen:
            print(f"Keine Rohdaten für Variante {variante}.")
            continue

        saetze_roh = [json.loads(p.read_text(encoding="utf-8")) for p in quellen]
        markdowns = nachbearbeiten(saetze_roh)

        saetze = []
        print(f"\n{variante}: {len(quellen)} Dokumente")
        for roh in saetze_roh:
            markdown = markdowns.get(roh["name"])
            if markdown is None:
                print(f"  {roh['name']}: kein Ergebnis")
                continue
            stamm = pathlib.Path(roh["name"]).stem
            name = stamm[:-5] if stamm.endswith("-scan") else stamm
            soll = json.loads((GOLD / f"{name}.json").read_text(encoding="utf-8"))
            werte = struktur.vergleiche(soll, struktur.aus_markdown(markdown))
            saetze.append({"dokument": name, "werte": werte})
            print(f"  {name}: {_zeile(werte)}")
        laeufe[variante] = saetze

    if not any(laeufe.values()):
        print("Nichts gemessen.")
        return 1

    commit = subprocess.run(["git", "-C", str(HIER.parent), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unbekannt"
    kopf = {"zeitpunkt": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "commit": commit, "basis": "offline (gesicherte Docling-Rohdaten)"}

    print()
    for variante, saetze in laeufe.items():
        if saetze:
            print(f"Mittel {variante}: "
                  f"{_zeile({k: _mittel(saetze, k) for k in KENNZAHLEN})}")

    if argumente.eintragen:
        bericht_schreiben(laeufe, kopf)
        eintrag = {**kopf, "mittel": {v: {k: _mittel(s, k) for k in KENNZAHLEN}
                                      for v, s in laeufe.items() if s},
                   "dokumente": {v: {s["dokument"]: s["werte"] for s in saetze}
                                 for v, saetze in laeufe.items() if saetze}}
        with VERLAUF.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        print(f"Bericht: {BERICHT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
