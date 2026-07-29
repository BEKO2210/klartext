-- KLARTEXT — Initiales Schema
-- Migrationen sind versioniert und werden genau einmal ausgefuehrt (Tabelle schema_migrations).

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    email           TEXT NOT NULL,
    email_norm      TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    is_admin        BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at   TIMESTAMPTZ
);

-- Sessions: nur der SHA-256-Hash des Cookie-Tokens wird gespeichert.
CREATE TABLE IF NOT EXISTS sessions (
    id           BIGSERIAL PRIMARY KEY,
    token_hash   TEXT NOT NULL UNIQUE,
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token   TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user_idx ON sessions(user_id);
CREATE INDEX IF NOT EXISTS sessions_expires_idx ON sessions(expires_at);

-- Einmal-Token fuer E-Mail-Verifizierung und Passwort-Reset (nur Hash gespeichert).
CREATE TABLE IF NOT EXISTS auth_tokens (
    id         BIGSERIAL PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL CHECK (kind IN ('verify_email', 'password_reset')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS auth_tokens_user_idx ON auth_tokens(user_id, kind);

-- Ein Job = eine hochgeladene Datei. Batch-Uploads teilen sich eine batch_id.
CREATE TABLE IF NOT EXISTS jobs (
    id             BIGSERIAL PRIMARY KEY,
    public_id      UUID NOT NULL UNIQUE,
    batch_id       UUID,
    user_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_name  TEXT NOT NULL,
    mime_type      TEXT NOT NULL,
    size_bytes     BIGINT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued', 'processing', 'done', 'error', 'deleted')),
    error_code     TEXT,
    page_count     INTEGER,
    attempts       INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at     TIMESTAMPTZ,
    finished_at    TIMESTAMPTZ,
    duration_ms    INTEGER,
    expires_at     TIMESTAMPTZ NOT NULL,
    purged_at      TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS jobs_user_created_idx ON jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS jobs_queue_idx ON jobs(status, created_at) WHERE status = 'queued';
CREATE INDEX IF NOT EXISTS jobs_expires_idx ON jobs(expires_at) WHERE purged_at IS NULL;

-- Dateien auf der Platte. Interner Name ist zufaellig, nie vom Benutzer beeinflusst.
CREATE TABLE IF NOT EXISTS files (
    id          BIGSERIAL PRIMARY KEY,
    job_id      BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('source', 'markdown', 'json')),
    storage_key TEXT NOT NULL,
    size_bytes  BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, role)
);
CREATE INDEX IF NOT EXISTS files_user_idx ON files(user_id);

-- Rein technische Fair-Use-Zaehler. Kein Billing, keine Tarife.
CREATE TABLE IF NOT EXISTS usage_events (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    jobs        INTEGER NOT NULL DEFAULT 1,
    pages       INTEGER NOT NULL DEFAULT 0,
    bytes       BIGINT NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS usage_user_time_idx ON usage_events(user_id, created_at DESC);

-- Generischer Zaehler fuer Rate-Limits (Login-Versuche, Registrierung, Uploads ...).
CREATE TABLE IF NOT EXISTS rate_limits (
    bucket     TEXT NOT NULL,
    window_at  TIMESTAMPTZ NOT NULL,
    hits       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket, window_at)
);
CREATE INDEX IF NOT EXISTS rate_limits_window_idx ON rate_limits(window_at);

-- Vom Admin zur Laufzeit aenderbare Limits. Fehlt ein Schluessel, gilt der ENV-Wert.
CREATE TABLE IF NOT EXISTS app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Betriebsprotokoll ohne Dokumentinhalte.
CREATE TABLE IF NOT EXISTS audit_log (
    id         BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id    BIGINT,
    action     TEXT NOT NULL,
    detail     TEXT
);
CREATE INDEX IF NOT EXISTS audit_created_idx ON audit_log(created_at DESC);
