#!/usr/bin/env python3
"""Baut aus den Quelldokumenten die Prüfdateien und die Wahrheit dazu.

Aufruf:  python3 bench/bauen.py [--nur 02] [--dpi 200]

Aus jeder Datei in `quellen/` entsteht:

* `dokumente/<name>.pdf`        — die digitale Fassung mit Textebene
* `dokumente/<name>-scan.pdf`   — dieselben Seiten als Bild, ohne Textebene:
                                  so kommt ein eingescanntes Dokument an
* `gold/<name>.json`            — die Wahrheit, direkt aus der Quelle abgeleitet

Der entscheidende Punkt: Die Wahrheit wird **nicht von Hand gepflegt**, sondern
aus dem Quelldokument berechnet. Ein neues Prüfdokument kostet damit nur die
Zeit, es zu schreiben — und die Messung kann nicht heimlich veralten.

Voraussetzungen: chromium (rendert HTML nach PDF), pdftoppm aus poppler-utils
(rastert die Seiten), Pillow (setzt die Bilder wieder zu einer PDF zusammen).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import struktur  # noqa: E402

HIER = pathlib.Path(__file__).resolve().parent
QUELLEN = HIER / "quellen"
DOKUMENTE = HIER / "dokumente"
GOLD = HIER / "gold"


def _chromium() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        pfad = shutil.which(name)
        if pfad:
            return pfad
    print("Kein chromium gefunden — ohne Browser lässt sich kein PDF rendern.")
    raise SystemExit(2)


def pdf_bauen(quelle: pathlib.Path, ziel: pathlib.Path) -> None:
    """HTML nach PDF. Chromium schreibt nur in Verzeichnisse, die es sehen darf —
    deshalb wird im Quellordner gerendert und danach verschoben."""
    zwischen = quelle.with_suffix(".pdf")
    subprocess.run(
        [_chromium(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={zwischen.name}", quelle.name],
        cwd=quelle.parent, capture_output=True, text=True, timeout=120,
    )
    if not zwischen.exists():
        raise RuntimeError(f"chromium hat kein PDF erzeugt: {quelle.name}")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(zwischen), ziel)


def scan_bauen(pdf: pathlib.Path, ziel: pathlib.Path, dpi: int = 200) -> None:
    """Aus der digitalen PDF eine Bild-PDF ohne Textebene machen.

    Genau das kommt aus einem Kopierer: Seiten als Bild, jedes Zeichen muss
    von der Texterkennung gelesen werden. Ohne diese Fassung misst der
    Messstand nur den einfachen Fall.
    """
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-jpeg", "-jpegopt", "quality=88",
                        str(pdf), f"{tmp}/seite"], check=True, timeout=300)
        seiten = sorted(pathlib.Path(tmp).glob("seite*.jpg"))
        if not seiten:
            raise RuntimeError(f"pdftoppm hat keine Seiten erzeugt: {pdf.name}")
        bilder = [Image.open(p).convert("RGB") for p in seiten]
        bilder[0].save(ziel, save_all=True, append_images=bilder[1:],
                       resolution=float(dpi))


def gold_bauen(quelle: pathlib.Path, ziel: pathlib.Path) -> dict:
    daten = struktur.aus_html(quelle.read_text(encoding="utf-8"))
    daten["name"] = quelle.stem
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    return daten


def main() -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument("--nur", default="", help="nur Quellen, deren Name das enthält")
    zerleger.add_argument("--dpi", type=int, default=200, help="Auflösung der Scanfassung")
    zerleger.add_argument("--ohne-scan", action="store_true", help="nur digitale Fassung")
    argumente = zerleger.parse_args()

    quellen = sorted(p for p in QUELLEN.glob("*.html") if argumente.nur in p.name)
    if not quellen:
        print("Keine passenden Quellen in", QUELLEN)
        return 2

    DOKUMENTE.mkdir(exist_ok=True)
    GOLD.mkdir(exist_ok=True)

    for quelle in quellen:
        pdf = DOKUMENTE / f"{quelle.stem}.pdf"
        pdf_bauen(quelle, pdf)
        daten = gold_bauen(quelle, GOLD / f"{quelle.stem}.json")
        zusatz = ""
        if not argumente.ohne_scan:
            scan_bauen(pdf, DOKUMENTE / f"{quelle.stem}-scan.pdf", argumente.dpi)
            zusatz = f" + Scan {argumente.dpi} dpi"
        print(f"{quelle.stem}: {len(daten['ueberschriften'])} Überschriften, "
              f"{len(daten['tabellen'])} Tabellen, {len(daten['listen'])} Listenpunkte, "
              f"{len(daten['volltext'])} Zeichen{zusatz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
