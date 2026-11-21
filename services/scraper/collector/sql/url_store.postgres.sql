-- url_store: kandydaci poziomu 1 (collector) dla floty poziomu 2.
-- Zrodlo prawdy dla migracji casedb (002_url_store.sql, wlasciciel: Rodz).
-- Idempotentne: mozna uruchamiac wielokrotnie.

CREATE TABLE IF NOT EXISTS url_store (
    id            BIGSERIAL PRIMARY KEY,
    source_type   TEXT NOT NULL CHECK (source_type IN ('facebook', 'youtube', 'web', 'synthetic')),
    external_id   TEXT NOT NULL,
    url           TEXT NOT NULL,
    query_tag     TEXT,
    publisher_key TEXT,
    creative_key  TEXT,
    landing_key   TEXT,
    priority      REAL NOT NULL DEFAULT 0,
    signals       JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
    state         TEXT NOT NULL DEFAULT 'new' CHECK (state IN
                  ('new', 'queued', 'in_progress', 'fetched', 'rejected', 'quarantined', 'merged', 'error', 'done')),
    merged_into   BIGINT REFERENCES url_store (id),
    document_id   TEXT,
    attempts      INTEGER NOT NULL DEFAULT 0,
    last_error    TEXT,
    locked_until  TIMESTAMPTZ,
    locked_by     TEXT,
    first_seen    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen     TIMESTAMPTZ NOT NULL DEFAULT now(),
    seen_count    INTEGER NOT NULL DEFAULT 1,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_type, external_id)
);

CREATE INDEX IF NOT EXISTS ix_url_ready    ON url_store (priority DESC, first_seen) WHERE state = 'queued';
CREATE INDEX IF NOT EXISTS ix_url_state    ON url_store (state);
CREATE INDEX IF NOT EXISTS ix_url_creative ON url_store (creative_key);
CREATE INDEX IF NOT EXISTS ix_url_landing  ON url_store (landing_key);
CREATE INDEX IF NOT EXISTS ix_url_lease    ON url_store (locked_until) WHERE state = 'in_progress';
