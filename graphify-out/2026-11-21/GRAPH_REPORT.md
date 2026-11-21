# Graph Report - osoba-c-modul3  (2026-11-21)

## Corpus Check
- 161 files · ~1,118,258 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 13, .gz 8, .example 3)

## Summary
- 2347 nodes · 5855 edges · 128 communities (100 shown, 28 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 580 edges (avg confidence: 0.93)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `fc871686`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InvestWatch Platform Architecture
- Development Documentation and Skills
- test_registry.py
- InvestWatch Challenge Description
- test_stt.py
- test_worker.py
- router.py
- test_evaluate.py
- classify_similarity
- risk_score
- InvestWatch — dokument projektowy (design doc)
- evaluate_batch_1
- classify_scope
- _file
- test_rules_hybrid.py
- analyzer/contracts.py
- Verdict
- worker.py
- test_scaling_runtime.py
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- test_contracts.py
- AdDocument
- FindingDetail.jsx
- test_preconditions.py
- Integracja serwisów — kto wywołuje kogo
- LocalBlobStore
- meta_json.py
- api/contracts.py
- test_facebook_contract.py
- OllamaClient
- analyze
- jobs.py
- SqlStore
- Verdict
- AdDocument
- pathlib
- check_compliance.py
- test_lang_consistency.py
- FacebookAdsSource
- _doc
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- DemoTests
- test_facebook_rules.py
- demo.py
- gpu
- quote_is_verifiable
- main.py
- scaling.py
- feed_fold_evidence
- risk_level
- Enum
- test_pool.py
- pytest
- test_api.py
- QueueState
- is_flagged
- EntityResolution
- infra - punkt startowy dla Osoby C (API + dashboard)
- api/store.py
- health.py
- casedb/store.py
- test_casedb.py
- Harmonogram i orkiestracja — dokument projektowy
- json
- services
- analyzer
- test_scoring.py
- scraper: FacebookAdsSource (Meta Ad Library)
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- healthcheck
- postgres
- test_gold_set.py
- _doc
- is_language
- facebook_rules.py
- collect_ads_from_dom
- Harmonogram Modułu 1 — plan implementacji
- api
- export.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- analyzer
- _default_spawn
- knn_score
- browser
- Zbior zloty (gold set)
- seaweedfs
- AlertHub
- db.py
- test_demo.py
- TestGranicyKontraktu
- QuietLogger
- json
- valkey
- web
- scan
- scraper/tests/test_contracts.py
- Rule
- TestInterfejsRule
- InvestWatch
- FeedFoldEvidence
- AGENTS.md - services/casedb
- test_casedb.py
- 5. Do zrobienia
- parse_args
- analyzer — Moduły Analityczne / AI
- casedb
- 8. Logika modułów
- 9. Scoring, threshold i metryki
- 4. Rozważone podejścia
- T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)
- volumes
- TranscriptSegment
- web (osoba C)

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 107 edges
2. `Verdict` - 106 edges
3. `RuleResult` - 76 edges
4. `OllamaClient` - 55 edges
5. `analyze()` - 55 edges
6. `FacebookAdsSource` - 49 edges
7. `AnalyzerConfig` - 46 edges
8. `EntityResolution` - 46 edges
9. `Engine` - 36 edges
10. `EvidenceKind` - 35 edges

## Surprising Connections (you probably didn't know these)
- `Jak wagi jury przekładają się na decyzje projektowe` --references--> `Source`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/scraper/sources/base.py
- `Osoba C` --references--> `PostgresStore`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/api/api/store.py
- `Osoba A — `services/scraper` (zmergowane, PR #2)` --references--> `FacebookAdsSource`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/scraper/sources/facebook.py
- `Pluginowalne źródła` --references--> `FacebookAdsSource`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/scraper/sources/facebook.py
- `Jak dodac pozycje` --references--> `risk_score()`  [INFERRED]
  fixtures/gold/README.md → services/analyzer/analyzer/scoring.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (128 total, 28 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.13
Nodes (18): build_config(), coverage_report(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _all_pass_handler(), _client() (+10 more)

### Community 4 - "test_stt.py"
Cohesion: 0.06
Nodes (43): Transcript, TranscriptSegment, _default_transcriber(), run(), _first_match_start(), normalize_text(), rate_anomaly(), risk_timing() (+35 more)

### Community 5 - "test_worker.py"
Cohesion: 0.16
Nodes (17): health_payload(), handle_job(), _api(), handler(), _llm(), test_api_error_on_get_returns_none(), test_api_error_on_post_returns_none(), test_get_document_raises_api_error() (+9 more)

### Community 6 - "router.py"
Cohesion: 0.10
Nodes (16): Relation, Routing, _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _matches_any(), route() (+8 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 9 - "risk_score"
Cohesion: 0.16
Nodes (5): risk_score(), _rule(), TestEskalacjiPoNajciezszymNaruszeniu, TestNotApplicableNieWchodziDoMianownika, TestRiskScore

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.11
Nodes (17): 10. Pozyskiwanie danych i bezpieczeństwo demo, 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 7. Mapowanie 18 reguł na silniki (+9 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.13
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.09
Nodes (8): classify_scope(), _find_any(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania, TestZwykleInstrumenty

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_rules_hybrid.py"
Cohesion: 0.05
Nodes (37): _deep_merge(), get_threshold(), load_thresholds(), TextNode, ViewportProbe, assess_rule_3(), _result(), _center_y() (+29 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.12
Nodes (17): AdvertiserRef, BBox, Embedding, Entities, Finding, InvestmentFirmRef, Publisher, RegistryMatch (+9 more)

### Community 16 - "Verdict"
Cohesion: 0.18
Nodes (20): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _normalize(), _boom(), _client(), wrapped(), _doc() (+12 more)

### Community 17 - "worker.py"
Cohesion: 0.10
Nodes (12): Co A wrzuca do kolejki, ApiClient, ApiError, _check_local(), serve(), analyze_document(), _build_det_results(), _build_resolution() (+4 more)

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.13
Nodes (14): Co zmieniło się po review zespołu (wersja 2), Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate, Rejestr ryzyk, T+10.5 — 22:00–01:30 · Dopięcie i polish (3,5 h), T+14 — 01:30–02:00 · Commit, push, tag (+6 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (26): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, legal_basis, max_distance_px, max_gap_seconds, max_offset_chars (+18 more)

### Community 22 - "test_contracts.py"
Cohesion: 0.11
Nodes (10): Engine, Evidence, EvidenceKind, _na(), _result(), _crashed_rule_result(), RuleBase, assess_rule_10() (+2 more)

### Community 23 - "AdDocument"
Cohesion: 0.19
Nodes (4): _doc(), _rule(), _runner(), TestAnalyze

### Community 24 - "FindingDetail.jsx"
Cohesion: 0.06
Nodes (62): react, react-dom, recharts, vite, @vitejs/plugin-react, dependencies, react@18.3.1, react-dom@18.3.1 (+54 more)

### Community 25 - "test_preconditions.py"
Cohesion: 0.08
Nodes (18): normalize(), _first_match_offset(), risk_sentences(), split_sentences(), _words(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax() (+10 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.17
Nodes (10): Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, api (osoba C), Endpointy (+2 more)

### Community 28 - "LocalBlobStore"
Cohesion: 0.10
Nodes (7): download_direct(), download_ytdlp(), probe_duration(), main(), Source, SourceBlocked, SourceError

### Community 29 - "meta_json.py"
Cohesion: 0.10
Nodes (33): doc_from_node(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards(), clean_text(), find_ad_nodes() (+25 more)

### Community 30 - "api/contracts.py"
Cohesion: 0.10
Nodes (26): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+18 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.09
Nodes (13): ad_id_from_url(), canonical_ad_url(), doc(), source(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_identity_and_url(), test_login_redirect_blocked_and_overlays_removed_without_clicks() (+5 more)

### Community 32 - "OllamaClient"
Cohesion: 0.08
Nodes (11): embed_document_text(), normalize(), tokenize(), OllamaClient, TestEmbedDocumentText, handler(), TestNormalizacjaITokeny, TestPowtarzalnosciModelu (+3 more)

### Community 33 - "analyze"
Cohesion: 0.14
Nodes (10): analyze(), AnalyzerConfig, _ensure_transcript(), _ensure_vector_representation(), _det(), _doc(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults (+2 more)

### Community 34 - "jobs.py"
Cohesion: 0.13
Nodes (10): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, NodeCache, SeenSet (+2 more)

### Community 35 - "SqlStore"
Cohesion: 0.13
Nodes (3): _iso(), PostgresStore, SqlStore

### Community 36 - "Verdict"
Cohesion: 0.06
Nodes (57): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 6: Klasyfikacja zdarzenia, Zadanie 7: Brama idempotencji przed kolejką GPU, _basis(), _cosine(), detect_change(), event() (+49 more)

### Community 37 - "AdDocument"
Cohesion: 0.10
Nodes (15): AdDocument, RuleResult, LlmError, load_prompt(), rule_3_runner(), evaluate_batch_2(), evaluate_batch_3(), evaluate_batch_4() (+7 more)

### Community 38 - "pathlib"
Cohesion: 0.10
Nodes (7): FacebookConfig, BlobStore, LocalBlobStore, S3BlobStore, doc(), main(), pick_ad()

### Community 39 - "check_compliance.py"
Cohesion: 0.27
Nodes (12): check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file(), _lines() (+4 more)

### Community 40 - "test_lang_consistency.py"
Cohesion: 0.18
Nodes (5): detect_language(), _client(), _doc(), TestDetectLanguage, TestOverrideWBatch2

### Community 42 - "_doc"
Cohesion: 0.14
Nodes (7): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), _doc(), TestKorpusuNaTejMaszynie, TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.16
Nodes (12): AdvertiserRef, Embedding, Entities, Finding, InvestmentFirmRef, MediaItem, Publisher, RegistryMatch (+4 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.15
Nodes (8): CircuitBreaker, RateLimiter, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures(), test_rate_limiter_spaces_requests(), test_success_resets_failures()

### Community 46 - "DemoTests"
Cohesion: 0.31
Nodes (3): analyze(), DemoTests, segments()

### Community 47 - "test_facebook_rules.py"
Cohesion: 0.16
Nodes (17): BBox, RenderProbe, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score() (+9 more)

### Community 48 - "demo.py"
Cohesion: 0.20
Nodes (9): candidates(), evidence(), metadata(), normalize(), run(), signals_in(), transcript(), request() (+1 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "quote_is_verifiable"
Cohesion: 0.27
Nodes (3): _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable

### Community 51 - "main.py"
Cohesion: 0.12
Nodes (14): alert_payload(), coverage(), create_app(), get_document(), get_finding(), health(), list_findings(), patch_finding() (+6 more)

### Community 52 - "scaling.py"
Cohesion: 0.18
Nodes (9): _connection(), _int(), _parse(), QueuePolicy, _rq_backlog_reader(), _read(), _rq_worker_counter(), _count() (+1 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.18
Nodes (13): feed_fold_evidence(), platform_rule_override(), test_feed_fold_hybrid_evidence_from_document_text(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "risk_level"
Cohesion: 0.13
Nodes (13): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego, 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły, InvestWatch — stan projektu (+5 more)

### Community 55 - "Enum"
Cohesion: 0.31
Nodes (6): Engine, EvidenceKind, Relation, RiskLevel, ScopeStatus, Verdict

### Community 56 - "test_pool.py"
Cohesion: 0.11
Nodes (16): Zadanie 4: Executor `pool`, DryRunExecutor, PoolExecutor, ScalingConfig, ScalingDecision, _d(), FakeSpawn, FakeWorker (+8 more)

### Community 57 - "pytest"
Cohesion: 0.20
Nodes (13): load_scaling_config(), ScalingConfigError, validate_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+5 more)

### Community 58 - "test_api.py"
Cohesion: 0.21
Nodes (18): client(), load(), seeded(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless(), test_document_upsert_returns_200_second_time(), test_embedding_survives_roundtrip(), test_finding_for_unknown_document_409() (+10 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "is_flagged"
Cohesion: 0.33
Nodes (3): is_flagged(), Co już jest (gotowe i przetestowane), TestIsFlagged

### Community 61 - "EntityResolution"
Cohesion: 0.14
Nodes (5): EntityResolution, _fake_transcriber(), TestKolejnosciEtapow, TestWywolaniaTranskrypcji, licznik()

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.14
Nodes (9): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth (+1 more)

### Community 63 - "api/store.py"
Cohesion: 0.13
Nodes (11): AdDocument, Finding, main(), seed(), document_row(), finding_row(), open_store(), _row_to_document() (+3 more)

### Community 64 - "health.py"
Cohesion: 0.08
Nodes (12): _Handler, _no_states(), _scaling_response(), _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json() (+4 more)

### Community 65 - "casedb/store.py"
Cohesion: 0.18
Nodes (9): add_asset(), Asset, Case, claim(), save_ai_result(), save_case(), set_columns(), set_status() (+1 more)

### Community 66 - "test_casedb.py"
Cohesion: 0.24
Nodes (7): from_ad_document(), from_youtube(), youtube_video_id(), case_id_for(), Content, test_facebook_mapping_keeps_document_id_and_drops_embedding(), test_youtube_mapping_is_stable()

### Community 67 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.15
Nodes (12): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 6. Idempotencja — warunek, żeby to nie było śmietnikiem (+4 more)

### Community 68 - "json"
Cohesion: 0.33
Nodes (5): load_case(), main(), print_table(), score_one(), update_gold()

### Community 69 - "services"
Cohesion: 0.18
Nodes (10): name, name, networks, investwatch, image, networks, ports, volumes (+2 more)

### Community 70 - "analyzer"
Cohesion: 0.29
Nodes (7): depends_on, depends_on, depends_on, postgres, valkey, condition, condition

### Community 71 - "test_scoring.py"
Cohesion: 0.15
Nodes (6): coverage(), max_breach_severity(), TestCoverage, TestFailedRules, TestMaxBreachSeverity, TestRiskLevel

### Community 72 - "scraper: FacebookAdsSource (Meta Ad Library)"
Cohesion: 0.20
Nodes (6): `.env`, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: FacebookAdsSource (Meta Ad Library), start_background(), Demo INVESTWATCH

### Community 73 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.20
Nodes (10): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba (+2 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 79 - "facebook_rules.py"
Cohesion: 0.40
Nodes (7): Evidence, RuleResult, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.33
Nodes (5): collect_ads_from_dom(), merge_nodes(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram Modułu 1 — plan implementacji"
Cohesion: 0.22
Nodes (8): CZĘŚĆ A — Autoskaler, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera

### Community 82 - "api"
Cohesion: 0.13
Nodes (16): build, build, environment, networks, ports, volumes, context, build (+8 more)

### Community 83 - "export.py"
Cohesion: 0.33
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "analyzer"
Cohesion: 0.25
Nodes (8): env_file, environment, extra_hosts, networks, API_BASE_URL, OLLAMA_BASE_URL, VALKEY_URL, analyzer

### Community 87 - "knn_score"
Cohesion: 0.24
Nodes (6): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h), knn_score(), TestKnnScore

### Community 88 - "browser"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 92 - "db.py"
Cohesion: 0.17
Nodes (6): _load(), main(), _write(), connect(), migrate(), conn()

### Community 93 - "test_demo.py"
Cohesion: 0.18
Nodes (3): find_targets(), host(), make_clips()

### Community 96 - "json"
Cohesion: 0.11
Nodes (10): main(), _load_analyzer(), test_fixtures_validate(), test_schema_identical_with_analyzer(), test_document_matches_frozen_contract(), test_committed_examples_have_no_external_hosts(), test_host_replaced_path_and_params_kept(), test_uppercase_scheme_and_s3_untouched() (+2 more)

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.40
Nodes (5): web, build, depends_on, networks, ports

### Community 99 - "scan"
Cohesion: 0.38
Nodes (5): load_inputs(), main(), save(), scan(), validate_inputs()

### Community 100 - "scraper/tests/test_contracts.py"
Cohesion: 0.17
Nodes (4): AdDocument, test_contract_copy_matches_analyzer(), test_example_validates(), test_facebook_golden_examples()

### Community 101 - "Rule"
Cohesion: 0.20
Nodes (9): 5. Architektura, Układ repozytorium, A — scraper + reguły DET, B — analyzer, C — api + web, Podział roli, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle) (+1 more)

### Community 103 - "InvestWatch"
Cohesion: 0.33
Nodes (5): Instalacja Dockera na Windows, InvestWatch, Struktura, Uruchomienie, Wymagania — bez tego projekt nie wystartuje

### Community 105 - "AGENTS.md - services/casedb"
Cohesion: 0.18
Nodes (9): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+1 more)

### Community 107 - "5. Do zrobienia"
Cohesion: 0.40
Nodes (5): 5. Do zrobienia, Nasze (Osoba B) — Moduł 1, harmonogram, Osoba A, Osoba C, Wspólne, blok dokumentacyjny

### Community 115 - "analyzer — Moduły Analityczne / AI"
Cohesion: 0.25
Nodes (7): analyzer — Moduły Analityczne / AI, Brama zakresu — najważniejsza decyzja domenowa, Co trzeba zrobić dalej (kolejność ma znaczenie), Quick start, Regeneracja przykładów kontraktów, Weryfikacja cytatu — zabezpieczenie przed halucynacją, Zasady, których trzymamy się w tym serwisie

### Community 117 - "casedb"
Cohesion: 0.29
Nodes (6): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Testy, Wymagania

### Community 119 - "8. Logika modułów"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 120 - "9. Scoring, threshold i metryki"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 122 - "4. Rozważone podejścia"
Cohesion: 0.50
Nodes (4): 4. Rozważone podejścia, Podejście A — „wszystko do LLM-a", Podejście B — „wszystko na regułach deterministycznych", Podejście C — hybryda warstwowa **[WYBRANE]**

### Community 123 - "T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### Community 124 - "volumes"
Cohesion: 0.50
Nodes (4): volumes, pgdata, seaweeddata, valkeydata

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 789 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `test_stt.py`, `evaluate_batch_1`, `test_rules_hybrid.py`, `analyzer/contracts.py`, `Verdict`, `worker.py`, `_client`, `test_contracts.py`, `AdDocument`, `test_preconditions.py`, `LocalBlobStore`, `meta_json.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `Verdict`, `pathlib`, `test_lang_consistency.py`, `FacebookAdsSource`, `_doc`, `test_facebook_rules.py`, `EntityResolution`, `json`, `_doc`, `facebook_rules.py`, `TestGranicyKontraktu`, `json`, `scraper/tests/test_contracts.py`, `Rule`, `TestInterfejsRule`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 53 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13118279569892474 - nodes in this community are weakly interconnected._
- **Why does `RuleResult` connect `AdDocument` to `test_registry.py`, `risk_score`, `evaluate_batch_1`, `test_rules_hybrid.py`, `analyzer/contracts.py`, `Verdict`, `worker.py`, `test_contracts.py`, `AdDocument`, `test_preconditions.py`, `OllamaClient`, `analyze`, `Verdict`, `test_facebook_rules.py`, `risk_level`, `json`, `test_scoring.py`, `facebook_rules.py`, `scraper/tests/test_contracts.py`, `Rule`, `TestInterfejsRule`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05502392344497608 - nodes in this community are weakly interconnected._