-- Layouttreue: wie viele Tabellen das Dokument hatte und wie viele davon
-- verbundene Zellen tragen. Nur Zahlen, keine Inhalte.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS table_count INT NOT NULL DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS merged_table_count INT NOT NULL DEFAULT 0;
