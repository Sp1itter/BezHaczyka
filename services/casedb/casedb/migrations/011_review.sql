-- Praca analityka nad findingiem: kto sie nim zajmuje i jaka jest ocena czlowieka.
-- Model tylko zaweza prace; potwierdzenie (review_*) i przypisanie (assignee) robi czlowiek.
-- review_label = feedback do kalibracji/uczenia (TP, FP, bledny podmiot, ...), lista w services/api/api/review.py.
ALTER TABLE findings
    ADD COLUMN IF NOT EXISTS assignee       TEXT,
    ADD COLUMN IF NOT EXISTS assigned_by    TEXT,         -- human | ai
    ADD COLUMN IF NOT EXISTS assigned_at    TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS review_verdict TEXT,         -- confirmed | dismissed
    ADD COLUMN IF NOT EXISTS review_label   TEXT,
    ADD COLUMN IF NOT EXISTS review_note    TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_by    TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_at    TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_findings_assignee ON findings (assignee);
CREATE INDEX IF NOT EXISTS idx_findings_review_label ON findings (review_label);

-- Historia pracy nad findingiem (os zdarzen w panelu, audyt decyzji).
CREATE TABLE IF NOT EXISTS finding_events (
    id          BIGSERIAL PRIMARY KEY,
    finding_id  UUID NOT NULL,
    at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor       TEXT,
    action      TEXT NOT NULL,                  -- status | assign | review
    detail      JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_finding_events_finding ON finding_events (finding_id, at);
