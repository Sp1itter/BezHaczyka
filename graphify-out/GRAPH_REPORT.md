# Graph Report - osoba-c-modul3  (2026-11-21)

## Corpus Check
- 160 files · ~1,117,673 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 13, .gz 8, .example 3)

## Summary
- 2340 nodes · 5850 edges · 129 communities (105 shown, 24 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 580 edges (avg confidence: 0.93)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `9394666a`
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
- embeddings.py
- risk_score
- InvestWatch — dokument projektowy (design doc)
- evaluate_batch_1
- classify_scope
- _file
- test_config.py
- contracts.py
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
- assess_rule_3
- test_rules_hybrid.py
- test_lang_consistency.py
- FacebookAdsSource
- _doc
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- DemoTests
- test_facebook_rules.py
- math
- gpu
- test_scaling_endpoint.py
- main.py
- scaling.py
- feed_fold_evidence
- InvestWatch — stan projektu
- max_breach_severity
- test_pool.py
- pytest
- test_api.py
- QueueState
- is_flagged
- pipeline.py
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
- risk_level
- db.py
- test_demo.py
- TestGranicyKontraktu
- run
- pathlib
- valkey
- web
- scan
- scraper/tests/test_contracts.py
- Rule
- ApiClient
- FeedFoldEvidence
- AGENTS.md - services/casedb
- main
- NodeCache
- parse_args
- analyzer — Moduły Analityczne / AI
- health_payload
- casedb
- 10. Pozyskiwanie danych i bezpieczeństwo demo
- 8. Logika modułów
- 9. Scoring, threshold i metryki
- 1. Co działa i jest zweryfikowane
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
7. `EntityResolution` - 46 edges
8. `AnalyzerConfig` - 46 edges
9. `Engine` - 36 edges
10. `EvidenceKind` - 35 edges

## Surprising Connections (you probably didn't know these)
- `Jak dodac pozycje` --references--> `risk_score()`  [INFERRED]
  fixtures/gold/README.md → services/analyzer/analyzer/scoring.py
- `4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py
- `6. Do udoskonalenia — uszeregowane po wpływie na demo` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py
- `Osoba C` --references--> `PostgresStore`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/api/api/store.py
- `Jak wagi jury przekładają się na decyzje projektowe` --references--> `Source`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/scraper/sources/base.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (129 total, 24 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.11
Nodes (20): rule_3_runner(), build_config(), coverage_report(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _with_hybrid() (+12 more)

### Community 4 - "test_stt.py"
Cohesion: 0.08
Nodes (40): Transcript, TranscriptSegment, _default_transcriber(), run(), _first_match_start(), normalize_text(), rate_anomaly(), risk_timing() (+32 more)

### Community 5 - "test_worker.py"
Cohesion: 0.24
Nodes (12): handle_job(), _api(), test_api_error_on_get_returns_none(), test_api_error_on_post_returns_none(), test_get_document_raises_api_error(), test_happy_path_end_to_end(), test_invalid_document_returns_none(), test_payload_without_document_id() (+4 more)

### Community 6 - "router.py"
Cohesion: 0.06
Nodes (20): Relation, Routing, _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _matches_any(), normalize() (+12 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "embeddings.py"
Cohesion: 0.10
Nodes (9): Embedding, classify_similarity(), embed_document_text(), normalize(), tokenize(), TestClassifySimilarity, TestEmbedDocumentText, handler() (+1 more)

### Community 9 - "risk_score"
Cohesion: 0.25
Nodes (4): risk_score(), _rule(), TestNotApplicableNieWchodziDoMianownika, TestRiskScore

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.15
Nodes (12): 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 7. Mapowanie 18 reguł na silniki, Anty-cele (to by oznaczało porażkę, nawet gdyby „działało") (+4 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.13
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.05
Nodes (26): classify_scope(), _find_any(), _normalize(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania (+18 more)

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.12
Nodes (18): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+10 more)

### Community 15 - "contracts.py"
Cohesion: 0.21
Nodes (10): AdvertiserRef, BBox, Entities, InvestmentFirmRef, Publisher, RegistryMatch, RenderProbe, Scope (+2 more)

### Community 16 - "Verdict"
Cohesion: 0.12
Nodes (22): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable, _boom(), _client() (+14 more)

### Community 17 - "worker.py"
Cohesion: 0.14
Nodes (8): Finding, serve(), _build_det_results(), _build_resolution(), main(), _start_health_server(), run(), test_finding_moze_nalezec_do_wielu_modulow()

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
Cohesion: 0.08
Nodes (17): Engine, Evidence, EvidenceKind, RuleResult, _na(), _result(), _crashed_rule_result(), _result() (+9 more)

### Community 23 - "AdDocument"
Cohesion: 0.20
Nodes (5): analyze(), _doc(), _rule(), _runner(), TestAnalyze

### Community 24 - "FindingDetail.jsx"
Cohesion: 0.06
Nodes (62): react, react-dom, recharts, vite, @vitejs/plugin-react, dependencies, react@18.3.1, react-dom@18.3.1 (+54 more)

### Community 25 - "test_preconditions.py"
Cohesion: 0.10
Nodes (13): evaluate_batch_4(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_historical_performance(), mentions_tax(), _client_returning_fail(), _client_that_must_not_be_called() (+5 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.13
Nodes (12): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, analyze_document() (+4 more)

### Community 28 - "LocalBlobStore"
Cohesion: 0.10
Nodes (8): download_direct(), download_ytdlp(), probe_duration(), main(), FacebookConfig, LocalBlobStore, main(), pick_ad()

### Community 29 - "meta_json.py"
Cohesion: 0.08
Nodes (38): test_przyklad_waliduje_sie_przeciw_modelowi(), doc_from_node(), Publisher, ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html() (+30 more)

### Community 30 - "api/contracts.py"
Cohesion: 0.10
Nodes (26): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+18 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.09
Nodes (13): Source, canonical_ad_url(), doc(), source(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_document_matches_frozen_contract(), test_feed_fold_hybrid_evidence_from_document_text() (+5 more)

### Community 32 - "OllamaClient"
Cohesion: 0.14
Nodes (6): OllamaClient, TestPowtarzalnosciModelu, check_embeddings(), main(), make_doc(), main()

### Community 33 - "analyze"
Cohesion: 0.13
Nodes (7): AnalyzerConfig, EntityResolution, _det(), TestPrzeplywuDetResults, TestRegulyR4, TestWarstwyWektorowej, TestWywolaniaTranskrypcji

### Community 34 - "jobs.py"
Cohesion: 0.12
Nodes (11): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, SeenSet, blob_store_from_env() (+3 more)

### Community 35 - "SqlStore"
Cohesion: 0.12
Nodes (5): AdDocument, _iso(), PostgresStore, _row_to_document(), SqlStore

### Community 36 - "Verdict"
Cohesion: 0.07
Nodes (56): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 6: Klasyfikacja zdarzenia, Zadanie 7: Brama idempotencji przed kolejką GPU, _basis(), _cosine(), detect_change(), event() (+48 more)

### Community 37 - "AdDocument"
Cohesion: 0.11
Nodes (10): AdDocument, LlmError, load_prompt(), evaluate_batch_2(), evaluate_batch_3(), _all_not_applicable(), _build_result(), evaluate_batch() (+2 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.15
Nodes (7): assess_rule_3(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestWarunkowosci

### Community 39 - "test_rules_hybrid.py"
Cohesion: 0.14
Nodes (12): TextNode, ViewportProbe, _center_y(), _first_match_offset(), _matches(), measure_geometry(), measure_proximity(), measure_text() (+4 more)

### Community 40 - "test_lang_consistency.py"
Cohesion: 0.13
Nodes (8): detect_language(), risk_sentences(), _words(), _client(), _doc(), TestDetectLanguage, TestOverrideWBatch2, TestRiskSentences

### Community 41 - "FacebookAdsSource"
Cohesion: 0.12
Nodes (5): MediaItem, SourceBlocked, SourceError, FacebookAdsSource, doc()

### Community 42 - "_doc"
Cohesion: 0.17
Nodes (6): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), _doc(), TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.13
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.14
Nodes (15): AdvertiserRef, Embedding, Engine, Entities, EvidenceKind, InvestmentFirmRef, MediaItem, RegistryMatch (+7 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.15
Nodes (8): CircuitBreaker, RateLimiter, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures(), test_rate_limiter_spaces_requests(), test_success_resets_failures()

### Community 46 - "DemoTests"
Cohesion: 0.31
Nodes (3): analyze(), DemoTests, segments()

### Community 47 - "test_facebook_rules.py"
Cohesion: 0.16
Nodes (17): BBox, RenderProbe, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score() (+9 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.21
Nodes (8): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), test_nieznana_sciezka_nadal_daje_404()

### Community 51 - "main.py"
Cohesion: 0.09
Nodes (15): alert_payload(), AlertHub, coverage(), create_app(), get_document(), get_finding(), health(), list_findings() (+7 more)

### Community 52 - "scaling.py"
Cohesion: 0.18
Nodes (9): _connection(), _int(), _parse(), QueuePolicy, _rq_backlog_reader(), _read(), _rq_worker_counter(), _count() (+1 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.19
Nodes (12): feed_fold_evidence(), platform_rule_override(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched(), test_quote_is_not_cut_at_abbreviation() (+4 more)

### Community 54 - "InvestWatch — stan projektu"
Cohesion: 0.15
Nodes (12): 2. Pomiary na żywym modelu, 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego, 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły, InvestWatch — stan projektu (+4 more)

### Community 56 - "test_pool.py"
Cohesion: 0.11
Nodes (16): Zadanie 4: Executor `pool`, DryRunExecutor, PoolExecutor, ScalingConfig, ScalingDecision, _d(), FakeSpawn, FakeWorker (+8 more)

### Community 57 - "pytest"
Cohesion: 0.15
Nodes (15): load_scaling_config(), ScalingConfigError, validate_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+7 more)

### Community 58 - "test_api.py"
Cohesion: 0.20
Nodes (18): client(), load(), seeded(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless(), test_document_upsert_returns_200_second_time(), test_embedding_survives_roundtrip(), test_finding_for_unknown_document_409() (+10 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "is_flagged"
Cohesion: 0.33
Nodes (3): is_flagged(), Co już jest (gotowe i przetestowane), TestIsFlagged

### Community 61 - "pipeline.py"
Cohesion: 0.11
Nodes (8): ScopeStatus, _ensure_transcript(), _ensure_vector_representation(), TestBramyZakresuNaRealnejReklamie, _fake_transcriber(), TestKolejnosciEtapow, TestKorpusuNaTejMaszynie, licznik()

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.14
Nodes (9): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth (+1 more)

### Community 63 - "api/store.py"
Cohesion: 0.15
Nodes (9): Finding, main(), seed(), document_row(), finding_row(), open_store(), SqliteStore, UpsertResult (+1 more)

### Community 64 - "health.py"
Cohesion: 0.13
Nodes (4): _Handler, _no_states(), _scaling_response(), TestZaleznosci

### Community 65 - "casedb/store.py"
Cohesion: 0.18
Nodes (9): add_asset(), Asset, Case, claim(), save_ai_result(), save_case(), set_columns(), set_status() (+1 more)

### Community 66 - "test_casedb.py"
Cohesion: 0.22
Nodes (8): from_ad_document(), from_youtube(), youtube_video_id(), case_id_for(), Content, test_claim_is_exclusive(), test_facebook_mapping_keeps_document_id_and_drops_embedding(), test_youtube_mapping_is_stable()

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
Cohesion: 0.18
Nodes (5): coverage(), failed_rules(), TestCoverage, TestFailedRules, TestRiskLevel

### Community 72 - "scraper: FacebookAdsSource (Meta Ad Library)"
Cohesion: 0.20
Nodes (6): `.env`, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: FacebookAdsSource (Meta Ad Library), start_background(), Demo INVESTWATCH

### Community 73 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.22
Nodes (9): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6. Kontrakty danych (ZAMROŻONE o 12:30) (+1 more)

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
Cohesion: 0.29
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "analyzer"
Cohesion: 0.25
Nodes (8): env_file, environment, extra_hosts, networks, API_BASE_URL, OLLAMA_BASE_URL, VALKEY_URL, analyzer

### Community 87 - "knn_score"
Cohesion: 0.21
Nodes (7): 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba, A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h), knn_score(), TestKnnScore

### Community 88 - "browser"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "risk_level"
Cohesion: 0.22
Nodes (3): 5. Typy zdarzeń, risk_level(), TestEskalacjiPoNajciezszymNaruszeniu

### Community 92 - "db.py"
Cohesion: 0.21
Nodes (3): connect(), migrate(), conn()

### Community 93 - "test_demo.py"
Cohesion: 0.20
Nodes (6): evidence(), find_targets(), host(), make_clips(), normalize(), signals_in()

### Community 95 - "run"
Cohesion: 0.15
Nodes (6): candidates(), metadata(), QuietLogger, run(), worker(), ydl_options()

### Community 96 - "pathlib"
Cohesion: 0.21
Nodes (3): _load_analyzer(), test_fixtures_validate(), test_schema_identical_with_analyzer()

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.40
Nodes (5): web, build, depends_on, networks, ports

### Community 99 - "scan"
Cohesion: 0.26
Nodes (5): load_inputs(), main(), save(), scan(), validate_inputs()

### Community 100 - "scraper/tests/test_contracts.py"
Cohesion: 0.18
Nodes (4): AdDocument, Finding, Scope, test_example_validates()

### Community 101 - "Rule"
Cohesion: 0.20
Nodes (9): 5. Architektura, Układ repozytorium, A — scraper + reguły DET, B — analyzer, C — api + web, Podział roli, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle) (+1 more)

### Community 103 - "ApiClient"
Cohesion: 0.29
Nodes (4): ApiClient, ApiError, _check_local(), test_external_base_url_rejected()

### Community 105 - "AGENTS.md - services/casedb"
Cohesion: 0.18
Nodes (9): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+1 more)

### Community 106 - "main"
Cohesion: 0.27
Nodes (4): _load(), main(), _write(), test_cli_ingest_and_export()

### Community 115 - "analyzer — Moduły Analityczne / AI"
Cohesion: 0.25
Nodes (7): analyzer — Moduły Analityczne / AI, Brama zakresu — najważniejsza decyzja domenowa, Co trzeba zrobić dalej (kolejność ma znaczenie), Quick start, Regeneracja przykładów kontraktów, Weryfikacja cytatu — zabezpieczenie przed halucynacją, Zasady, których trzymamy się w tym serwisie

### Community 116 - "health_payload"
Cohesion: 0.33
Nodes (5): health_payload(), handler(), _llm(), test_health_ollama_down_is_degraded_not_fatal(), test_health_ollama_up()

### Community 117 - "casedb"
Cohesion: 0.29
Nodes (6): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Testy, Wymagania

### Community 118 - "10. Pozyskiwanie danych i bezpieczeństwo demo"
Cohesion: 0.40
Nodes (5): 10. Pozyskiwanie danych i bezpieczeństwo demo, Bezpieczeństwo demo (anty-cel: „demo zależne od wifi"), Cybersec (kryterium oceniane wprost), Kolejka i harmonogram, Pluginowalne źródła

### Community 119 - "8. Logika modułów"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 120 - "9. Scoring, threshold i metryki"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 121 - "1. Co działa i jest zweryfikowane"
Cohesion: 0.50
Nodes (4): 1. Co działa i jest zweryfikowane, Osoba A — `services/scraper` (zmergowane, PR #2), Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`), Osoba C — `services/api`, `services/web`

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 784 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `test_stt.py`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `worker.py`, `_client`, `test_contracts.py`, `AdDocument`, `test_preconditions.py`, `LocalBlobStore`, `meta_json.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `Verdict`, `assess_rule_3`, `test_rules_hybrid.py`, `test_lang_consistency.py`, `FacebookAdsSource`, `_doc`, `test_facebook_rules.py`, `pytest`, `pipeline.py`, `json`, `_doc`, `facebook_rules.py`, `TestGranicyKontraktu`, `Rule`, `ApiClient`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 53 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10810810810810811 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `Verdict` to `test_registry.py`, `risk_score`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `_client`, `test_contracts.py`, `AdDocument`, `test_preconditions.py`, `OllamaClient`, `analyze`, `AdDocument`, `assess_rule_3`, `test_rules_hybrid.py`, `test_lang_consistency.py`, `test_facebook_rules.py`, `max_breach_severity`, `pipeline.py`, `json`, `test_scoring.py`, `facebook_rules.py`, `risk_level`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0822746521476104 - nodes in this community are weakly interconnected._