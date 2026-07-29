-- Hinweis auf eine zu grob aufgeloeste Vorlage. Wird beim Umwandeln ermittelt
-- und dem Benutzer beim Ergebnis angezeigt: zu kleine Bilder fuehren zu
-- Lesefehlern, die sich nachtraeglich nicht reparieren lassen.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS quality_note text;
