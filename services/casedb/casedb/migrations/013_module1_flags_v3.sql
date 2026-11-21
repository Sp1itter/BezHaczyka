-- Raport Modulu 1 v3: cofniete_zezwolenie tylko dla rejestru cofniete_zezwolenia
-- (inactive_reason); zakonczona_dzialalnosc (dane historyczne) jako osobna flaga na koncu.

DROP VIEW IF EXISTS module1_report;
CREATE VIEW module1_report AS
WITH base AS (
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
        f.routing->>'reason'                                AS routing_reason,
        (c.entity_resolution->>'firm_license_active')::boolean AS firm_license_active,
        (c.entity_resolution->>'affiliate_without_disclosure')::boolean AS affiliate_without_disclosure,
        c.entity_resolution->>'inactive_reason'             AS inactive_reason,
        (SELECT a.uri FROM case_assets a
          WHERE a.case_id = c.case_id AND a.kind = 'screenshot'
          ORDER BY a.id LIMIT 1)                            AS screenshot_uri,
        CASE WHEN btrim(COALESCE(t.body, '')) = '' THEN NULL
             ELSE md5(lower(regexp_replace(left(t.body, 300), '\s+', ' ', 'g'))) END AS campaign_key
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
           OR c.entity_resolution->>'publisher_relation' = 'third_party')
)
SELECT
    b.case_id,
    b.source,
    b.url,
    b.title,
    b.tresc,
    b.advertiser_name,
    b.advertiser_handle,
    b.advertiser_url,
    b.relation,
    b.disclosure_found,
    b.affiliate_link,
    b.firm_name_in_ad,
    b.firm_knf_id,
    b.firm_official_name,
    b.firm_is_authorized,
    b.firm_type,
    b.firm_country,
    b.first_seen_at,
    b.last_seen_at,
    b.seen_count,
    b.gone_at,
    b.status,
    b.risk_level,
    b.risk_score,
    b.primary_module,
    b.modules,
    b.routing_reason,
    b.firm_license_active,
    b.affiliate_without_disclosure,
    b.screenshot_uri,
    b.campaign_key,
    CASE WHEN b.campaign_key IS NULL THEN NULL
         ELSE count(*) OVER (PARTITION BY b.campaign_key) END AS campaign_size,
    array_remove(ARRAY[
        CASE WHEN b.relation = 'third_party' AND NOT COALESCE(b.disclosure_found, false)
             THEN 'podmiot_trzeci_bez_ujawnienia' END,
        CASE WHEN COALESCE(b.affiliate_without_disclosure, false)
             THEN 'link_afiliacyjny_bez_ujawnienia' END,
        CASE WHEN b.inactive_reason = 'cofniete_zezwolenie' THEN 'cofniete_zezwolenie' END,
        CASE WHEN b.firm_country IS NOT NULL AND b.firm_country <> 'PL'
             THEN 'firma_zagraniczna' END,
        CASE WHEN b.inactive_reason = 'zakonczona_dzialalnosc' THEN 'zakonczona_dzialalnosc' END
    ], NULL)::text[]                                       AS m1_flags
FROM base b;
