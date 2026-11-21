-- Snapshot wykazow KNF "Firmy inwestycyjne i Agenci firm inwestycyjnych" (tools/knf_snapshot.py).
-- Jeden wiersz = podmiot z jednego wykazu. Ladowanie: python -m casedb load-knf (zastepuje snapshot).
CREATE TABLE IF NOT EXISTS knf_entities (
    id            BIGSERIAL PRIMARY KEY,
    register      TEXT NOT NULL,          -- np. domy_maklerskie, zfi_bez_oddzialu, agenci_osoby_fizyczne
    category      TEXT NOT NULL,          -- firma_inwestycyjna | zagraniczna_firma_inwestycyjna | agent
    active        BOOLEAN NOT NULL,       -- false: cofniete zezwolenie / dane historyczne
    name          TEXT NOT NULL,
    name_key      TEXT NOT NULL,          -- znormalizowana nazwa (casedb.knf.name_key)
    former_names  TEXT[] NOT NULL DEFAULT '{}',
    former_keys   TEXT[] NOT NULL DEFAULT '{}',
    fields        JSONB NOT NULL DEFAULT '{}'::jsonb,  -- wszystkie pola karty KNF
    source_url    TEXT NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS knf_entities_name_key ON knf_entities (name_key);
CREATE INDEX IF NOT EXISTS knf_entities_former_keys ON knf_entities USING GIN (former_keys);
CREATE INDEX IF NOT EXISTS knf_entities_register ON knf_entities (register);
