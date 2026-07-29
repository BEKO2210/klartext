-- Fundstellen der Qualitaetspruefung als Liste, zusaetzlich zum zusammen-
-- fassenden Hinweistext. Enthaelt Seite, Zeilenbezeichnung, Spalte und den
-- unveraenderten Wert aus der Texterkennung.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS quality_findings jsonb;

-- Welche Erkennungs-Engine den Auftrag bearbeitet hat. Grundlage fuer einen
-- spaeteren Vergleich mehrerer Engines und eine Auswahl nach Dokumenttyp.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ocr_engine text;
