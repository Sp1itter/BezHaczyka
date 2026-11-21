-- Modul 1: okresowa aktualizacja, rejestr KNF, findings, change_events, widok raportu.
-- bge-m3 daje wektory 1024-wymiarowe. Zmiana modelu = zmiana wymiaru.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE cases
    ADD COLUMN IF NOT EXISTS first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS last_seen_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS seen_count        INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS content_hash      TEXT,
    ADD COLUMN IF NOT EXISTS gone_at           TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS entity_resolution JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS embedding         vector(1024),
    ADD COLUMN IF NOT EXISTS simhash           TEXT;

CREATE INDEX IF NOT EXISTS idx_cases_last_seen ON cases (last_seen_at);

CREATE TABLE IF NOT EXISTS authorized_entities (
    knf_id           TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    normalized_name  TEXT NOT NULL,
    type             TEXT,
    country          TEXT,
    register         TEXT,
    aliases          TEXT[] NOT NULL DEFAULT '{}',
    domains          TEXT[] NOT NULL DEFAULT '{}',
    handles          TEXT[] NOT NULL DEFAULT '{}',
    source_url       TEXT,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_authorized_entities_norm ON authorized_entities (normalized_name);

-- documents: AdDocument w ksztalcie kontraktu, czytany przez services/api (dashboard).
-- Dawniej w infra/init.sql. Analyzer (ANALYZER_STORE=db) wypelnia go migawka dokumentu
-- przy zapisie findingu (store.save_finding); API zapisuje tu przez POST /documents.
-- id == cases.case_id dla tego samego materialu.
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
    embedding     vector(1024),
    simhash       TEXT,
    scope         JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- ivfflat na pustej tabeli dziala; po zaladowaniu korpusu warto REINDEX.
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- document_id = cases.case_id (analyzer, Modul 1) albo documents.id (POST /findings w API);
-- dla tego samego materialu to ten sam UUID. Bez klucza obcego, bo zapisuja tu obie sciezki.
CREATE TABLE IF NOT EXISTS findings (
    id                UUID PRIMARY KEY,
    document_id       UUID NOT NULL,
    primary_module    INTEGER,          -- NULL dozwolone (R4)
    modules           INTEGER[] NOT NULL DEFAULT '{}',
    -- routing.reason to zdanie po polsku pokazywane nadzorcy - nie wolno go gubic.
    routing           JSONB,
    risk_score        DOUBLE PRECISION,
    risk_level        TEXT,             -- low | medium | high
    -- rule_results w calosci: panel kalibracji przelicza flagi po stronie klienta.
    rule_results      JSONB,
    entities          JSONB,
    knn_score         DOUBLE PRECISION,
    status            TEXT NOT NULL DEFAULT 'new',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- AdDocument w chwili analizy, potrzebny do detekcji zmian.
    document_snapshot JSONB
);

CREATE INDEX IF NOT EXISTS idx_findings_risk_level ON findings (risk_level);
CREATE INDEX IF NOT EXISTS idx_findings_created_at ON findings (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_findings_document_id ON findings (document_id);

CREATE TABLE IF NOT EXISTS change_events (
    id                   UUID PRIMARY KEY,
    document_id          UUID REFERENCES cases(case_id) ON DELETE CASCADE,
    kind                 TEXT NOT NULL,
    detected_at          TIMESTAMPTZ NOT NULL,
    previous_finding_id  UUID,
    current_finding_id   UUID,
    rule_diff            JSONB,
    similarity           JSONB,
    risk_level_from      TEXT,
    risk_level_to        TEXT,
    summary              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_change_events_document ON change_events (document_id);
CREATE INDEX IF NOT EXISTS idx_change_events_detected ON change_events (detected_at DESC);

CREATE OR REPLACE VIEW module1_report AS
SELECT
    c.case_id,
    c.source,
    c.url,
    c.title,
    LEFT(t.body, 1000)                                  AS tresc,
    COALESCE(c.entity_resolution->>'publisher_name', c.author_name) AS advertiser_name,
    c.author_id                                         AS advertiser_handle,
    c.author_url                                        AS advertiser_url,
    c.entity_resolution->>'publisher_relation'          AS relation,
    (c.entity_resolution->>'disclosure_found')::boolean AS disclosure_found,
    c.entity_resolution->>'affiliate_link'              AS affiliate_link,
    c.entity_resolution->>'firm_name_in_ad'             AS firm_name_in_ad,
    c.entity_resolution->>'registry_knf_id'             AS firm_knf_id,
    c.entity_resolution->>'registry_official_name'      AS firm_official_name,
    (c.entity_resolution->>'firm_is_authorized')::boolean AS firm_is_authorized,
    ae.type                                             AS firm_type,
    ae.country                                          AS firm_country,
    c.first_seen_at,
    c.last_seen_at,
    c.seen_count,
    c.gone_at,
    c.status,
    f.risk_level,
    f.risk_score,
    f.primary_module,
    f.modules,
    f.routing->>'reason'                                AS routing_reason
FROM cases c
LEFT JOIN authorized_entities ae ON ae.knf_id = c.entity_resolution->>'registry_knf_id'
LEFT JOIN LATERAL (
    SELECT body FROM case_content
    WHERE case_id = c.case_id AND kind IN ('text', 'description')
    ORDER BY (kind = 'text') DESC, seq
    LIMIT 1
) t ON TRUE
LEFT JOIN LATERAL (
    SELECT risk_level, risk_score, primary_module, modules, routing
    FROM findings
    WHERE document_id = c.case_id
    ORDER BY created_at DESC
    LIMIT 1
) f ON TRUE
WHERE c.source IN ('facebook', 'youtube', 'www')
  AND (COALESCE((c.entity_resolution->>'mentions_authorized_firm')::boolean, false)
       OR c.entity_resolution->>'publisher_relation' = 'third_party');
