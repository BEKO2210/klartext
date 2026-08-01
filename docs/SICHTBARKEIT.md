# Klartext sichtbar machen — Anleitung und Rechtsrahmen

Stand 01.08.2026. Was der Server schon selbst tut, was du einmalig einrichten
musst, und was rechtlich zu beachten ist. Alles am Handy machbar.

---

## Was bereits automatisch läuft (nichts zu tun)

| Baustein | Zustand |
|---|---|
| Sitemap mit hreflang | `/sitemap.xml`, 12 Adressen, beide Sprachen |
| robots.txt | Suche erlaubt, KI-Training verboten, KI-Zitieren erlaubt (deine Cloudflare-Einstellung vom 01.08.) |
| IndexNow | Schlüssel liegt auf der Domain; `scripts/indexnow.sh` hat alle 12 Adressen gemeldet (HTTP 202). **Nach jedem inhaltlichen Deploy einmal ausführen.** |
| llms.txt | `/llms.txt` — Inhaltsverzeichnis für KI-Werkzeuge |
| Schema.org | WebApplication + FAQPage, beide Sprachen |
| Vergleichsseite | `/compare` und `/de/vergleich` — fängt „pandoc alternative"-Fragen |

---

## 1. Microsoft: Bing Webmaster Tools (~10 Minuten)

Warum zuerst: **ChatGPT und Copilot beantworten aus dem Bing-Index.** Ohne
Bing-Aufnahme keine ChatGPT-Verweise, egal wie gut die Seite ist.

1. **bing.com/webmasters** öffnen → mit Microsoft-Konto anmelden
   (jedes private reicht, auch ein frisches).
2. „Add your site" → `https://klartext.it-handwerk-stuttgart.de` eintragen.
3. Verifizierung: Methode **DNS (CNAME/TXT)** wählen. Bing zeigt dir einen
   Wert wie `verify.bing.com` mit einer Kennung.
   - **Sag mir einfach den angezeigten Wert** — ich setze den DNS-Eintrag
     über die Cloudflare-API in Sekunden. Alternativ selbst: Cloudflare →
     it-handwerk-stuttgart.de → DNS → Eintrag hinzufügen, exakt wie angezeigt.
4. Zurück in Bing „Verify" drücken.
5. Danach: **Sitemaps** → `https://klartext.it-handwerk-stuttgart.de/sitemap.xml`
   eintragen.
6. Fertig. IndexNow ist damit automatisch verknüpft — künftige Meldungen
   vom Server landen direkt in deinem Bing-Konto sichtbar.

**Nicht nötig:** Bing Places (das ist für Läden mit Adresse), bezahlte
Optionen, „Import from Google".

## 2. Google: Search Console (~10 Minuten)

Bringt keine Rankings, aber Sicht: welche Suchbegriffe, welche Seiten
indexiert, welche Fehler.

1. **search.google.com/search-console** → mit Google-Konto anmelden.
2. Property-Typ **„Domain"** wählen (nicht „URL-Präfix") →
   `klartext.it-handwerk-stuttgart.de` eintragen.
3. Google zeigt einen **TXT-Eintrag** (`google-site-verification=…`).
   - Auch hier: **Wert mir geben**, ich setze ihn per Cloudflare-API.
4. „Bestätigen" drücken (nach DNS-Setzen 1–2 Minuten warten).
5. **Sitemaps** → `sitemap.xml` eintragen.
6. Einmalig: „URL-Prüfung" → Startseite eingeben → „Indexierung beantragen".
   Dasselbe für `/de` und `/compare`. Mehr nicht — der Rest kommt über
   die Sitemap.

**Nicht nötig:** Google Analytics (du hast Plausible — datenschutzfreundlicher),
Google Ads, „AdSense verknüpfen".

## 3. Danach: einmal prüfen (mache ich)

Sobald beide verifiziert sind, sag Bescheid — ich prüfe dann von hier:
Indexierungsstand, Crawling-Fehler, und ob IndexNow in Bing ankommt.

---

## Rechtsrahmen (Deutschland) — was gilt und was wir deshalb so gebaut haben

**Vergleichsseite (§ 6 UWG, vergleichende Werbung).** Erlaubt, wenn sachlich,
nachprüfbar, nicht herabsetzend, keine Verwechslungsgefahr. Deshalb:
- nur Eigenschaften laut öffentlicher Dokumentation (OCR ja/nein, wo Daten
  laufen, Installation, Preis) — jede Aussage nachprüfbar
- **keine erfundenen Messwerte über fremde Werkzeuge**: unser 98%-Benchmark
  misst nur OCR-Engines *innerhalb* von Klartext und sagt das auch dazu
- jedes Werkzeug bekommt ein ehrliches „wann es die bessere Wahl ist"
- Stand-Datum + Korrekturangebot auf der Seite (entkräftet Irreführungsvorwurf)
- Markennennung (pandoc, Docling, Marker) ist als beschreibende Nennung
  zulässig; keine fremden Logos verwenden — haben wir nicht

**Werbeaussagen generell (§ 5 UWG, Irreführung).** Die Linie, die wir fahren
und die du beibehalten solltest: **nur behaupten, was gemessen oder belegbar
ist.** „98 % OCR-Treffer" steht nur mit Methodik daneben. Formulierungen wie
„der beste Konverter" oder „100 % genau" wären abmahnfähig — gibt es auf der
Seite nicht und sollte es nie geben.

**Impressum/Datenschutz:** vorhanden und verlinkt — Pflichtgrundlage für
alles Weitere, nichts zu tun.

---

## Sollten wir werben? Meine Empfehlung: **bezahlt nein, organisch ja**

**Gegen bezahlte Anzeigen (Google Ads etc.) sprechen drei Dinge:**
1. Klartext verdient nichts — jeder Werbe-Euro ist weg, ohne Rückweg.
2. Die Kapazität ist real begrenzt (~55 Dokumente/Stunde auf dem Heimserver).
   Erfolgreiche Werbung würde den Dienst für alle langsam machen — du würdest
   dafür bezahlen, dein eigenes Produkt schlechter zu machen.
3. Der Product-Hunt-Schub + KI-Verweise + Suche erreichen dieselbe Zielgruppe
   kostenlos.

**Stattdessen, kostenlos und wirksam (Reihenfolge = Priorität):**
1. **AlternativeTo.net** — Klartext als Alternative zu pandoc/Cloud-Konvertern
   eintragen. KI-Antworten zitieren AlternativeTo oft direkt. Konto anlegen,
   „Add application", Fakten aus der Vergleichsseite übernehmen.
2. **Reddit/Foren** (r/selfhosted, r/datacurator, r/de_EDV) — als Maker posten
   ist erlaubt und üblich, **aber offenlegen** („Ich habe das gebaut").
   Verdeckt posten wäre Schleichwerbung (§ 5a UWG) und fliegt ohnehin auf.
3. **Hacker News „Show HN"** — gleiche Regel: offen als Maker.
4. **GitHub** — falls du das Repo öffentlich machst: README mit Link zur
   Live-Seite; viele KI-Antworten zitieren GitHub-READMEs. (Deine Entscheidung,
   Repo ist bisher privat.)

**Realistische Erwartung:** Bing-Aufnahme Tage bis wenige Wochen, erste
KI-Verweise frühestens danach. Der PH-Launchtag mit 2.800 Besuchern ist genau
das Signal, das diese Systeme gewichten — der Zeitpunkt ist gut.

---

## Merkzettel: nach jedem inhaltlichen Deploy

```
cd ~/klartext && ./scripts/indexnow.sh
```

Eine Zeile, meldet alle Seiten neu an Bing & Co.
