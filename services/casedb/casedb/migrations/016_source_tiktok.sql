-- Nowe zrodlo: tiktok (szkielet, services/scraper/sources/tiktok.py).
-- Rozszerza CHECK z 001_cases.sql; nazwa ograniczenia nadana domyslnie przez Postgresa.
ALTER TABLE cases DROP CONSTRAINT IF EXISTS cases_source_check;
ALTER TABLE cases ADD CONSTRAINT cases_source_check
    CHECK (source IN ('youtube', 'facebook', 'www', 'tiktok'));
