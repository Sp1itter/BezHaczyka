-- Schemat InvestWatch. Odpowiada kontraktom z services/analyzer/analyzer/contracts.py
-- (AdDocument, Finding). Uruchamiany raz, przy pierwszym starcie na pustym wolumenie.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id            UUID PRIMARY KEY,
    source        TEXT NOT NULL,
    url           TEXT NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL,
    publisher     JSONB NOT NULL DEFAULT '{}'::jsonb,
    lang          TEXT NOT NULL DEFAULT 'pl',
    title         TEXT,
    text          TEXT NOT NULL DEFAULT '',
    html_path     TEXT,
    screenshots   JSONB NOT NULL DEFAULT '{}'::jsonb,
    media         JSONB NOT NULL DEFAULT '[]'::jsonb,
    transcript    JSONB,
    render_probe  JSONB,
    -- bge-m3 daje wektory 1024-wymiarowe. Zmiana modelu = zmiana tego wymiaru.
    embedding     vector(1024),
    simhash       TEXT,
    scope         JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS findings (
    id              UUID PRIMARY KEY,
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    primary_module  INTEGER NOT NULL,
    modules         INTEGER[] NOT NULL DEFAULT '{}',
    -- routing.reason to zdanie po polsku POKAZYWANE nadzorcy - nie wolno go gubic.
    routing         JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_score      DOUBLE PRECISION NOT NULL,
    risk_level      TEXT NOT NULL,   -- low | medium | high; "high" = broadcast WebSocket
    -- rule_results trzymamy W CALOSCI (kazda regula: verdict, confidence, severity,
    -- evidence). Panel kalibracji przelicza flagi przy przesuwaniu suwaka PO STRONIE
    -- KLIENTA, bez requestu do modelu. Okrojenie tego pola zabije natychmiastowosc suwaka.
    rule_results    JSONB NOT NULL DEFAULT '[]'::jsonb,
    entities        JSONB NOT NULL DEFAULT '{}'::jsonb,
    knn_score       DOUBLE PRECISION,
    status          TEXT NOT NULL DEFAULT 'new',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS authorized_entities (
    name             TEXT NOT NULL,
    normalized_name  TEXT NOT NULL,
    knf_id           TEXT PRIMARY KEY,
    type             TEXT,
    country          TEXT
);

-- Wyszukiwanie podobnych dokumentow (cosinus). ivfflat wymaga danych do dobrego
-- treningu list; na pustej tabeli dziala, ale warto go odbudowac po zaladowaniu korpusu.
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_findings_risk_level ON findings (risk_level);
CREATE INDEX IF NOT EXISTS idx_findings_created_at ON findings (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_findings_document_id ON findings (document_id);
CREATE INDEX IF NOT EXISTS idx_authorized_entities_norm ON authorized_entities (normalized_name);
