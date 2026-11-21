# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 123 files · ~1,104,392 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: .gz 8, (none) 5, .example 2)

## Summary
- 1959 nodes · 5029 edges · 111 communities (84 shown, 27 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 574 edges (avg confidence: 0.93)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `3f3fb41a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InvestWatch Platform Architecture
- Development Documentation and Skills
- test_registry.py
- InvestWatch Challenge Description
- test_stt.py
- test_worker.py
- Relation
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
- RenderProbe
- facebook.py
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- test_contracts.py
- transcribe
- TestPolskaOdmiana
- Integracja serwisów — kto wywołuje kogo
- LocalBlobStore
- meta_json.py
- test_preconditions.py
- test_facebook_contract.py
- OllamaClient
- analyze
- jobs.py
- re
- Verdict
- RuleResult
- assess_rule_3
- test_rules_hybrid.py
- test_lang_consistency.py
- FacebookAdsSource
- test_stt_pipeline.py
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- DemoTests
- test_facebook_rules.py
- json
- gpu
- test_scaling_endpoint.py
- parametrize
- load_scaling_config
- feed_fold_evidence
- InvestWatch — stan projektu
- max_breach_severity
- test_pool.py
- FakeWorker
- TestPowtarzalnosciModelu
- QueueState
- test_scoring.py
- risk_level
- infra - punkt startowy dla Osoby C (API + dashboard)
- router.py
- health.py
- cosine
- TranscriptSegment
- 10. Pozyskiwanie danych i bezpieczeństwo demo
- json
- services
- analyzer
- Enum
- scraper: FacebookAdsSource (Meta Ad Library)
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- healthcheck
- postgres
- test_gold_set.py
- _client
- is_language
- facebook_rules.py
- collect_ads_from_dom
- Harmonogram Modułu 1 — plan implementacji
- api
- 4. Rozważone podejścia
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- _default_spawn
- knn_score
- conftest.py
- Zbior zloty (gold set)
- seaweedfs
- TestProgowZKonfiguracji
- 8. Logika modułów
- 9. Scoring, threshold i metryki
- nginx
- valkey
- web
- T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)
- TestZaleznosci
- TranscriptSegment
- FeedFoldEvidence

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 111 edges
2. `Verdict` - 106 edges
3. `RuleResult` - 80 edges
4. `OllamaClient` - 55 edges
5. `analyze()` - 55 edges
6. `FacebookAdsSource` - 48 edges
7. `AnalyzerConfig` - 46 edges
8. `EntityResolution` - 46 edges
9. `Engine` - 36 edges
10. `EvidenceKind` - 35 edges

## Surprising Connections (you probably didn't know these)
- `6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Jak wagi jury przekładają się na decyzje projektowe` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Podejście C — hybryda warstwowa **[WYBRANE]**` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `A — scraper + reguły DET` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-plan-24h.md → services/analyzer/analyzer/contracts.py
- `6.1 `AdDocument` — to, co produkuje scraper` --references--> `AdDocument`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (111 total, 27 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.12
Nodes (18): build_config(), coverage_report(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _all_pass_handler(), _client() (+10 more)

### Community 4 - "test_stt.py"
Cohesion: 0.20
Nodes (20): Transcript, rate_anomaly(), risk_timing(), RiskTiming, test_rate_anomaly_fast_disclaimer(), test_rate_anomaly_single_segment(), test_rate_anomaly_too_few_segments(), test_rate_anomaly_zero_median() (+12 more)

### Community 5 - "test_worker.py"
Cohesion: 0.07
Nodes (28): Co A wrzuca do kolejki, ApiClient, ApiError, _check_local(), health_payload(), serve(), analyze_document(), _build_det_results() (+20 more)

### Community 6 - "Relation"
Cohesion: 0.12
Nodes (11): Relation, Routing, route(), RoutingDecision, RoutingInput, _build_resolution(), _inp(), TestR1WlasnyMaterialFirmy (+3 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "embeddings.py"
Cohesion: 0.14
Nodes (6): classify_similarity(), normalize(), tokenize(), TestClassifySimilarity, TestNormalizacjaITokeny, normalize()

### Community 9 - "risk_score"
Cohesion: 0.22
Nodes (3): risk_score(), TestNotApplicableNieWchodziDoMianownika, TestRiskScore

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.14
Nodes (13): 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 5. Architektura, 7. Mapowanie 18 reguł na silniki (+5 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.09
Nodes (10): evaluate_batch_1(), _normalize_for_match(), quote_is_verifiable(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1 (+2 more)

### Community 12 - "classify_scope"
Cohesion: 0.11
Nodes (8): ScopeStatus, classify_scope(), _find_any(), _normalize(), TestCfdNaKryptoZostajeWZakresie, TestNiepewneIdaDoTriage, TestPozaZakresemTylkoBezOpakowania, TestZwykleInstrumenty

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.13
Nodes (17): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+9 more)

### Community 15 - "contracts.py"
Cohesion: 0.20
Nodes (10): AdvertiserRef, BBox, Embedding, Entities, InvestmentFirmRef, Publisher, RegistryMatch, Scope (+2 more)

### Community 16 - "Verdict"
Cohesion: 0.18
Nodes (19): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _boom(), _client(), wrapped(), _doc(), _ok() (+11 more)

### Community 17 - "RenderProbe"
Cohesion: 0.18
Nodes (11): 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, Co zmieniło się po review zespołu (wersja 2), Podział roli, RenderProbe, analyzer — Moduły Analityczne / AI, Brama zakresu — najważniejsza decyzja domenowa, Co trzeba zrobić dalej (kolejność ma znaczenie), Quick start (+3 more)

### Community 18 - "facebook.py"
Cohesion: 0.16
Nodes (4): Publisher, Source, SourceBlocked, SourceError

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.12
Nodes (16): B — analyzer, C — api + web, Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate, Rejestr ryzyk, T+10.5 — 22:00–01:30 · Dopięcie i polish (3,5 h) (+8 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (26): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, legal_basis, max_distance_px, max_gap_seconds, max_offset_chars (+18 more)

### Community 22 - "test_contracts.py"
Cohesion: 0.09
Nodes (14): Układ repozytorium, A — scraper + reguły DET, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), AdDocument, Evidence, RuleResult, _crashed_rule_result(), rule_3_runner() (+6 more)

### Community 23 - "transcribe"
Cohesion: 0.16
Nodes (13): _default_transcriber(), run(), SttError, transcribe(), test_stt_error_is_runtime_error(), test_transcribe_empty_result(), test_transcribe_passes_through_stt_error(), boom() (+5 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.29
Nodes (6): Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem

### Community 28 - "LocalBlobStore"
Cohesion: 0.13
Nodes (7): download_direct(), download_ytdlp(), probe_duration(), main(), FacebookConfig, LocalBlobStore, doc()

### Community 29 - "meta_json.py"
Cohesion: 0.10
Nodes (35): ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards(), clean_text(), find_ad_nodes() (+27 more)

### Community 30 - "test_preconditions.py"
Cohesion: 0.10
Nodes (14): evaluate_batch_3(), evaluate_batch_4(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_historical_performance(), mentions_tax(), _client_returning_fail() (+6 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.11
Nodes (11): canonical_ad_url(), doc(), source(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_document_matches_frozen_contract(), test_identity_and_url(), test_login_redirect_blocked_and_overlays_removed_without_clicks() (+3 more)

### Community 32 - "OllamaClient"
Cohesion: 0.09
Nodes (11): embed_document_text(), OllamaClient, evaluate_batch_2(), apply_rule_10_override(), _with_hybrid(), TestEmbedDocumentText, handler(), check_embeddings() (+3 more)

### Community 33 - "analyze"
Cohesion: 0.05
Nodes (20): analyze(), AnalyzerConfig, _ensure_transcript(), _ensure_vector_representation(), EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie (+12 more)

### Community 34 - "jobs.py"
Cohesion: 0.08
Nodes (12): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, NodeCache, SeenSet (+4 more)

### Community 35 - "re"
Cohesion: 0.23
Nodes (13): test_committed_examples_have_no_external_hosts(), check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file() (+5 more)

### Community 36 - "Verdict"
Cohesion: 0.06
Nodes (69): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 6: Klasyfikacja zdarzenia, Zadanie 7: Brama idempotencji przed kolejką GPU, 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja (+61 more)

### Community 37 - "RuleResult"
Cohesion: 0.20
Nodes (10): Engine, EvidenceKind, LlmError, load_prompt(), _na(), _result(), _all_not_applicable(), _build_result() (+2 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.15
Nodes (8): assess_rule_3(), _result(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestWarunkowosci

### Community 39 - "test_rules_hybrid.py"
Cohesion: 0.13
Nodes (13): TextNode, ViewportProbe, normalize(), _center_y(), _first_match_offset(), _matches(), measure_geometry(), measure_proximity() (+5 more)

### Community 40 - "test_lang_consistency.py"
Cohesion: 0.11
Nodes (9): assess_rule_10(), _result(), detect_language(), risk_sentences(), split_sentences(), _words(), TestAssessRule10, TestDetectLanguage (+1 more)

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.12
Nodes (6): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), TestKorpusuNaTejMaszynie, TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.12
Nodes (16): AdDocument, AdvertiserRef, Embedding, Entities, Finding, InvestmentFirmRef, MediaItem, RegistryMatch (+8 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.16
Nodes (8): CircuitBreaker, RateLimiter, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures(), test_rate_limiter_spaces_requests(), test_success_resets_failures()

### Community 46 - "DemoTests"
Cohesion: 0.14
Nodes (8): analyze(), evidence(), find_targets(), host(), make_clips(), signals_in(), DemoTests, segments()

### Community 47 - "test_facebook_rules.py"
Cohesion: 0.18
Nodes (16): BBox, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score(), test_not_applicable_rules_stay_out_of_score_denominator() (+8 more)

### Community 48 - "json"
Cohesion: 0.10
Nodes (13): candidates(), load_inputs(), main(), metadata(), QuietLogger, run(), save(), scan() (+5 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.17
Nodes (9): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), _zla() (+1 more)

### Community 51 - "parametrize"
Cohesion: 0.10
Nodes (6): _first_match_start(), normalize_text(), TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZgodnosciKolejkiMiedzySerwisami, test_normalize_strips_diacritics()

### Community 52 - "load_scaling_config"
Cohesion: 0.12
Nodes (21): CZĘŚĆ A — Autoskaler, Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera, Zadanie 4: Executor `pool`, _int(), load_scaling_config(), _parse(), QueuePolicy (+13 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.18
Nodes (13): feed_fold_evidence(), platform_rule_override(), test_feed_fold_hybrid_evidence_from_document_text(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "InvestWatch — stan projektu"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego, 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły (+8 more)

### Community 56 - "test_pool.py"
Cohesion: 0.14
Nodes (13): DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, test_apply_jest_idempotentne(), test_apply_startuje_brakujace_workery(), test_apply_zamyka_nadmiarowe_workery() (+5 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "test_scoring.py"
Cohesion: 0.13
Nodes (8): coverage(), failed_rules(), is_flagged(), Co już jest (gotowe i przetestowane), TestCoverage, TestFailedRules, TestIsFlagged, TestRiskLevel

### Community 61 - "risk_level"
Cohesion: 0.27
Nodes (3): risk_level(), _rule(), TestEskalacjiPoNajciezszymNaruszeniu

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.15
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth

### Community 63 - "router.py"
Cohesion: 0.27
Nodes (6): _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _matches_any(), TestHasProfitClaims

### Community 64 - "health.py"
Cohesion: 0.20
Nodes (3): _Handler, _no_states(), _scaling_response()

### Community 66 - "TranscriptSegment"
Cohesion: 0.27
Nodes (6): TranscriptSegment, speech_rate(), _fake_transcriber(), licznik(), test_speech_rate_basic(), test_speech_rate_zero_duration_no_crash()

### Community 67 - "10. Pozyskiwanie danych i bezpieczeństwo demo"
Cohesion: 0.40
Nodes (5): 10. Pozyskiwanie danych i bezpieczeństwo demo, Bezpieczeństwo demo (anty-cel: „demo zależne od wifi"), Cybersec (kryterium oceniane wprost), Kolejka i harmonogram, Pluginowalne źródła

### Community 68 - "json"
Cohesion: 0.12
Nodes (13): test_przyklad_waliduje_sie_przeciw_modelowi(), doc_from_node(), load_case(), main(), print_table(), score_one(), update_gold(), test_host_replaced_path_and_params_kept() (+5 more)

### Community 69 - "services"
Cohesion: 0.20
Nodes (9): name, name, networks, investwatch, services, volumes, pgdata, seaweeddata (+1 more)

### Community 70 - "analyzer"
Cohesion: 0.22
Nodes (10): depends_on, env_file, extra_hosts, networks, depends_on, postgres, valkey, condition (+2 more)

### Community 71 - "Enum"
Cohesion: 0.31
Nodes (6): Engine, EvidenceKind, Relation, RiskLevel, ScopeStatus, Verdict

### Community 72 - "scraper: FacebookAdsSource (Meta Ad Library)"
Cohesion: 0.20
Nodes (6): `.env`, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: FacebookAdsSource (Meta Ad Library), start_background(), Demo INVESTWATCH

### Community 73 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.22
Nodes (9): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba, 6. Kontrakty danych (ZAMROŻONE o 12:30) (+1 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 77 - "_client"
Cohesion: 0.39
Nodes (3): _client(), _doc(), TestOverrideWBatch2

### Community 79 - "facebook_rules.py"
Cohesion: 0.44
Nodes (6): Evidence, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.33
Nodes (5): collect_ads_from_dom(), merge_nodes(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram Modułu 1 — plan implementacji"
Cohesion: 0.33
Nodes (5): Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach)

### Community 82 - "api"
Cohesion: 0.25
Nodes (8): build, build, networks, ports, profiles, context, api, build

### Community 83 - "4. Rozważone podejścia"
Cohesion: 0.50
Nodes (4): 4. Rozważone podejścia, Podejście A — „wszystko do LLM-a", Podejście B — „wszystko na regułach deterministycznych", Podejście C — hybryda warstwowa **[WYBRANE]**

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.29
Nodes (7): environment, environment, API_BASE_URL, DATABASE_URL, OLLAMA_BASE_URL, S3_ENDPOINT, VALKEY_URL

### Community 87 - "knn_score"
Cohesion: 0.24
Nodes (6): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h), knn_score(), TestKnnScore

### Community 88 - "conftest.py"
Cohesion: 0.39
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 94 - "8. Logika modułów"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 95 - "9. Scoring, threshold i metryki"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 96 - "nginx"
Cohesion: 0.40
Nodes (5): image, networks, ports, volumes, nginx

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.40
Nodes (5): web, depends_on, networks, ports, profiles

### Community 100 - "T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 662 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `test_contracts.py` to `test_registry.py`, `test_worker.py`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `facebook.py`, `_client`, `LocalBlobStore`, `test_preconditions.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `Verdict`, `RuleResult`, `assess_rule_3`, `test_rules_hybrid.py`, `test_lang_consistency.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `scraper/contracts.py`, `test_facebook_rules.py`, `parametrize`, `TranscriptSegment`, `json`, `6. Kontrakty danych (ZAMROŻONE o 12:30)`, `_client`, `facebook_rules.py`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 57 inferred relationships involving `AdDocument` (e.g. with `6.1 `AdDocument` — to, co produkuje scraper` and `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"`) actually correct?**
  _`AdDocument` has 57 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `Verdict` to `test_registry.py`, `risk_score`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `_client`, `test_contracts.py`, `test_preconditions.py`, `OllamaClient`, `analyze`, `RuleResult`, `assess_rule_3`, `test_rules_hybrid.py`, `test_lang_consistency.py`, `test_facebook_rules.py`, `max_breach_severity`, `test_scoring.py`, `risk_level`, `json`, `_client`, `facebook_rules.py`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_worker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07127882599580712 - nodes in this community are weakly interconnected._