-- Bilder aus dem Dokument als eigene Dateien.
-- Eigene Tabelle statt files.role='image', weil files eine Zeile je Rolle erlaubt
-- und ein Dokument beliebig viele Bilder enthalten kann.

CREATE TABLE IF NOT EXISTS job_images (
    id          BIGSERIAL PRIMARY KEY,
    job_id      BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,
    page_no     INTEGER,
    storage_key TEXT NOT NULL,
    mime_type   TEXT NOT NULL,
    size_bytes  BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, seq)
);
CREATE INDEX IF NOT EXISTS job_images_job_idx ON job_images(job_id);
CREATE INDEX IF NOT EXISTS job_images_user_idx ON job_images(user_id);

-- Zähler für die Auftragsübersicht, damit die Liste keine Unterabfrage braucht.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS image_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS link_count  INTEGER NOT NULL DEFAULT 0;
