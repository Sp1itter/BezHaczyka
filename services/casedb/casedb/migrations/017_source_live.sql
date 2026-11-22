-- Nowe zrodla sprintu finalowego (osoba A): www_live (prawdziwy internet, ddgs + curl_cffi),
-- tiktok_ads (TikTok Ad Library, region PL). Rozszerza CHECK z 016_source_tiktok.sql.
ALTER TABLE cases DROP CONSTRAINT IF EXISTS cases_source_check;
ALTER TABLE cases ADD CONSTRAINT cases_source_check
    CHECK (source IN ('youtube', 'facebook', 'www', 'tiktok', 'www_live', 'tiktok_ads'));
