"""Deutsche Texte — erreichbar unter /de.

Gleiche Schluessel wie in strings_en.py. Fehlt einer, faellt die Anzeige auf
Englisch zurueck, statt eine leere Stelle zu hinterlassen.
"""

STRINGS: dict[str, str] = {
    # ---------------------------------------------------------------- Rahmen
    "meta.title": "{product} — Dokumente in sauberes Markdown",
    "meta.description": "{product} wandelt Dokumente und Bilder in sauberes Markdown und "
    "JSON um — kostenlos, komplett auf eigenem Server.",
    "og.image_alt": "Klartext — aus Dokumenten wird sauberes Markdown",
    "skip_to_content": "Zum Inhalt springen",
    "nav.aria.main": "Hauptnavigation",
    "nav.login": "Anmelden",
    "nav.logout": "Abmelden",
    "nav.create_account": "Konto erstellen",
    "nav.create_account_short": "Konto",
    "nav.convert": "Konvertieren",
    "nav.account": "Konto",
    "nav.admin": "Verwaltung",
    "footer.aria.legal": "Rechtliches",
    "footer.imprint": "Impressum",
    "footer.privacy": "Datenschutz",
    "footer.terms": "Nutzungsbedingungen",
    "footer.licenses": "Open-Source-Lizenzen",
    "footer.note": "Verarbeitung ausschließlich auf eigenem Server. Keine Weitergabe an "
    "KI-Dienste Dritter.",
    "lang.aria": "Sprache",
    "lang.switch_to_en": "Auf Englisch umschalten",
    "lang.switch_to_de": "Auf Deutsch umschalten",
    "lang.to_de": "Deutsch",
    "lang.to_en": "English",

    # --------------------------------------------------------------- Landing
    "landing.title": "{product} — PDF, Scan & Foto in Markdown umwandeln — kostenlos",
    "landing.description": "PDF, Scans, Fotos, Word oder Excel kostenlos in Markdown und "
    "JSON umwandeln. OCR läuft lokal auf eigenem Server — ohne KI-Anbieter, DSGVO-freundlich.",
    "landing.schema.description": "Wandelt PDF, Fotos, Scans, Word-, Excel- und "
    "PowerPoint-Dateien in sauberes Markdown und strukturtreues JSON um. Verarbeitung "
    "ausschließlich auf einem eigenen Server, ohne Weitergabe an externe KI- oder "
    "OCR-Dienste.",
    "landing.eyebrow": "Kostenlos · Lokal verarbeitet · Ohne KI-Anbieter",
    "landing.h1": "Aus Dokumenten wird Klartext.",
    "landing.lead": "PDF, Foto, Scan, Word oder Excel hochladen — heraus kommt sauberes "
    "Markdown zum Weiterverwenden. Kein Abtippen mehr.",
    "landing.cta.primary": "Kostenloses Konto erstellen",
    "landing.cta.secondary": "Anmelden",
    "landing.hero_note": "Dauerhaft kostenlos. Keine Tarife, keine Zahlung, keine "
    "gesperrten Funktionen.",
    "landing.producthunt.alt": "Klartext — Dokumente und Scans werden zu sauberem "
    "Markdown und JSON. Vorgestellt auf Product Hunt.",
    # ------------------------------------------------------------- Vergleich
    # Rechtlicher Rahmen (§ 6 UWG, vergleichende Werbung): ausschliesslich
    # nachpruefbare Eigenschaften laut oeffentlicher Dokumentation der Projekte,
    # nichts Herabsetzendes, keine erfundenen Messwerte ueber fremde Werkzeuge.
    # Der eigene OCR-Benchmark vergleicht nur Engines INNERHALB von Klartext
    # und taucht hier bewusst nicht als Konkurrenzvergleich auf.
    "compare.title": "{product} oder pandoc, Docling, Marker? Ein ehrlicher Vergleich",
    "compare.description": "PDF und Scans in Markdown umwandeln: Klartext, pandoc, "
    "Docling, Marker und Cloud-Konverter im sachlichen Vergleich — OCR, Datenschutz, "
    "Einrichtung, Kosten.",
    "compare.h1": "Klartext — oder etwas anderes?",
    "compare.lead": "Es gibt mehrere gute Wege von PDF zu Markdown. Welcher passt, "
    "hängt davon ab, wer du bist und wo deine Dokumente laufen dürfen. Hier der "
    "sachliche Vergleich — auch mit den Fällen, in denen ein anderes Werkzeug die "
    "bessere Wahl ist.",
    "compare.list.aria": "Werkzeuge im Vergleich",
    "compare.ours": "das hier",
    "compare.col.ocr": "Scans & Fotos",
    "compare.col.data": "Wo Dokumente landen",
    "compare.col.setup": "Einrichtung",
    "compare.col.cost": "Preis",

    "compare.tool.1.name": "Klartext",
    "compare.tool.1.what": "Webdienst: hochladen, Markdown und JSON herunterladen. "
    "Gebaut auf der Open-Source-Bibliothek Docling.",
    "compare.tool.1.ocr": "Ja — Texterkennung läuft mit (RapidOCR).",
    "compare.tool.1.data": "Auf einem einzelnen Server in Deutschland; nach 24 Stunden "
    "automatisch gelöscht. Keine Weitergabe an KI-Anbieter.",
    "compare.tool.1.setup": "Keine. Browser genügt, auch am Handy.",
    "compare.tool.1.cost": "Kostenlos, ohne Tarife.",
    "compare.tool.1.verdict": "Für alle, die keine Software installieren wollen oder "
    "dürfen — und für Dokumente, die keinen US-Server sehen sollen.",

    "compare.tool.2.name": "Docling",
    "compare.tool.2.what": "Open-Source-Bibliothek (IBM, MIT-Lizenz) zum Auslesen von "
    "Dokumenten — genau die Technik, auf der Klartext aufbaut.",
    "compare.tool.2.ocr": "Ja, mit wählbaren OCR-Engines.",
    "compare.tool.2.data": "Wo du sie ausführst — dein Rechner, dein Server.",
    "compare.tool.2.setup": "Python-Umgebung, Modelle werden beim ersten Lauf geladen.",
    "compare.tool.2.cost": "Kostenlos (Open Source).",
    "compare.tool.2.verdict": "Wer eine Bibliothek für die eigene Software sucht, ist "
    "bei Docling direkt richtig — dafür braucht es Klartext nicht.",

    "compare.tool.3.name": "pandoc",
    "compare.tool.3.what": "Der Klassiker unter den Formatwandlern: übersetzt zwischen "
    "Dutzenden Textformaten (DOCX, LaTeX, HTML, Markdown …).",
    "compare.tool.3.ocr": "Nein — pandoc liest keine Scans oder Fotos, es arbeitet auf "
    "bereits vorhandenem Text.",
    "compare.tool.3.data": "Auf deinem Rechner.",
    "compare.tool.3.setup": "Lokale Installation, Kommandozeile.",
    "compare.tool.3.cost": "Kostenlos (Open Source).",
    "compare.tool.3.verdict": "Für saubere Textdateien ohne Scans hervorragend — wer "
    "DOCX nach Markdown will und die Kommandozeile mag, braucht nichts anderes.",

    "compare.tool.4.name": "Marker",
    "compare.tool.4.what": "Python-Bibliothek für PDF nach Markdown mit Fokus auf "
    "wissenschaftliche Dokumente.",
    "compare.tool.4.ocr": "Ja.",
    "compare.tool.4.data": "Auf deinem Rechner; für flottes Arbeiten wird eine GPU "
    "empfohlen.",
    "compare.tool.4.setup": "Python-Umgebung plus Modell-Downloads.",
    "compare.tool.4.cost": "Open Source; Lizenzbedingungen des Projekts beachten.",
    "compare.tool.4.verdict": "Stark für Stapelverarbeitung auf eigener Hardware, wenn "
    "Einrichtung und GPU kein Hindernis sind.",

    "compare.tool.5.name": "Cloud-KI-Konverter",
    "compare.tool.5.what": "Chat-Assistenten und Online-Konverter, bei denen das "
    "Dokument zur Verarbeitung hochgeladen wird.",
    "compare.tool.5.ocr": "Meist ja.",
    "compare.tool.5.data": "Auf den Servern des jeweiligen Anbieters, häufig außerhalb "
    "der EU; Speicherdauer je nach Anbieter und Einstellung.",
    "compare.tool.5.setup": "Keine bis Konto-Anmeldung.",
    "compare.tool.5.cost": "Teils kostenlos mit Grenzen, teils Abo.",
    "compare.tool.5.verdict": "Bequem für Unkritisches. Für Verträge, Patientendaten "
    "oder Mandantenunterlagen entscheidet die Frage, ob das Dokument den Anbieter "
    "wechseln darf.",

    "compare.when.h": "Kurz entschieden",
    "compare.when.1": "<strong>Saubere DOCX/HTML ohne Scans, Kommandozeile ok?</strong> "
    "pandoc.",
    "compare.when.2": "<strong>Eigene Software bauen?</strong> Docling als Bibliothek.",
    "compare.when.3": "<strong>Stapelverarbeitung auf eigener GPU?</strong> Marker "
    "oder Docling.",
    "compare.when.4": "<strong>Kein Installieren, Scans und Fotos dabei, Dokumente "
    "sollen in Deutschland bleiben?</strong> Klartext.",
    "compare.back": "Zur Startseite",
    "compare.disclaimer": "Stand August 2026, Eigenschaften laut öffentlicher "
    "Dokumentation der jeweiligen Projekte. Alle genannten Namen sind Marken ihrer "
    "Inhaber; es bestehen keine Verbindungen zu den Projekten — Docling wird als "
    "Grundlage von Klartext genutzt und ist unter Lizenzen genannt. Unser eigener "
    "Genauigkeits-Benchmark misst ausschließlich OCR-Engines innerhalb von Klartext "
    "und trifft keine Aussage über die hier genannten Werkzeuge. Etwas veraltet oder "
    "falsch dargestellt? Eine Nachricht an die Adresse im Impressum genügt, wir "
    "korrigieren.",

    "landing.bench.h": "Gemessen, nicht versprochen",
    "landing.bench.sub": "Drei Texterkennungen traten gegeneinander an. Eine Messung, "
    "ein Sieger — und der läuft hier im Betrieb.",
    "landing.bench.active": "läuft hier",
    "landing.bench.method": "Gemessen an 45 Pflichtangaben — Namen, Artikelnummern, "
    "Beträge, Umlaute, Gradzeichen — über vier Testscans, jede einzeln von Hand geprüft. "
    "Ein typisches Dokument ist in Sekunden umgewandelt, nicht in Minuten.",
    "landing.bench.compare_link": "Und wie schlägt sich Klartext gegen pandoc & Co.?",
    "landing.io.md_cap": "zum Lesen und Weiterverwenden",
    "landing.io.json_cap": "volle Struktur für andere Programme",
    "landing.io.in_label": "Eingabe",
    "landing.io.in_note": "Formate",
    "landing.io.out_label": "Ausgabe",
    "landing.io.out_note": "immer zwei Dateien",
    "landing.showcase.aria": "Links ein gescanntes Dokument mit einer Tabelle, rechts das "
    "daraus erzeugte Markdown mit derselben Tabelle.",
    "landing.showcase.before": "Vorher — Scan oder Foto",
    "landing.showcase.after": "Nachher — Markdown",
    "landing.showcase.code.heading": "# Preisliste 2026",
    "landing.showcase.code.body": """| Artikelnummer | Bezeichnung      | Preis  |
|---------------|------------------|--------|
| A-1001        | Kupferrohr 15 mm | 8,40 € |
| B-2010        | Dämmschale 20 mm | 4,95 € |

Alle Preise zzgl. MwSt.""",
    "landing.formats.aria": "Unterstützte Dateiformate",
    "landing.formats.title": "Liest zuverlässig",
    "landing.stats.aria": "Eckdaten",
    "landing.stats.formats": "Formate",
    "landing.stats.pages": "Seiten je Dokument",
    "landing.stats.retention": "dann gelöscht",
    "landing.stats.price": "dauerhaft",
    "landing.feature.1.h": "Nichts verlässt den Server",
    "landing.feature.1.p": "Alles läuft auf diesem Server. Keine Inhalte an OpenAI, "
    "Anthropic, Google oder einen anderen Dienst. Keine Werbenetzwerke, keine Verfolgung "
    "über Seiten hinweg.",
    "landing.feature.2.h": "So wenig Verlust wie möglich",
    "landing.feature.2.p": "Zahlen, Namen und Tabellen bleiben, wie sie im Original "
    "stehen. Nichts wird zusammengefasst oder umformuliert.",
    "landing.feature.3.h": "Automatisch gelöscht",
    "landing.feature.3.p": "Dateien und Ergebnisse verschwinden nach {hours} Stunden von "
    "selbst — oder sofort, wenn du willst.",
    "landing.uses.h": "Wofür Leute das nutzen",
    "landing.uses.sub": "Alltagsfälle, keine Technik.",
    "landing.uses.1.h": "Rechnung abfotografiert",
    "landing.uses.1.p": "Positionen zum Kopieren statt abtippen.",
    "landing.uses.2.h": "Lieferschein gescannt",
    "landing.uses.2.p": "Mengen und Artikelnummern als Tabelle.",
    "landing.uses.3.h": "Vertrag als PDF",
    "landing.uses.3.p": "Einzelne Klauseln per Textsuche finden.",
    "landing.uses.4.h": "Preisliste fotografiert",
    "landing.uses.4.p": "Tabelle direkt für Excel.",
    "landing.uses.5.h": "Vorlesungsskript",
    "landing.uses.5.p": "Text für Zusammenfassungen und Karteikarten.",
    "landing.uses.6.h": "Altes Schreiben aus dem Ordner",
    "landing.uses.6.p": "Durchsuchbar statt nur ein Bild.",
    "landing.uses.7.h": "Excel-Tabelle",
    "landing.uses.7.p": "Als Markdown für Programme ohne XLSX.",
    "landing.conv.h": "Die wichtigsten Umwandlungen",
    "landing.conv.sub": "Was dabei erhalten bleibt und was nicht.",
    "landing.conv.1.h": "PDF in Markdown",
    "landing.conv.1.p": "Rechnungen, Verträge, Handbücher. Überschriften, Absätze und "
    "Tabellen werden übernommen. Bei mehrspaltigem Layout kann die Reihenfolge "
    "durcheinandergeraten.",
    "landing.conv.2.h": "Foto in Text",
    "landing.conv.2.p": "Ein abfotografiertes Dokument wird zu kopierbarem Text. Ein "
    "gerades, scharfes Foto liefert das beste Ergebnis.",
    "landing.conv.3.h": "Word in Markdown",
    "landing.conv.3.p": "Überschriften, Absätze, Listen und Tabellen kommen strukturiert "
    "an. Kommentare, Fußnoten und Textfelder bleiben auf der Strecke.",
    "landing.conv.4.h": "Excel in Markdown",
    "landing.conv.4.p": "Jede Tabelle wird zur Markdown-Tabelle mit Kopfzeile. "
    "Zellformate, Formeln und Diagramme werden nicht übertragen.",
    "landing.conv.5.h": "Scan in Text",
    "landing.conv.5.p": "Auch ein altes, vergilbtes Schreiben wird durchsuchbar. Bei "
    "schlechter Scanqualität oder Handschrift sinkt die Erkennung.",
    "landing.conv.6.h": "PowerPoint in Markdown",
    "landing.conv.6.p": "Jede Folie wird zu Überschrift und Aufzählung. Grafiken, "
    "Animationen und Notizen bleiben auf der Strecke.",
    "landing.io.h": "Was hineingeht, was herauskommt",
    "landing.io.sub": "Diese Dateitypen nimmt {product} an:",
    "landing.io.note": "Heraus kommen immer zwei Dateien: <strong>.md</strong> zum Lesen "
    "und Weiterverwenden, <strong>.json</strong> mit der vollständigen Struktur für andere "
    "Programme.",
    "landing.limits.h": "Grenzen für alle gleich",
    "landing.limits.sub": "Damit der Dienst für alle stabil bleibt, gelten technische "
    "Fair-Use-Grenzen. Sie dienen dem Schutz vor Überlastung — nicht dem Verkauf.",
    "landing.limits.filesize": "Größe je Datei",
    "landing.limits.files": "Dateien je Upload",
    "landing.limits.pages": "Seiten je Dokument",
    "landing.limits.perday": "Konvertierungen pro Tag",
    "landing.faq.h": "Häufige Fragen",
    "landing.faq.1.q": "Ist {product} wirklich kostenlos?",
    "landing.faq.1.a": "Ja. Es gibt keine Tarife, keine Zahlung und keine gesperrten "
    "Funktionen. Für die Nutzung ist lediglich ein kostenloses Konto nötig.",
    "landing.faq.2.q": "Was ist Markdown überhaupt?",
    "landing.faq.2.a": "Eine einfache Auszeichnungssprache für Text: Überschriften, Listen "
    "und Tabellen werden mit gewöhnlichen Zeichen wie # oder | markiert. Lesbar als reiner "
    "Text und, in Notiz-Apps, Wikis oder auf GitHub, hübsch formatiert.",
    "landing.faq.2.a_html": "Eine einfache Auszeichnungssprache für Text: Überschriften, "
    "Listen und Tabellen werden mit gewöhnlichen Zeichen wie <code>#</code> oder "
    "<code>|</code> markiert. Lesbar als reiner Text und, in Notiz-Apps, Wikis oder auf "
    "GitHub, hübsch formatiert.",
    "landing.faq.3.q": "Wozu dient die JSON-Datei?",
    "landing.faq.3.a": "Sie enthält dieselben Inhalte maschinenlesbar aufgeschlüsselt — "
    "mit Seiten, Blöcken und Tabellenzellen einzeln erfasst. Praktisch zum Einbinden in "
    "eigene Programme, Automatisierungen oder Datenbanken, wo Markdown zu grob wäre.",
    "landing.faq.4.q": "Werden meine Dokumente an einen KI-Anbieter weitergegeben?",
    "landing.faq.4.a": "Nein. Die gesamte Umwandlung läuft auf einem eigenen Server. Es "
    "werden keine Inhalte an OpenAI, Anthropic, Google oder andere KI- oder OCR-Dienste "
    "geschickt.",
    "landing.faq.5.q": "Werden meine Dokumente gespeichert?",
    "landing.faq.5.a": "Nur vorübergehend, zur Verarbeitung. Hochgeladene Dateien und "
    "Ergebnisse werden automatisch nach {hours} Stunden gelöscht, und lassen sich bei "
    "jedem Auftrag auch von Hand vorher entfernen. {product} ist kein dauerhafter "
    "Speicherort.",
    "landing.faq.6.q": "Ist das Ergebnis fehlerfrei?",
    "landing.faq.6.a": "Nein. Die Umwandlung läuft automatisch und kann bei schlechten "
    "Scans, Handschrift oder verschachtelten Tabellen Fehler enthalten. Markdown kann "
    "außerdem nicht jedes Layout abbilden — für die strukturtreuere Version eignet sich "
    "die JSON-Datei. Ergebnisse sollten vor der Weiterverwendung geprüft werden.",
    "landing.faq.7.q": "Wie gut erkennt {product} Handschrift?",
    "landing.faq.7.a": "Ehrlich gesagt schlecht. Die Texterkennung ist auf gedruckten Text "
    "trainiert. Handschriftliche Notizen, Unterschriften oder von Hand ausgefüllte "
    "Formulare werden oft falsch oder gar nicht erkannt — für Gedrucktes und gute Scans "
    "funktioniert sie zuverlässig.",
    "landing.faq.8.q": "Funktioniert es mit Fotos vom Handy?",
    "landing.faq.8.a": "Ja. Entscheidend sind Schärfe und Auflösung: Ein gerades, scharfes "
    "und gut ausgeleuchtetes Foto liefert brauchbare Ergebnisse, ein verwackeltes oder "
    "dunkles Foto lässt die Texterkennung öfter stolpern.",
    "landing.faq.9.q": "Welche Dateien kann ich hochladen?",
    "landing.faq.10.q": "Warum brauche ich ein Konto?",
    "landing.faq.10.a": "Die Registrierung ist kostenlos und sorgt dafür, dass die "
    "Fair-Use-Grenzen pro Person gelten, statt sich alle Besucher eine gemeinsame Grenze "
    "zu teilen.",

    # ----------------------------------------------------------------- Login
    "login.title": "Anmelden — {product}",
    "login.description": "Bei {product} anmelden und Dokumente in Markdown und JSON "
    "umwandeln.",
    "login.h1": "Anmelden",
    "login.email": "E-Mail-Adresse",
    "login.password": "Passwort",
    "login.submit": "Anmelden",
    "login.resend": "Bestätigungsmail erneut senden",
    "login.forgot": "Passwort vergessen?",
    "login.no_account": "Noch kein Konto?",
    "login.create": "Konto erstellen",

    # -------------------------------------------------------------- Register
    "register.title": "Kostenloses Konto erstellen — {product}",
    "register.description": "Kostenloses Konto bei {product} anlegen und Dokumente in "
    "Markdown und JSON umwandeln. Keine Tarife, keine Zahlung, keine gesperrten "
    "Funktionen.",
    "register.h1": "Konto erstellen",
    "register.intro": "Kostenlos, ohne Tarife. Das Konto brauchen wir nur, damit die "
    "Nutzungsgrenzen pro Person gelten statt sich alle Besucher eine gemeinsame Grenze zu "
    "teilen.",
    "register.errors_intro": "Bitte prüfe deine Eingaben:",
    "register.email": "E-Mail-Adresse",
    "register.password": "Passwort",
    "register.password_hint": "Mindestens 10 Zeichen. Länger ist besser als kompliziert.",
    "register.password2": "Passwort wiederholen",
    "register.accept": "Ich habe die {terms} und die {privacy} gelesen.",
    "register.accept.terms": "Nutzungsbedingungen",
    "register.accept.privacy": "Datenschutzhinweise",
    "register.submit": "Konto erstellen",
    "register.have_account": "Schon ein Konto?",
    "register.sign_in": "Hier anmelden",

    # --------------------------------------------------------- Register done
    "register_done.title": "Fast geschafft — {product}",
    "register_done.h1": "Fast geschafft",
    "register_done.mail": "Falls die Adresse noch frei war, ist eine E-Mail mit "
    "Bestätigungslink unterwegs. Der Link gilt 24 Stunden.",
    "register_done.spam": "Nichts da? Bitte im Spam-Ordner nachsehen. Wenn nach ein paar "
    "Minuten nichts ankommt, {link}.",
    "register_done.spam_link": "schicken wir die Mail erneut",
    "register_done.nomail": "Das Konto ist angelegt. Du kannst dich jetzt direkt anmelden.",
    "register_done.to_login": "Zur Anmeldung",

    # --------------------------------------------------------- Verify again
    "verify_again.title": "Bestätigungsmail erneut senden — {product}",
    "verify_again.description": "Keine Bestätigungsmail von {product} bekommen? Hier neu "
    "anfordern — der Link gilt 24 Stunden.",
    "verify_again.h1": "Bestätigungsmail erneut senden",
    "verify_again.nomail": "Auf dieser Installation ist kein E-Mail-Versand eingerichtet. "
    "Bitte wende dich an den Betreiber.",
    "verify_again.intro": "Gib deine Adresse ein. Falls dazu ein noch unbestätigtes Konto "
    "gehört, schicken wir einen neuen Link. Er gilt 24 Stunden; ältere Links werden dabei "
    "ungültig.",
    "verify_again.email": "E-Mail-Adresse",
    "verify_again.submit": "Mail neu schicken",
    "verify_again.back": "Zurück zur Anmeldung",

    # ---------------------------------------------------------------- Forgot
    "forgot.title": "Passwort vergessen — {product}",
    "forgot.description": "Passwort für dein {product}-Konto zurücksetzen. Wir schicken "
    "dir einen Link, der eine Stunde gilt.",
    "forgot.h1": "Passwort vergessen",
    "forgot.nomail": "Auf dieser Installation ist kein E-Mail-Versand eingerichtet. Das "
    "Zurücksetzen per Link funktioniert deshalb derzeit nicht — bitte wende dich an den "
    "Betreiber.",
    "forgot.intro": "Gib deine Adresse ein. Falls es dazu ein Konto gibt, schicken wir "
    "einen Link zum Zurücksetzen. Der Link gilt eine Stunde und funktioniert einmal.",
    "forgot.email": "E-Mail-Adresse",
    "forgot.submit": "Link anfordern",
    "forgot.back": "Zurück zur Anmeldung",

    # ----------------------------------------------------------------- Reset
    "reset.title": "Neues Passwort — {product}",
    "reset.description": "Neues Passwort für dein {product}-Konto setzen.",
    "reset.h1": "Neues Passwort setzen",
    "reset.password": "Neues Passwort",
    "reset.password_hint": "Mindestens 10 Zeichen.",
    "reset.password2": "Neues Passwort wiederholen",
    "reset.sessions_note": "Alle bestehenden Anmeldungen werden dabei beendet.",
    "reset.submit": "Passwort speichern",
    "reset.broken": "Der Link ist unvollständig oder abgelaufen.",
    "reset.request_new": "Neuen Link anfordern",

    # ------------------------------------------------------------- Info/Error
    "info.continue": "Weiter",
    "info.to_app": "Zur Übersicht",
    "info.to_login": "Zur Anmeldung",
    "error.title": "Fehler {status} — {product}",
    "error.h.401": "Anmeldung nötig",
    "error.h.404": "Nicht gefunden",
    "error.h.413": "Datei zu groß",
    "error.h.429": "Kurz warten, bitte",
    "error.h.400": "Das hat nicht geklappt",
    "error.h.other": "Da ist etwas schiefgelaufen",
    "error.code": "Fehler {status}",
    "error.to_home": "Zur Startseite",
    "error.to_app": "Zur Übersicht",
    "error.to_login": "Zur Anmeldung",

    # ------------------------------------------------------------- Dashboard
    "dashboard.title": "Konvertieren — {product}",
    "dashboard.h1": "Neue Konvertierung",
    "dashboard.explainer": "Datei hochladen, {product} liest den Inhalt aus.",
    "dashboard.drop": "Dateien hierher ziehen",
    "dashboard.or": "oder",
    "dashboard.choose": "Dateien auswählen",
    "dashboard.limits": "max. {mb} MB · {files} Dateien · {pages} Seiten",
    "dashboard.submit": "Konvertierung starten",
    "dashboard.clear": "Auswahl leeren",
    "dashboard.fineprint": "Löschung nach {hours} Stunden. Verarbeitung nur auf diesem "
    "Server.",
    "dashboard.jobs": "Aufträge",
    "dashboard.zip": "Alles als ZIP",
    "dashboard.usage": "Heute {jobs}/{jobs_max} Konvertierungen · {pages}/{pages_max} "
    "Seiten",
    "dashboard.usage_active": "{active} in Arbeit, {queued} wartend",
    "dashboard.empty": "Noch nichts konvertiert. Lade oben eine Datei hoch — das Ergebnis "
    "erscheint hier.",
    "dashboard.empty.1": "Datei auswählen oder in das Feld oben ziehen.",
    "dashboard.empty.2": "Auf „Konvertierung starten“ tippen.",
    "dashboard.empty.3": "Fertige Aufträge erscheinen hier mit Markdown- und "
    "JSON-Download.",

    # ------------------------------------------------------------------ Job
    "job.back": "← Zurück zur Übersicht",
    "job.status.done": "Fertig",
    "job.status.processing": "Wird verarbeitet",
    "job.status.queued": "In Warteschlange",
    "job.status.error": "Fehler",
    "job.pages": "{count} Seite",
    "job.pages_plural": "{count} Seiten",
    "job.seconds": "{value} s",
    "job.expires": "wird gelöscht am {when} Uhr",
    "job.note.title": "Hinweis zur Vorlage.",
    "job.note.page": "Seite",
    "job.note.row": "Zeile",
    "job.note.column": "Spalte",
    "job.note.read_as": "Gelesen als",
    "job.pending": "Das Dokument ist noch in Arbeit. Diese Seite aktualisiert sich nicht "
    "von selbst — {link} zeigt den Fortschritt live.",
    "job.pending.link": "die Übersicht",
    "job.download_all": "Alles herunterladen (ZIP)",
    "job.download_all_images": "Alles herunterladen — ZIP mit {count} Bildern",
    "job.copy": "Kopieren",
    "job.formats_note": "<strong>.md</strong> für Notizen und Texte, "
    "<strong>.json</strong> für eigene Programme. Meistens reicht die Markdown-Datei.",
    "job.images.h": "Bilder aus dem Dokument",
    "job.images.count": "{count} Abbildung herausgelöst. Im Markdown steht ein Verweis "
    "darauf, im ZIP liegt sie als Datei.",
    "job.images.count_plural": "{count} Abbildungen herausgelöst. Im Markdown stehen "
    "Verweise darauf, im ZIP liegen sie als Dateien.",
    "job.image.alt": "Bild {seq} aus dem Dokument",
    "job.image.alt_page": "Bild {seq} aus dem Dokument, Seite {page}",
    "job.preview.h": "Vorschau",
    "job.preview.raw": "Rohtext mit Markdown-Zeichen wie <code>#</code> und "
    "<code>|</code>.",
    "job.preview.gone": "Das Ergebnis ist nicht mehr verfügbar. Vermutlich wurde es "
    "bereits automatisch gelöscht.",
    "job.delete": "Auftrag jetzt löschen",

    # --------------------------------------------------------------- Account
    "account.title": "Konto — {product}",
    "account.h1": "Konto",
    "account.changed": "Das Passwort wurde geändert.",
    "account.signed_in_as": "Angemeldet als",
    "account.unverified": "Die E-Mail-Adresse ist noch nicht bestätigt.",
    "account.usage.h": "Nutzung",
    "account.usage.sub": "Reiner Serverschutz. Für alle Konten gleich.",
    "account.usage.quota": "Kontingent",
    "account.usage.used": "Genutzt",
    "account.usage.limit": "Grenze",
    "account.usage.jobs_hour": "Konvertierungen (Stunde)",
    "account.usage.jobs_day": "Konvertierungen (Tag)",
    "account.usage.pages_day": "Seiten (Tag)",
    "account.usage.bytes_day": "Datenmenge (Tag)",
    "account.usage.active": "Gleichzeitig in Arbeit",
    "account.password.h": "Passwort ändern",
    "account.password.current": "Aktuelles Passwort",
    "account.password.new": "Neues Passwort",
    "account.password.hint": "Mindestens 10 Zeichen.",
    "account.password.repeat": "Neues Passwort wiederholen",
    "account.password.note": "Alle anderen Anmeldungen werden dabei beendet.",
    "account.password.submit": "Passwort speichern",
    "account.delete.h": "Konto löschen",
    "account.delete.p": "Konto, Aufträge und alle Dateien werden sofort und endgültig "
    "gelöscht.",
    "account.delete.confirm": "Zur Bestätigung {word} eingeben",
    "account.delete.word": "LÖSCHEN",
    "account.delete.submit": "Konto endgültig löschen",

    # ----------------------------------------------------------------- Admin
    "admin.title": "Verwaltung — {product}",
    "admin.h1": "Verwaltung",
    "admin.saved": "Die Grenzen wurden gespeichert.",
    "admin.load.h": "Auslastung",
    "admin.load.queued": "wartend",
    "admin.load.processing": "in Arbeit",
    "admin.load.users": "Konten",
    "admin.load.done": "fertig (24 h)",
    "admin.load.errors": "Fehler (24 h)",
    "admin.load.avg": "Schnitt (24 h)",
    "admin.limits.h": "Technische Grenzen",
    "admin.limits.sub": "Wirken sofort für alle Konten. Reiner Serverschutz — keine "
    "Tarife, kein Verkauf.",
    "admin.limits.default": "Vorgabe aus der Konfiguration: {value}",
    "admin.limits.submit": "Grenzen speichern",
    "admin.users.h": "Konten",
    "admin.users.email": "E-Mail",
    "admin.users.status": "Status",
    "admin.users.jobs": "Aufträge",
    "admin.users.last_seen": "Zuletzt aktiv",
    "admin.users.action": "Aktion",
    "admin.users.admin_badge": "Verwaltung",
    "admin.users.active": "aktiv",
    "admin.users.inactive": "deaktiviert",
    "admin.users.unconfirmed": "unbestätigt",
    "admin.users.never": "nie",
    "admin.users.deactivate": "Deaktivieren",
    "admin.users.activate": "Aktivieren",
    "admin.users.own": "eigenes Konto",
    "admin.users.note": "Passwörter sind als Argon2id-Hash gespeichert und hier bewusst "
    "nicht einsehbar.",
    "admin.failed.h": "Zuletzt fehlgeschlagen",
    "admin.failed.time": "Zeitpunkt",
    "admin.failed.reason": "Grund",
    "admin.failed.account": "Konto",
    "admin.failed.note": "Dateinamen und Inhalte werden bewusst nicht protokolliert.",
    "admin.failed.none": "Keine fehlgeschlagenen Aufträge.",

    # ---------------------------------------------------------------- Rechtes
    "imprint.title": "Impressum — {product}",
    "imprint.description": "Impressum und Anbieterkennzeichnung von {product}.",
    "imprint.h1": "Impressum",
    "imprint.legal_note": "",
    "imprint.unconfigured": "Noch nicht konfiguriert.",
    "imprint.unconfigured.p": "Die Pflichtangaben nach § 5 DDG stehen noch aus. Sie werden "
    "über die Umgebungsvariablen {vars} gesetzt. Es werden hier bewusst keine Angaben "
    "erfunden.",
    "imprint.none": "— nicht konfiguriert —",
    "imprint.provider.h": "Angaben gemäß § 5 DDG",
    "imprint.contact.h": "Kontakt",
    "imprint.contact.email": "E-Mail",
    "imprint.contact.phone": "Telefon",
    "imprint.vat.h": "Umsatzsteuer-Identifikationsnummer",
    "imprint.responsible.h": "Verantwortlich für den Inhalt",
    "imprint.dispute.h": "Verbraucherstreitbeilegung",
    "imprint.dispute.p": "Wir sind nicht bereit und nicht verpflichtet, an "
    "Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.",
    "imprint.oss.h": "Eingesetzte Open-Source-Software",
    "imprint.oss.p": "Die Konvertierung erfolgt mit freier Software. Die vollständige "
    "Liste mit Lizenzen und Urheberrechtsvermerken steht unter {link}. {product} ist ein "
    "eigenständiger Dienst und steht in keiner Verbindung zu den Urhebern der eingesetzten "
    "Bibliotheken.",

    "privacy.title": "Datenschutz — {product}",
    "privacy.description": "Datenschutzhinweise von {product}: was mit hochgeladenen "
    "Dokumenten passiert, Speicherdauer und deine Rechte.",
    "privacy.h1": "Datenschutzhinweise",
    "privacy.legal_note": "",
    "privacy.unconfigured": "Verantwortliche Stelle noch nicht konfiguriert.",
    "privacy.unconfigured.p": "Ohne diese Angabe ist der Text unvollständig. Siehe {link}.",
    "privacy.controller.h": "Verantwortliche Stelle",
    "privacy.uploads.h": "Was mit hochgeladenen Dokumenten passiert",
    "privacy.uploads.p1": "Hochgeladene Dateien werden ausschließlich auf dem Server "
    "dieses Dienstes verarbeitet. Die Umwandlung erfolgt lokal durch freie Software, die "
    "auf demselben Server läuft.",
    "privacy.uploads.p2": "<strong>Es werden keine Dokumentinhalte an Dritte "
    "übermittelt.</strong> Insbesondere nicht an:",
    "privacy.uploads.l1": "OpenAI, Anthropic, Google oder andere Anbieter von "
    "Sprachmodellen",
    "privacy.uploads.l2": "externe OCR- oder Texterkennungsdienste",
    "privacy.uploads.l3": "externe Bildanalysedienste",
    "privacy.uploads.l4": "externe Analyse-, Statistik- oder Tracking-Anbieter",
    "privacy.uploads.l5": "Fehlerprotokoll-Dienste",
    "privacy.uploads.p3": "Dokumentinhalte, erkannte Texte und Dateinamen werden nicht in "
    "Anwendungsprotokolle geschrieben. Protokolliert werden ausschließlich technische "
    "Ereignisse wie Fehlerarten, Dauer und Seitenzahl.",
    "privacy.retention.h": "Speicherdauer",
    "privacy.retention.p": "Hochgeladene Dateien und erzeugte Ergebnisse werden automatisch "
    "nach <strong>{hours} Stunden</strong> gelöscht. Die Originaldatei wird bereits kurz "
    "nach Abschluss der Verarbeitung entfernt. Jeder Auftrag kann jederzeit selbst sofort "
    "gelöscht werden.",
    "privacy.account.h": "Konto und Verarbeitungszwecke",
    "privacy.account.p": "Gespeichert werden: E-Mail-Adresse, ein Argon2id-Hash des "
    "Passworts (nie das Passwort selbst), Zeitpunkt der Registrierung und der letzten "
    "Anmeldung sowie Auftragsdaten (Dateiname, Dateityp, Größe, Seitenzahl, Status, "
    "Zeitpunkte). Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Erfüllung des "
    "Nutzungsverhältnisses) sowie Art. 6 Abs. 1 lit. f DSGVO für den Schutz des Dienstes "
    "vor Missbrauch.",
    "privacy.mail.h": "E-Mail-Versand",
    "privacy.mail.p1": "Bestätigungs- und Passwort-Links werden über den E-Mail-Dienst von "
    "Google versendet (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, "
    "Irland). Übermittelt wird ausschließlich die E-Mail-Adresse samt Link — "
    "<strong>niemals Dokumentinhalte oder Dateinamen</strong>.",
    "privacy.mail.p2": "Diese E-Mails sind reiner Text, enthalten keine Zählpixel und "
    "keine umgeleiteten Links. Es wird nicht erfasst, ob oder wann eine Nachricht geöffnet "
    "wurde.",
    "privacy.cookies.h": "Cookies",
    "privacy.cookies.p": "Es werden ausschließlich technisch notwendige Cookies gesetzt: "
    "ein Sitzungscookie für die Anmeldung, ein Cookie zum Schutz von Formularen gegen "
    "Fremdeinreichung (CSRF) und ein Cookie für die gewählte Sprache. Alle sind für den "
    "Betrieb erforderlich und deshalb nach § 25 Abs. 2 TDDDG nicht einwilligungspflichtig. "
    "Es gibt keine Tracking-, Werbe- oder Analyse-Cookies und deshalb bewusst auch kein "
    "Cookie-Banner.",
    "privacy.analytics.h": "Reichweitenmessung",
    "privacy.analytics.p1": "Um zu sehen, wie oft die öffentlichen Seiten aufgerufen "
    "werden, läuft auf demselben Server eine selbst betriebene Instanz von "
    "<strong>Plausible Analytics</strong>. Es ist kein externer Dienst beteiligt; die Daten "
    "verlassen den Server nicht. Das Zählskript wird über die eigene Domain ausgeliefert, "
    "die Seite baut also keine Verbindung zu einem fremden Rechner auf.",
    "privacy.analytics.p2": "Erfasst werden je Aufruf:",
    "privacy.analytics.l1": "die aufgerufene Seite und die verweisende Adresse",
    "privacy.analytics.l2": "Browser, Betriebssystem und Gerätetyp in grober Einteilung",
    "privacy.analytics.l3": "das Land, abgeleitet aus der IP-Adresse",
    "privacy.analytics.p3": "<strong>Die IP-Adresse wird nicht gespeichert.</strong> Aus "
    "ihr wird zusammen mit einem täglich wechselnden Zufallswert eine Prüfsumme gebildet, "
    "die nur der Zählung wiederkehrender Aufrufe innerhalb eines Tages dient und danach "
    "niemandem mehr zuzuordnen ist. Es werden keine Cookies gesetzt und nichts auf dem "
    "Gerät gespeichert oder ausgelesen — deshalb ist dafür weder eine Einwilligung nach "
    "§ 25 TDDDG nötig noch ein Cookie-Banner. Rechtsgrundlage ist das berechtigte "
    "Interesse an einer datensparsamen Reichweitenmessung, Art. 6 Abs. 1 lit. f DSGVO.",
    "privacy.analytics.p4": "<strong>Im angemeldeten Bereich wird nicht gemessen.</strong> "
    "Dort stehen Auftragskennungen in der Adresszeile; diese haben in einer Statistik "
    "nichts zu suchen. Gemessen werden ausschließlich die öffentlich zugänglichen Seiten.",
    "privacy.logs.h": "Server-Protokolle",
    "privacy.logs.p": "Zum Schutz vor Missbrauch werden IP-Adressen kurzzeitig für "
    "Zählerstände (Anfragen pro Minute, Anmeldeversuche) verwendet. Diese Zähler werden "
    "nach spätestens zwei Tagen gelöscht. Der Betrieb läuft hinter einem "
    "Content-Delivery-Netzwerk, das den Aufruf technisch weiterleitet und dabei "
    "Verbindungsdaten verarbeitet.",
    "privacy.rights.h": "Deine Rechte",
    "privacy.rights.p": "Auskunft, Berichtigung, Löschung, Einschränkung, "
    "Datenübertragbarkeit und Widerspruch nach Art. 15–21 DSGVO. Das Konto kann jederzeit "
    "selbst unter {link} vollständig gelöscht werden; dabei werden alle zugehörigen Daten "
    "und Dateien sofort entfernt. Es besteht ein Beschwerderecht bei einer "
    "Datenschutzaufsichtsbehörde.",

    "terms.title": "Nutzungsbedingungen — {product}",
    "terms.description": "Nutzungsbedingungen von {product}: kostenlose Nutzung, faire "
    "Nutzungsgrenzen und Ergebnisqualität.",
    "terms.h1": "Nutzungsbedingungen",
    "terms.legal_note": "",
    "terms.unconfigured": "Betreiber noch nicht konfiguriert.",
    "terms.unconfigured.p": "Siehe {link}.",
    "terms.1.h": "1. Gegenstand",
    "terms.1.p": "{product} wandelt hochgeladene Dokumente und Bilder in Markdown und eine "
    "strukturierte JSON-Darstellung um. Der Dienst ist kostenlos. Es gibt keine "
    "kostenpflichtigen Funktionen, keine Tarife und kein Abonnement.",
    "terms.2.h": "2. Konto",
    "terms.2.p": "Für die Nutzung ist ein Konto erforderlich. Zugangsdaten sind geheim zu "
    "halten. Ein Konto darf nicht an Dritte weitergegeben werden. Das Konto kann jederzeit "
    "selbst gelöscht werden.",
    "terms.3.h": "3. Faire Nutzung",
    "terms.3.p": "Es gelten technische Grenzen zum Schutz des Servers: derzeit {mb} MB je "
    "Datei, {files} Dateien je Upload, {pages} Seiten je Dokument, {per_hour} "
    "Konvertierungen je Stunde und {per_day} je Tag. Diese Werte können zur Sicherung des "
    "Betriebs angepasst werden. Automatisierte Massennutzung, Umgehungsversuche der "
    "Grenzen und der Betrieb über mehrere Konten hinweg sind nicht gestattet.",
    "terms.4.h": "4. Inhalte",
    "terms.4.p": "Es dürfen nur Dateien hochgeladen werden, an denen die nötigen Rechte "
    "bestehen. Rechtswidrige Inhalte sind untersagt. Verantwortlich für die hochgeladenen "
    "Inhalte ist ausschließlich die hochladende Person.",
    "terms.5.h": "5. Verfügbarkeit und Datenverlust",
    "terms.5.p": "Der Dienst wird ohne Verfügbarkeitszusage bereitgestellt. Dateien und "
    "Ergebnisse werden nach {hours} Stunden automatisch gelöscht — der Dienst ist "
    "<strong>kein Speicherort und kein Archiv</strong>. Ergebnisse sind selbst zu sichern.",
    "terms.6.h": "6. Ergebnisqualität",
    "terms.6.p": "Die Umwandlung erfolgt automatisch. Ziel ist es, so wenig Information "
    "wie technisch möglich zu verlieren: es wird nichts zusammengefasst, umformuliert oder "
    "korrigiert. Eine fehlerfreie Erkennung — insbesondere bei gescannten Vorlagen, "
    "Handschrift oder komplexen Tabellen — kann dennoch nicht zugesichert werden. Markdown "
    "kann bestimmte Layoutmerkmale technisch nicht abbilden; die JSON-Ausgabe ist "
    "strukturtreuer. Ergebnisse sind vor einer Weiterverwendung zu prüfen.",
    "terms.7.h": "7. Sperrung",
    "terms.7.p": "Konten, die den Betrieb gefährden oder gegen diese Bedingungen "
    "verstoßen, können ohne Vorankündigung deaktiviert werden.",
    "terms.8.h": "8. Haftung",
    "terms.8.p": "Die Haftung richtet sich nach den gesetzlichen Vorschriften. Für einen "
    "kostenlos bereitgestellten Dienst wird — soweit gesetzlich zulässig — nur bei Vorsatz "
    "und grober Fahrlässigkeit gehaftet. Die Haftung für Schäden aus der Verletzung des "
    "Lebens, des Körpers oder der Gesundheit bleibt unberührt.",

    "licenses.title": "Open-Source-Lizenzen — {product}",
    "licenses.description": "Liste der eingesetzten Open-Source-Komponenten von {product} "
    "mit Version, Lizenz und Urheberrechtsvermerk.",
    "licenses.h1": "Open-Source-Lizenzen",
    "licenses.intro": "{product} setzt freie Software ein. Nachfolgend die eingesetzten "
    "Komponenten mit Version, Lizenz und Urheberrechtsvermerk. {product} ist ein "
    "eigenständiger Dienst und steht in keiner Verbindung zu den Urhebern dieser "
    "Komponenten.",
    "licenses.missing": "Die Lizenzübersicht konnte nicht geladen werden.",

    # ---------------------------------------------------------- Fehlermeldungen
    "error.unsupported_type": "Dieses Dateiformat wird nicht unterstützt. Möglich sind: "
    "{list}.",
    "error.type_mismatch": "Der Inhalt der Datei passt nicht zur Dateiendung. Bitte lade "
    "die Originaldatei hoch.",
    "error.empty_file": "Die Datei ist leer.",
    "error.file_too_large": "Die Datei ist größer als erlaubt.",
    "error.too_many_files": "Du hast zu viele Dateien auf einmal ausgewählt.",
    "error.too_many_pages": "Das Dokument hat mehr Seiten als erlaubt.",
    "error.queue_full": "Deine Warteschlange ist voll. Warte, bis die laufenden "
    "Konvertierungen fertig sind.",
    "error.hourly_limit": "Du hast das Stundenkontingent erreicht. Bitte später noch "
    "einmal.",
    "error.daily_limit": "Du hast das Tageskontingent erreicht. Morgen geht es weiter.",
    "error.pages_limit": "Du hast das Seitenkontingent für heute erreicht.",
    "error.volume_limit": "Du hast das Datenvolumen für heute erreicht.",
    "error.server_busy": "Gerade sind sehr viele Konvertierungen unterwegs. Bitte versuche "
    "es in ein paar Minuten noch einmal.",
    "error.timeout": "Die Verarbeitung hat zu lange gedauert und wurde abgebrochen.",
    "error.conversion_failed": "Das Dokument konnte nicht gelesen werden. Möglicherweise "
    "ist es beschädigt oder passwortgeschützt.",
    "error.engine_unreachable": "Die Verarbeitung ist gerade nicht verfügbar. Der Auftrag "
    "bleibt in der Warteschlange.",
    "error.engine_error": "Bei der Verarbeitung ist ein Fehler aufgetreten.",
    "error.unsupported": "Dieses Dokument konnte nicht verarbeitet werden.",
    "error.no_files": "Es wurde keine Datei ausgewählt.",
    "error.encrypted_pdf": "Diese PDF ist passwortgeschützt und kann nicht gelesen werden.",
    "error.generic": "Es ist ein Fehler aufgetreten. Bitte versuche es noch einmal.",
    "error.rate_limited": "Zu viele Anfragen. Bitte kurz warten.",
    "error.upload_too_large": "Der Upload ist zu groß.",
    "error.form_expired": "Das Formular ist abgelaufen. Bitte lade die Seite neu.",
    "error.not_found": "Diese Seite gibt es nicht.",
    "error.unexpected": "Es ist ein unerwarteter Fehler aufgetreten. Bitte versuche es "
    "erneut.",
    "error.login_required": "Bitte melde dich an.",
    "error.file_missing": "Diese Datei gibt es nicht.",
    "error.address_missing": "Diese Adresse gibt es nicht.",
    "error.request_too_large": "Die Anfrage ist zu gross.",
    "error.register_flood": "Zu viele Registrierungen von dieser Verbindung. Bitte später.",
    "error.email_invalid": "Bitte gib eine gültige E-Mail-Adresse an.",
    "error.password_mismatch": "Die beiden Passwörter stimmen nicht überein.",
    "error.password_short": "Das Passwort braucht mindestens {min} Zeichen.",
    "error.password_long": "Das Passwort ist zu lang.",
    "error.password_blank": "Das Passwort darf nicht nur aus Leerzeichen bestehen.",
    "error.accept_required": "Bitte bestätige die Nutzungsbedingungen und die "
    "Datenschutzhinweise.",
    "error.verify_flood_ip": "Zu viele Anfragen von dieser Verbindung. Bitte später.",
    "error.verify_flood_mail": "Diese Adresse hat schon mehrere Mails erhalten. Bitte "
    "warte eine Stunde.",
    "error.login_wrong": "E-Mail-Adresse oder Passwort stimmt nicht.",
    "error.account_disabled": "Dieses Konto ist deaktiviert.",
    "error.email_unverified": "Bitte bestätige zuerst deine E-Mail-Adresse über den Link, "
    "den wir dir geschickt haben. Keine Mail bekommen? Unter „Bestätigungsmail erneut "
    "senden“ schicken wir sie neu.",
    "error.login_flood": "Zu viele Anmeldeversuche. Bitte warte 15 Minuten und versuche es "
    "erneut.",
    "error.forgot_flood": "Zu viele Anfragen. Bitte später noch einmal.",
    "error.reset_link_dead": "Dieser Link ist abgelaufen oder wurde bereits benutzt.",
    "error.job_missing": "Dieser Auftrag existiert nicht.",
    "error.format_missing": "Dieses Format gibt es nicht.",
    "error.result_gone": "Das Ergebnis ist nicht (mehr) verfügbar.",
    "error.image_missing": "Dieses Bild gibt es nicht.",
    "error.image_gone": "Das Bild ist nicht mehr verfügbar.",
    "error.zip_empty": "Es wurden keine Ergebnisse ausgewählt.",
    "error.zip_nothing": "Es gibt keine fertigen Ergebnisse zum Herunterladen.",
    "error.password_current_wrong": "Das aktuelle Passwort stimmt nicht.",
    "error.password_new_mismatch": "Die beiden neuen Passwörter stimmen nicht überein.",
    "error.delete_confirm": "Zur Bestätigung muss LÖSCHEN eingegeben werden.",
    "error.admin_self": "Das eigene Konto kann hier nicht deaktiviert werden.",
    "error.max_size_hint": "Erlaubt sind {mb} MB.",
    "error.pages_hint": "Diese hat {count}, erlaubt sind {max}.",
    "error.rejected_file": "„{name}“: {reason}",
    "error.passthrough": "{text}",

    # -------------------------------------------------------------- Hinweise
    "info.verify_sent.h": "Mail ist unterwegs",
    "info.verify_sent.p": "Falls die Adresse zu einem noch unbestätigten Konto gehört, "
    "haben wir einen neuen Bestätigungslink geschickt. Er gilt 24 Stunden. Nichts da? "
    "Bitte auch im Spam-Ordner nachsehen.",
    "info.verify_dead.h": "Link ungültig",
    "info.verify_dead.p": "Dieser Bestätigungslink ist abgelaufen oder wurde bereits "
    "benutzt.",
    "info.verified.h": "E-Mail bestätigt",
    "info.verified.p": "Deine Adresse ist bestätigt. Du kannst dich jetzt anmelden.",
    "info.forgot_sent.h": "E-Mail unterwegs",
    "info.forgot_sent.p": "Falls es zu dieser Adresse ein Konto gibt, ist eine E-Mail mit "
    "einem Link zum Zurücksetzen unterwegs. Der Link gilt eine Stunde.",
    "info.password_changed.h": "Passwort geändert",
    "info.password_changed.p": "Du kannst dich jetzt mit dem neuen Passwort anmelden.",

    # ---------------------------------------------------------------- E-Mails
    "mail.verify.subject": "{product}: E-Mail-Adresse bestätigen",
    "mail.verify.body": """Hallo,

bitte bestätige deine E-Mail-Adresse für {product}:

{link}

Der Link ist 24 Stunden gültig. Wenn du dich nicht registriert hast,
ignoriere diese Nachricht einfach — es passiert dann nichts weiter.
""",
    "mail.reset.subject": "{product}: Passwort zurücksetzen",
    "mail.reset.body": """Hallo,

über diesen Link kannst du ein neues Passwort setzen:

{link}

Der Link ist 1 Stunde gültig und funktioniert nur einmal.
Wenn du das nicht angefordert hast, ignoriere diese Nachricht —
dein bisheriges Passwort bleibt unverändert gültig.
""",

    # ------------------------------------------------------- Texte im Ergebnis
    "result.links.h": "Verweise im Dokument",
    "result.links.intro": "Diese Verweise liegen in der PDF als anklickbare Verknuepfungen "
    "vor und tauchen im Fliesstext nicht auf.",
    "result.links.page": "Seite {page}",
    "result.repeated.h": "Wiederkehrende Seitenelemente",
    "result.repeated.intro": "Dieser Text steht in der Vorlage auf nahezu jeder Seite "
    "(Kopf- oder Fusszeile, Wasserzeichen). Er ist hier einmal aufgefuehrt statt auf jeder "
    "Seite wiederholt. Die JSON-Ausgabe enthaelt ihn unveraendert an jeder Fundstelle.",
    "note.image_lowres": "Auf dieser Vorlage ist die Schrift nur etwa {height} Bildpunkte "
    "hoch{size}. Für eine sichere Texterkennung sollten es mindestens {min} sein. Einzelne "
    "Zeichen können deshalb falsch gelesen werden. Am besten die Vorlage noch einmal näher "
    "heran und mit voller Kameraauflösung aufnehmen.",
    "note.image_lowres.size": " ({width} × {height} Bildpunkte)",
    "note.pdf_lowres": "Dieses PDF enthält gescannte Seiten mit {width} × {height} "
    "Bildpunkten — etwa {dpi} Punkte je Zoll, empfohlen sind {min}. Einzelne Zeichen "
    "können deshalb falsch gelesen werden. Am besten mit mindestens 300 Punkten je Zoll "
    "neu einscannen.",
    "note.units.one": "Eine Zelle in einer Einheiten-Spalte ergibt keine bekannte Einheit",
    "note.units.many": "{count} Zellen in Einheiten-Spalten ergeben keine bekannte Einheit",
    "note.units.tail": "{lead} — vermutlich hat die Texterkennung sie falsch gelesen. Die "
    "Werte stehen unverändert im Ergebnis und sind unten einzeln aufgeführt; korrigiert "
    "wird nichts, weil das Raten wäre.",
    "note.file.h": "Hinweis zur Vorlage",
    "note.file.cells": "Auffällige Zellen (unverändert übernommen):",
    "note.file.line": "- {place}, Zeile \"{row}\", Spalte \"{column}\": gelesen als "
    "\"{value}\"",
    "note.file.page": "Seite {page}",
    "note.file.table": "Tabelle",
    "note.file.unnamed": "ohne Bezeichnung",

    # ---------------------------------------------------------- Browser-Texte
    "js.new": "neu",
    "js.since": "seit {value}",
    "js.pages.one": "{count} Seite",
    "js.pages.many": "{count} Seiten",
    "js.minutes": "{min} min {sec} s",
    "js.seconds": "{value} s",
    "js.usage_active": "{active} in Arbeit, {queued} wartend",
    "js.rejected.one": "Eine Datei wurde nicht angenommen:",
    "js.rejected.many": "Einige Dateien wurden nicht angenommen:",
    "js.uploading": "Wird hochgeladen ...",
    "js.checking": "Hochgeladen — wird geprüft ...",
    "js.submit": "Konvertierung starten",
    "js.uploaded.one": "1 Datei hochgeladen. Die Umwandlung läuft — der Auftrag steht "
    "unten in der Liste.",
    "js.uploaded.many": "{count} Dateien hochgeladen. Die Umwandlung läuft — die Aufträge "
    "stehen unten in der Liste.",
    "js.upload_rejected": "Der Upload wurde abgelehnt.",
    "js.connection_lost": "Die Verbindung wurde unterbrochen. Bitte erneut versuchen.",
    "js.progress_aria": "Fortschritt des Uploads",
    "js.ahead.one": "1 Auftrag davor",
    "js.ahead.many": "{count} Aufträge davor",
    "js.ahead.next": "als Nächstes an der Reihe",
    "js.usage": "Heute {jobs}/{jobs_max} Konvertierungen · {pages}/{pages_max} Seiten",
    "js.status.queued": "In Warteschlange",
    "js.status.processing": "Wird verarbeitet",
    "js.status.done": "Fertig",
    "js.status.error": "Fehler",
    "js.note.lowres": "Vorlage grob aufgelöst — einzelne Zeichen können falsch gelesen "
    "werden.",
    "js.view": "Ansehen",
    "js.download_md": "Markdown herunterladen: {name}",
    "js.download_json": "JSON herunterladen: {name}",
    "js.delete_aria": "Auftrag löschen: {name}",
    "js.delete_title": "Auftrag löschen",
    "js.delete_confirm": "Diesen Auftrag mit allen Ergebnissen endgültig löschen?",
    "js.empty": "Noch nichts konvertiert. Lade oben eine Datei hoch — das Ergebnis "
    "erscheint hier.",
    "js.empty.1": "Datei auswählen oder in das Feld oben ziehen.",
    "js.empty.2": "Auf „Konvertierung starten“ tippen.",
    "js.empty.3": "Fertige Aufträge erscheinen hier mit Markdown- und JSON-Download.",
    "js.copied": "Markdown in die Zwischenablage kopiert.",
    "js.copy_failed": "Kopieren hat nicht geklappt. Bitte den Text markieren und manuell "
    "kopieren.",
}
