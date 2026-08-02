#!/usr/bin/env python3
"""Misst die Umwandlungsqualität gegen den Gold-Korpus.

Aufruf:
    python3 bench/messen.py                      # digitale Fassungen
    python3 bench/messen.py --variante scan      # eingescannte Fassungen
    python3 bench/messen.py --variante beide
    python3 bench/messen.py --nur 02 --basis http://127.0.0.1:8160

Die Dateien laufen durch den **laufenden Dienst**, nicht an ihm vorbei: gemessen
wird, was Nutzer bekommen — Docling plus Nachbearbeitung plus Layouttreue.

Kennzahlen, alle von 0 bis 1, größer ist besser:

* `text`                — Anteil des Quelltextes, der im Ergebnis wiederkehrt
* `ueberschriften`      — F1 über Ebene und Text, Ebenen relativ gerechnet
* `listen`              — F1 über Listenpunkte samt Verschachtelungstiefe
* `tabellen_struktur`   — F1 über das Zellraster mit Zeilen- und Spaltenverbünden
* `tabellen_inhalt`     — dasselbe, zusätzlich mit übereinstimmendem Zelltext
* `reihenfolge`         — Kendalls Tau der Absatzreihenfolge (Lesereihenfolge)

Jeder Lauf hängt eine Zeile an `bench/verlauf.jsonl` und schreibt
`bench/BERICHT.md` neu. Damit ist jede Änderung am Dienst als Zahl sichtbar,
statt als Eindruck.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys
import time

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent / "tests"))

import struktur  # noqa: E402

DOKUMENTE = HIER / "dokumente"
GOLD = HIER / "gold"
VERLAUF = HIER / "verlauf.jsonl"
BERICHT = HIER / "BERICHT.md"

KENNZAHLEN = ("text", "ueberschriften", "listen", "tabellen_struktur",
              "tabellen_inhalt", "reihenfolge")
TITEL = {"text": "Text", "ueberschriften": "Überschr.", "listen": "Listen",
         "tabellen_struktur": "Tab-Struktur", "tabellen_inhalt": "Tab-Inhalt",
         "reihenfolge": "Reihenfolge"}


def _e2e(basis: str):
    """Der Testclient aus tests/e2e.py — dort steckt schon alles, was es
    braucht: Cookies, CSRF, Multipart, ein glaubwürdiger User-Agent."""
    import e2e
    e2e.BASE = basis.rstrip("/")
    return e2e


# Eigenes Konto für den Messstand. Es teilt sich die Fair-Use-Grenzen mit
# niemandem: ein Messlauf sind zwei Dutzend Aufträge, die sonst das Tageslimit
# eines mitbenutzten Kontos aufbrauchen und den nächsten Lauf verhindern.
BENCH_KONTO = "klartext-bench@example.invalid"


def _konto(e2e) -> str:
    """Gibt das Messkonto zurück und legt es an, falls es noch nicht existiert."""
    vorhanden = e2e.psql(
        f"SELECT email_norm FROM users WHERE email_norm = '{BENCH_KONTO}'")
    if vorhanden:
        return BENCH_KONTO

    print(f"Messkonto {BENCH_KONTO} wird angelegt.")
    e2e.register(e2e.Client(), BENCH_KONTO)
    if not e2e.psql(f"SELECT email_norm FROM users WHERE email_norm = '{BENCH_KONTO}'"):
        print("Konto konnte nicht angelegt werden (Registrierbremse?).")
        raise SystemExit(2)
    return BENCH_KONTO


def _hochladen(e2e, client, dateien: list[pathlib.Path], csrf: str) -> tuple[list[str], list[str]]:
    """Lädt in Paketen hoch und wartet, bis alles fertig ist.

    Gibt die angenommenen Dateinamen zurück und die Gründe, warum etwas nicht
    durchkam. Ein Lauf mit Ablehnungen ist unvollständig und darf nicht als
    Messreihe gelten — sonst steht im Verlauf ein Mittelwert über die halbe
    Stichprobe neben einem über die ganze."""
    angenommen: list[str] = []
    probleme: list[str] = []
    for start in range(0, len(dateien), 5):
        paket = dateien[start:start + 5]
        teile = [("files", p.name, p.read_bytes(), "application/pdf") for p in paket]
        status, _, rumpf = client.post_multipart("/app/upload", {"csrf": csrf}, teile)
        text = rumpf.decode(errors="replace")
        if status != 200:
            hinweis = f"Upload abgelehnt (HTTP {status}): {text[:160]}"
            print(f"  {hinweis}")
            probleme.append(hinweis)
            continue
        antwort = json.loads(text)
        abgelehnt = {a.get("name") for a in antwort.get("abgelehnt", [])}
        angenommen += [p.name for p in paket if p.name not in abgelehnt]
        for a in antwort.get("abgelehnt", []):
            hinweis = f"{a.get('name')}: {a.get('grund') or a.get('reason')}"
            print(f"  Abgelehnt — {hinweis}")
            probleme.append(hinweis)
        _warten(client)
    return angenommen, probleme


def _warten(client, frist: int = 900) -> list[dict]:
    ende = time.time() + frist
    while time.time() < ende:
        status, _, rumpf = client.get("/api/jobs", headers={"Accept": "application/json"})
        if status != 200:
            time.sleep(4)
            continue
        auftraege = json.loads(rumpf)["jobs"]
        if not [j for j in auftraege if j["status"] in ("queued", "processing")]:
            return auftraege
        time.sleep(5)
    return []


def _markdown_holen(client, auftrag_id: str) -> str | None:
    status, _, rumpf = client.get(f"/app/job/{auftrag_id}/download/md")
    if status != 200:
        return None
    return rumpf.decode("utf-8", "replace")


def _zeile(werte: dict) -> str:
    def z(name):
        wert = werte.get(name)
        return "—" if wert is None else f"{wert:.3f}"
    return " | ".join(z(k) for k in KENNZAHLEN)


def _mittel(saetze: list[dict], name: str) -> float | None:
    werte = [s["werte"][name] for s in saetze if s["werte"].get(name) is not None]
    return round(sum(werte) / len(werte), 4) if werte else None


def bericht_schreiben(laeufe: dict[str, list[dict]], kopf: dict) -> None:
    zeilen = ["# Messbericht", "",
              f"Erhoben am {kopf['zeitpunkt']} · Stand `{kopf['commit']}` · "
              f"Dienst {kopf['basis']}", "",
              "Alle Werte von 0 bis 1, größer ist besser. `—` heißt: im Dokument "
              "kommt diese Eigenschaft nicht vor.", ""]

    for variante, saetze in laeufe.items():
        if not saetze:
            continue
        zeilen += [f"## {variante}", "",
                   "| Dokument | " + " | ".join(TITEL[k] for k in KENNZAHLEN) + " |",
                   "|---|" + "---|" * len(KENNZAHLEN)]
        for satz in sorted(saetze, key=lambda s: s["dokument"]):
            zeilen.append(f"| {satz['dokument']} | {_zeile(satz['werte'])} |")
        mittel = {k: _mittel(saetze, k) for k in KENNZAHLEN}
        zeilen.append("| **Mittel** | " + _zeile(mittel) + " |")
        zeilen.append("")

    zeilen += ["## Wie das gemessen wird", "",
               "Die Prüfdokumente in `bench/quellen/` sind selbst geschrieben; die "
               "Wahrheit wird aus ihnen berechnet (`bench/bauen.py`), nicht von Hand "
               "gepflegt. Gemessen wird das Markdown, das der laufende Dienst "
               "ausliefert — also die Datei, die Nutzer herunterladen.", "",
               "Abschnitte, die der Dienst selbst anfügt (Verweisliste, wiederkehrende "
               "Seitenelemente), bleiben außen vor: sie stehen nicht in der Vorlage und "
               "sollen die Messung weder heben noch senken.", ""]
    BERICHT.write_text("\n".join(zeilen), encoding="utf-8")


def main() -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument("--basis", default="https://klartext.it-handwerk-stuttgart.de")
    zerleger.add_argument("--variante", default="digital",
                          choices=["digital", "scan", "beide"])
    zerleger.add_argument("--nur", default="", help="nur Dokumente, deren Name das enthält")
    zerleger.add_argument("--ohne-verlauf", action="store_true",
                          help="Ergebnis nicht in verlauf.jsonl aufnehmen")
    argumente = zerleger.parse_args()

    e2e = _e2e(argumente.basis)
    konto = _konto(e2e)
    client = e2e.Client()
    e2e.login(client, konto)
    csrf = client.csrf("/app")
    if not csrf:
        print("Anmeldung fehlgeschlagen — kein CSRF-Feld erhalten.")
        return 2

    varianten = (["digital", "scan"] if argumente.variante == "beide"
                 else [argumente.variante])
    laeufe: dict[str, list[dict]] = {}
    unvollstaendig: list[str] = []

    for variante in varianten:
        muster = "*-scan.pdf" if variante == "scan" else "*.pdf"
        dateien = sorted(p for p in DOKUMENTE.glob(muster)
                         if argumente.nur in p.name
                         and (variante == "scan") == p.stem.endswith("-scan"))
        if not dateien:
            print(f"Keine Dokumente für Variante {variante} — erst bench/bauen.py laufen lassen.")
            continue

        print(f"\n{variante}: {len(dateien)} Dokumente")
        angenommen, probleme = _hochladen(e2e, client, dateien, csrf)
        unvollstaendig.extend(f"{variante}: {p}" for p in probleme)
        auftraege = _warten(client)
        # Die Liste kommt neueste zuerst. Bei einem wiederholten Lauf liegt
        # derselbe Dateiname mehrfach vor — gemessen wird der frische Auftrag.
        nach_name: dict[str, dict] = {}
        for auftrag in auftraege:
            nach_name.setdefault(auftrag["name"], auftrag)

        saetze = []
        for datei in dateien:
            if datei.name not in angenommen:
                continue
            auftrag = nach_name.get(datei.name)
            if auftrag is None or auftrag["status"] != "done":
                print(f"  {datei.stem}: kein Ergebnis ({auftrag and auftrag['status']})")
                unvollstaendig.append(f"{variante}: {datei.stem} ohne Ergebnis")
                continue
            markdown = _markdown_holen(client, auftrag["id"])
            if markdown is None:
                print(f"  {datei.stem}: Markdown nicht abrufbar")
                unvollstaendig.append(f"{variante}: {datei.stem} nicht abrufbar")
                continue
            name = datei.stem[:-5] if datei.stem.endswith("-scan") else datei.stem
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
            "commit": commit, "basis": argumente.basis}
    bericht_schreiben(laeufe, kopf)

    if unvollstaendig:
        print("\nLauf unvollständig — nicht in den Verlauf aufgenommen:")
        for eintrag in unvollstaendig:
            print(f"  - {eintrag}")
    elif not argumente.ohne_verlauf:
        eintrag = {**kopf, "mittel": {v: {k: _mittel(s, k) for k in KENNZAHLEN}
                                      for v, s in laeufe.items() if s},
                   "dokumente": {v: {s["dokument"]: s["werte"] for s in saetze}
                                 for v, saetze in laeufe.items() if saetze}}
        with VERLAUF.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(eintrag, ensure_ascii=False) + "\n")

    print(f"\nBericht: {BERICHT}")
    for variante, saetze in laeufe.items():
        if saetze:
            mittel = {k: _mittel(saetze, k) for k in KENNZAHLEN}
            print(f"Mittel {variante}: {_zeile(mittel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
