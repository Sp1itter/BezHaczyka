-- Pochodzenie wpisu rejestru: curated = CSV z aliasami/domenami, knf = wyprowadzone ze snapshotu.
ALTER TABLE authorized_entities
    ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'curated',
    ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT true;
