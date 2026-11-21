-- Podsumowanie findingu dla nadzorcy (2-3 zdania po polsku) i jego zrodlo:
-- 'llm' (Bielik) albo 'template' (deterministyczny szablon, gdy model niedostepny).
ALTER TABLE findings ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS summary_engine TEXT;
