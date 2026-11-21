-- Wspolna baza przypadkow (case) dla scraperow YouTube, Facebook i WWW.
-- Metadane: cases. Tresc: case_content (SQL) + case_assets (URI do S3/SeaweedFS lub link).
-- Wyniki AI: ai_results (JSONB, nowy model/zadanie nie wymaga migracji).
-- case_id = uuid5(NAMESPACE_URL, kanoniczny URL) - ten sam schemat co AdDocument.id
-- w scraperze FB, wiec case_id == documents.id dla tego samego materialu.

CREATE TABLE IF NOT EXISTS cases (
    case_id         UUID PRIMARY KEY,
    source          TEXT NOT NULL CHECK (source IN ('youtube', 'facebook', 'www')),
    source_item_id  TEXT NOT NULL,
    url             TEXT NOT NULL,
    title           TEXT,
    author_name     TEXT,
    author_id       TEXT,
    author_url      TEXT,
    lang            TEXT,
    published_at    TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    status          TEXT NOT NULL DEFAULT 'new'
                    CHECK (status IN ('new', 'queued', 'processing', 'done', 'error', 'skipped')),
    assigned_to     TEXT,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,
    extra           JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_item_id)
);

CREATE TABLE IF NOT EXISTS case_content (
    id       BIGSERIAL PRIMARY KEY,
    case_id  UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    kind     TEXT NOT NULL,          -- title | description | text | transcript | clip | comment | evidence
    seq      INTEGER NOT NULL DEFAULT 0,
    body     TEXT NOT NULL DEFAULT '',
    start_s  DOUBLE PRECISION,
    end_s    DOUBLE PRECISION,
    url      TEXT,
    extra    JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (case_id, kind, seq)
);

CREATE TABLE IF NOT EXISTS case_assets (
    id       BIGSERIAL PRIMARY KEY,
    case_id  UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    kind     TEXT NOT NULL,          -- link | html | screenshot | video | audio | image
    label    TEXT,
    uri      TEXT NOT NULL,          -- s3://bucket/key albo https://...
    mime     TEXT,
    sha256   TEXT,
    bytes    BIGINT,
    extra    JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (case_id, uri)
);

CREATE TABLE IF NOT EXISTS ai_results (
    id          BIGSERIAL PRIMARY KEY,
    case_id     UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    task        TEXT NOT NULL,
    model       TEXT NOT NULL,
    version     TEXT NOT NULL DEFAULT '',
    endpoint    TEXT,
    label       TEXT,
    score       DOUBLE PRECISION,
    result      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (case_id, task, model, version)
);

CREATE INDEX IF NOT EXISTS idx_cases_status_created ON cases (status, created_at);
CREATE INDEX IF NOT EXISTS idx_cases_source ON cases (source);
CREATE INDEX IF NOT EXISTS idx_case_content_case ON case_content (case_id);
CREATE INDEX IF NOT EXISTS idx_case_assets_case ON case_assets (case_id);
CREATE INDEX IF NOT EXISTS idx_ai_results_case ON ai_results (case_id);
CREATE INDEX IF NOT EXISTS idx_ai_results_task ON ai_results (task);
