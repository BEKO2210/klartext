-- Sprache des Auftrags. Die Hinweise zur Vorlage und die Zusatzabschnitte im
-- Markdown entstehen erst im Worker; ohne diese Spalte wuesste er nicht, in
-- welcher Sprache die Person den Auftrag eingestellt hat, und wuerde deutsche
-- Saetze in ein englisches Ergebnis schreiben.
--
-- Bestandsauftraege sind auf Deutsch entstanden, deshalb 'de' als Vorgabe fuer
-- vorhandene Zeilen. Neue Auftraege setzen den Wert immer selbst.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS lang TEXT NOT NULL DEFAULT 'de';
