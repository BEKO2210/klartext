# Lizenzen eingesetzter Fremdkomponenten

Stand der Prüfung: **29.07.2026**. Alle Angaben wurden an diesem Tag direkt aus den
tatsächlich verwendeten Repositories, Paket-Registries und Modell-Karten gelesen —
nicht aus Sekundärquellen übernommen.

Ergebnis: **Alle eingesetzten Komponenten erlauben kommerzielle Nutzung, Veränderung
und den öffentlichen Betrieb unter eigenem Namen und eigenem Branding.** Keine
Komponente verlangt die Übernahme fremder Marken oder Logos; keine Komponente
verbietet den Betrieb als Dienst.

---

## 1. Konvertierungs-Engine

| Projekt | Version | Lizenz | Repository | Attribution nötig | Kommerziell | Änderung |
|---|---|---|---|---|---|---|
| Docling | in docling-serve v1.28.0 enthalten | MIT | https://github.com/docling-project/docling | ja — Lizenztext + Copyright | ja | ja |
| Docling Serve | v1.28.0 (Image `quay.io/docling-project/docling-serve-cpu:v1.28.0`) | MIT | https://github.com/docling-project/docling-serve | ja — Lizenztext + Copyright | ja | ja |

Copyright-Vermerk beider Projekte, wörtlich aus der Datei `LICENSE`:

> Copyright (c) 2024 International Business Machines

**Auflagen der MIT-Lizenz:** Lizenztext und Copyright-Vermerk müssen bei Weitergabe
beigelegt werden. Diese Datei erfüllt das und ist im Dienst unter `/lizenzen`
öffentlich abrufbar.

**Was die MIT-Lizenz ausdrücklich *nicht* verlangt:** die Nennung von IBM oder Docling
im Produktnamen, im Logo oder in der Oberfläche. Die MIT-Lizenz gewährt keine
Markenrechte — deshalb werden hier weder das Docling- noch das IBM-Logo verwendet und
der Dienst tritt nirgends als offizielles IBM- oder Docling-Produkt auf. Das ist
zugleich Auflage und bewusste Entscheidung.

---

## 2. Modelle

Modelle können abweichende Lizenzen zur Software haben. Jedes im Image
enthaltene Modell wurde einzeln geprüft. Verwendet werden nur die unten mit
**„aktiv"** markierten.

| Modell | Zweck | Lizenz | Quelle | Status |
|---|---|---|---|---|
| `ds4sd/docling-layout-heron` | Layout-Analyse, Lesereihenfolge | Apache-2.0 | https://huggingface.co/ds4sd/docling-layout-heron | **aktiv** |
| `ds4sd/docling-models` (TableFormer) | Tabellenstruktur | CDLA-Permissive-2.0 und Apache-2.0 | https://huggingface.co/ds4sd/docling-models | **aktiv** |
| RapidOCR (Engine) | Texterkennung | Apache-2.0, Copyright (c) 2021 RapidOCR Authors | https://github.com/RapidAI/RapidOCR | **aktiv** |
| RapidOCR-Modelle (PP-OCRv6 det/rec, PP-OCRv4 cls, ONNX) | Texterkennung | Apache-2.0 (aus PaddleOCR, Copyright (c) 2016 PaddlePaddle Authors) | https://github.com/PaddlePaddle/PaddleOCR | **aktiv** |
| Tesseract OCR + `tessdata_fast` (eng, osd) | alternative Texterkennung | Apache-2.0 | https://github.com/tesseract-ocr/tesseract, https://github.com/tesseract-ocr/tessdata_fast | umschaltbar |
| `tessdata_fast` deu (Tag 4.1.0) | deutsche Texterkennung für Tesseract | Apache-2.0 | https://github.com/tesseract-ocr/tessdata_fast | umschaltbar |
| EasyOCR-Modelle | alternative Texterkennung | Code Apache-2.0; Detektor CRAFT MIT (NAVER Corp.); Erkenner aus deep-text-recognition-benchmark | im Image enthalten | **nicht aktiv** |
| `ds4sd/DocumentFigureClassifier-v2.5` | Bildklassifikation | MIT | https://huggingface.co/ds4sd/DocumentFigureClassifier | **nicht aktiv** |

**Warum RapidOCR und nicht EasyOCR (der Docling-Standard):**

Ausschlaggebend war die Erkennungsqualität. Gemessen am 29.07.2026 auf dieser
Installation über vier Testbilder (Fließtext niedrig aufgelöst, dasselbe als JPEG,
eine vierspaltige Preistabelle in zwei Auflösungen), geprüft wurde jede der 45
Pflichtangaben einzeln — Namen, Straßen, Postleitzahlen, Artikelnummern, Beträge,
Umlaute und das Gradzeichen:

| Engine | Treffer | Quote |
|---|---|---|
| **RapidOCR** | 44 / 45 | **98 %** |
| EasyOCR | 34 / 45 | 76 % |
| Tesseract (deu+eng) | 19 / 45 | 42 % |

EasyOCR verlor durchgängig Beträge (`8,40`, `189,00`) und das Gradzeichen — bei
Rechnungen und Preislisten also genau die Stellen, auf die es ankommt. Tesseract
scheiterte an Tabellen in Bildern fast vollständig. Einziger Fehltreffer von
RapidOCR war eine Telefonnummer mit Leerzeichen und Schrägstrich
(`07031 / 55 42 19`) im niedrig aufgelösten Bild.

Die Lizenzlage stützt dieselbe Wahl: RapidOCR ist durchgängig eindeutig — Engine
unter Apache-2.0 (RapidOCR Authors), Modelle aus PaddleOCR ebenfalls unter
Apache-2.0 (PaddlePaddle Authors), mitgeliefert als ONNX-Dateien im offiziellen
Docling-Image. Bei EasyOCR ist der Detektor sauber (CRAFT, MIT, NAVER Corp.), für
die von JaidedAI trainierten Erkennungsgewichte liegt jedoch keine eigenständige
Lizenzangabe bei den Gewichtsdateien vor.

Tesseract bleibt als Alternative im Image und ist über `OCR_ENGINE=tesseract`
umschaltbar; das deutsche Sprachpaket ist weiterhin eingehängt.

**CDLA-Permissive-2.0** (TableFormer) ist eine permissive Datenlizenz: kommerzielle
Nutzung und Veränderung erlaubt; bei Weitergabe der Daten selbst müssen Lizenztext und
Haftungsausschluss beiliegen. Der Dienst gibt die Modelldateien nicht weiter, sondern
nutzt sie nur serverseitig — die Auflage ist damit erfüllt und wird hier zusätzlich
dokumentiert.

---

## 3. Backend-Pakete (Python)

Alle Versionen sind in `app/requirements.txt` gepinnt.

| Paket | Version | Lizenz |
|---|---|---|
| fastapi | 0.140.13 | MIT |
| starlette | 1.3.1 | BSD-3-Clause |
| uvicorn | 0.51.0 | BSD-3-Clause |
| uvloop | 0.22.1 | MIT |
| httptools | 0.8.0 | MIT |
| websockets | 16.1.1 | BSD-3-Clause |
| watchfiles | 1.2.0 | MIT |
| pydantic | 2.13.4 | MIT |
| pydantic-core | 2.46.4 | MIT |
| annotated-types | 0.8.0 | MIT |
| annotated-doc | 0.0.5 | MIT |
| typing-extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.2 | MIT |
| jinja2 | 3.1.6 | BSD-3-Clause |
| MarkupSafe | 3.0.3 | BSD-3-Clause |
| asyncpg | 0.31.0 | Apache-2.0 |
| argon2-cffi | 25.1.0 | MIT |
| argon2-cffi-bindings | 25.1.0 | MIT |
| cffi | 2.1.0 | MIT-0 |
| pycparser | 3.0 | BSD-3-Clause |
| python-multipart | 0.0.32 | Apache-2.0 |
| httpx | 0.28.1 | BSD-3-Clause |
| httpcore | 1.0.9 | BSD-3-Clause |
| h11 | 0.16.0 | MIT |
| anyio | 4.14.2 | MIT |
| idna | 3.18 | BSD-3-Clause |
| certifi | 2026.7.22 | MPL-2.0 |
| python-magic | 0.4.27 | MIT |
| pypdf | 6.14.2 | BSD-3-Clause |
| aiosmtplib | 5.1.2 | MIT |
| itsdangerous | 2.2.0 | BSD-3-Clause |
| python-dotenv | 1.2.2 | BSD-3-Clause |
| PyYAML | 6.0.3 | MIT |
| click | 8.4.2 | BSD-3-Clause |

`certifi` steht unter MPL-2.0. MPL-2.0 ist dateibezogenes Copyleft: es wirkt nur auf
veränderte MPL-Dateien und greift nicht auf den eigenen Code über. `certifi` wird
unverändert eingesetzt.

Die Tabelle wurde maschinell gegen die PyPI-Metadaten der jeweils gepinnten Version
abgeglichen (`license_expression`, ersatzweise `license` bzw. die Trove-Klassifizierer).

`libmagic` (Systempaket, Debian `libmagic1`) steht unter der BSD-2-Clause-artigen
„file"-Lizenz von Ian F. Darwin und Christos Zoulas. Kommerzielle Nutzung erlaubt.

---

## 4. Infrastruktur-Images

| Image | Version | Lizenz |
|---|---|---|
| `postgres` | 16.11-alpine | PostgreSQL License (BSD-artig) |
| `python` | 3.12.13-slim-bookworm | PSF-2.0 plus Debian-Basissystem (überwiegend GPL/LGPL/BSD, unverändert genutzt) |

Debian-Systembibliotheken unter GPL/LGPL werden ausschließlich unverändert und
dynamisch gelinkt verwendet. Es entsteht keine Copyleft-Wirkung auf den
Anwendungscode.

---

## 5. Schriften und Symbole

- **Schriften:** keine. Es wird ausschließlich der Systemschriftstapel des jeweiligen
  Geräts verwendet (`system-ui`, San Francisco, Segoe UI, Roboto). Es werden keine
  Schriftdateien ausgeliefert und keine Schrift-CDNs eingebunden — damit entstehen
  weder Lizenz- noch Datenschutzfragen.
- **Symbole:** alle SVG-Symbole in der Oberfläche sind für dieses Projekt selbst
  gezeichnet. Es wird kein fremdes Icon-Set ausgeliefert.
- **Logo:** eigenständig gezeichnet (siehe `brand/BRAND.md`). Kein fremdes Logo, keine
  fremde Wortmarke, kein Bezug zu IBM oder Docling.

---

## 6. Frontend

Kein Framework, keine Bibliothek, kein CDN. Das ausgelieferte JavaScript und CSS ist
vollständig eigener Code. Damit entfallen Frontend-Lizenzabhängigkeiten und externe
Requests.

---

## 7. Prüfmethode und Wiederholung

Geprüft wurde durch direktes Abrufen von `LICENSE`-Dateien der Repositories,
der Lizenzfelder der PyPI-Metadaten und der Lizenzangaben der Modellkarten auf
Hugging Face. Diese Datei ist bei jedem Versionswechsel von Docling, Docling Serve
oder einem der Modelle erneut zu prüfen — Modelllizenzen können sich zwischen
Versionen ändern, auch wenn die Softwarelizenz gleich bleibt.
