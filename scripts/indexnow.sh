#!/usr/bin/env bash
# Meldet die oeffentlichen Seiten an IndexNow (Bing, Yandex u. a.).
#
# Wann ausfuehren: nach jedem Deploy, der Inhalte aendert. Kostet nichts,
# kein Konto noetig — der Schluessel liegt als /<key>.txt auf der Domain
# (Route in main.py) und beweist nur, dass uns die Domain gehoert.
#
#   ./scripts/indexnow.sh
set -euo pipefail

HOST="klartext.it-handwerk-stuttgart.de"
KEY="83c7219232f501978ffcc4bcdc3a1acb"

# Adressliste direkt aus der Sitemap — dann kann sie nie auseinanderlaufen.
URLS=$(curl -fsS "https://${HOST}/sitemap.xml" | grep -oE '<loc>[^<]+' | sed 's/<loc>//')
[ -n "$URLS" ] || { echo "Sitemap leer — Abbruch." >&2; exit 1; }

LISTE=$(printf '%s\n' "$URLS" | python3 -c 'import json,sys; print(json.dumps([z.strip() for z in sys.stdin if z.strip()]))')

ANTWORT=$(curl -fsS -o /dev/null -w "%{http_code}" -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{\"host\":\"${HOST}\",\"key\":\"${KEY}\",\"urlList\":${LISTE}}")

echo "IndexNow: HTTP ${ANTWORT} für $(printf '%s\n' "$URLS" | wc -l) Adressen"
# 200 = angenommen, 202 = angenommen (Schluessel wird noch geprueft).
case "$ANTWORT" in 200|202) exit 0 ;; *) exit 1 ;; esac
