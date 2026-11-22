-- Ustawienia panelu nadzorcy (services/api), np. prog alertow z kalibracji (klucz alert_threshold).
-- Pula numerow osoby C (023-025), plan sprintu finalowego par. 6.
CREATE TABLE IF NOT EXISTS app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by TEXT
);
