# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 124 files · ~1,105,444 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: .gz 8, (none) 5, .example 2)

## Summary
- 2000 nodes · 5106 edges · 117 communities (88 shown, 29 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 577 edges (avg confidence: 0.93)
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
- worker.py
- test_scaling_runtime.py
- _client
- RenderProbe
- rules
- test_contracts.py
- AdDocument
- evaluate_batch_4
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
- batching.py
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
- demo.py
- gpu
- test_scaling_endpoint.py
- parametrize
- scaling.py
- feed_fold_evidence
- InvestWatch — stan projektu
- max_breach_severity
- test_pool.py
- pytest
- TestPowtarzalnosciModelu
- QueueState
- is_flagged
- test_idempotency_gate.py
- infra - punkt startowy dla Osoby C (API + dashboard)
- router.py
- health.py
- cosine
- TranscriptSegment
- Harmonogram i orkiestracja — dokument projektowy
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
- change_detect.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- pool.py
- knn_score
- test_gen_examples.py
- Zbior zloty (gold set)
- seaweedfs
- Engine
- re
- test_demo.py
- TestGranicyKontraktu
- QuietLogger
- nginx
- valkey
- web
- scan
- registry.py
- TranscriptSegment
- FeedFoldEvidence

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 111 edges
2. `Verdict` - 106 edges
3. `RuleResult` - 79 edges
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
- `6.2 `RenderProbe` — geometria renderu, podstawa reguł DET` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Jak wagi jury przekładają się na decyzje projektowe` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Podejście C — hybryda warstwowa **[WYBRANE]**` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `6.1 `AdDocument` — to, co produkuje scraper` --references--> `AdDocument`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (117 total, 29 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.15
Nodes (16): build_config(), coverage_report(), expected_rule_ids(), module2_runners(), _rule_sort_key(), _all_pass_handler(), _client(), _doc() (+8 more)

### Community 4 - "test_stt.py"
Cohesion: 0.08
Nodes (38): _default_transcriber(), run(), _first_match_start(), normalize_text(), rate_anomaly(), risk_timing(), RiskTiming, speech_rate() (+30 more)

### Community 5 - "test_worker.py"
Cohesion: 0.07
Nodes (25): Co A wrzuca do kolejki, ApiClient, ApiError, _check_local(), health_payload(), analyze_document(), _build_det_results(), handle_job() (+17 more)

### Community 6 - "Relation"
Cohesion: 0.13
Nodes (8): route(), RoutingDecision, RoutingInput, _inp(), TestR1WlasnyMaterialFirmy, TestR2PodmiotTrzeci, TestR3DoradztwoBezZezwolenia, TestR4Triage

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "embeddings.py"
Cohesion: 0.14
Nodes (8): Zadanie 6: Klasyfikacja zdarzenia, hamming_distance(), is_near_duplicate_simhash(), normalize(), simhash(), tokenize(), TestNormalizacjaITokeny, TestSimhash

### Community 9 - "risk_score"
Cohesion: 0.11
Nodes (9): failed_rules(), risk_level(), risk_score(), _rule(), TestEskalacjiPoNajciezszymNaruszeniu, TestFailedRules, TestNotApplicableNieWchodziDoMianownika, TestRiskLevel (+1 more)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.06
Nodes (32): 10. Pozyskiwanie danych i bezpieczeństwo demo, 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 4. Rozważone podejścia (+24 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.08
Nodes (9): classify_scope(), _find_any(), _normalize(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania (+1 more)

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.13
Nodes (17): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+9 more)

### Community 15 - "contracts.py"
Cohesion: 0.17
Nodes (12): AdvertiserRef, BBox, Embedding, Entities, InvestmentFirmRef, Publisher, RegistryMatch, Relation (+4 more)

### Community 16 - "Verdict"
Cohesion: 0.09
Nodes (26): LlmError, load_prompt(), advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _na(), _result(), _normalize_for_match() (+18 more)

### Community 17 - "worker.py"
Cohesion: 0.11
Nodes (7): serve(), _build_resolution(), main(), parse_args(), _start_health_server(), run(), TestFlagiKolejkiWWorkerze

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "RenderProbe"
Cohesion: 0.06
Nodes (34): Układ repozytorium, A — scraper + reguły DET, A — scraper + reguły DET, B — analyzer, B — analyzer, C — api + web, C — api + web, Co zmieniło się po review zespołu (wersja 2) (+26 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (26): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, legal_basis, max_distance_px, max_gap_seconds, max_offset_chars (+18 more)

### Community 22 - "test_contracts.py"
Cohesion: 0.10
Nodes (12): Evidence, RuleResult, _crashed_rule_result(), _result(), RuleBase, _result(), test_analyzable_text_zawiera_transkrypcje(), test_finding_moze_nalezec_do_wielu_modulow() (+4 more)

### Community 23 - "AdDocument"
Cohesion: 0.19
Nodes (5): AdDocument, _doc(), _rule(), _runner(), TestAnalyze

### Community 25 - "evaluate_batch_4"
Cohesion: 0.17
Nodes (7): evaluate_batch_4(), _client_returning_fail(), _client_that_must_not_be_called(), handler(), _doc(), TestBramkiWsadu3, TestBramkiWsadu4

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.18
Nodes (8): Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, coverage(), TestCoverage

### Community 28 - "LocalBlobStore"
Cohesion: 0.12
Nodes (7): download_ytdlp(), probe_duration(), main(), FacebookConfig, LocalBlobStore, main(), pick_ad()

### Community 29 - "meta_json.py"
Cohesion: 0.10
Nodes (35): ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards(), clean_text(), find_ad_nodes() (+27 more)

### Community 30 - "test_preconditions.py"
Cohesion: 0.17
Nodes (7): evaluate_batch_3(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_historical_performance(), mentions_tax(), TestWynikiHistoryczne

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.08
Nodes (14): Source, SourceBlocked, SourceError, canonical_ad_url(), doc(), source(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls() (+6 more)

### Community 32 - "OllamaClient"
Cohesion: 0.11
Nodes (8): embed_document_text(), OllamaClient, TestEmbedDocumentText, handler(), check_embeddings(), main(), make_doc(), main()

### Community 33 - "analyze"
Cohesion: 0.13
Nodes (11): analyze(), AnalyzerConfig, _ensure_transcript(), _ensure_vector_representation(), EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie (+3 more)

### Community 34 - "jobs.py"
Cohesion: 0.15
Nodes (9): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, blob_store_from_env(), BlobStore (+1 more)

### Community 35 - "re"
Cohesion: 0.27
Nodes (12): check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file(), _lines() (+4 more)

### Community 36 - "Verdict"
Cohesion: 0.27
Nodes (25): detect_change(), diff_rule_results(), ChangeKind, RiskLevel, Verdict, _doc(), _finding(), _r() (+17 more)

### Community 37 - "batching.py"
Cohesion: 0.36
Nodes (4): _all_not_applicable(), _build_result(), evaluate_batch(), _not_applicable()

### Community 38 - "assess_rule_3"
Cohesion: 0.18
Nodes (6): assess_rule_3(), _doc(), _node(), TestOsiGeometrii, TestOsiTekstu, TestWarunkowosci

### Community 39 - "test_rules_hybrid.py"
Cohesion: 0.17
Nodes (6): _first_match_offset(), measure_proximity(), measure_text(), measure_timeline(), Proximity, TestWyboruOsi

### Community 40 - "test_lang_consistency.py"
Cohesion: 0.14
Nodes (5): apply_rule_10_override(), assess_rule_10(), detect_language(), TestAssessRule10, TestDetectLanguage

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.09
Nodes (12): Transcript, ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), _doc(), _fake_transcriber(), TestKolejnosciEtapow (+4 more)

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.10
Nodes (18): AdDocument, AdvertiserRef, BBox, Embedding, Entities, Finding, InvestmentFirmRef, MediaItem (+10 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.09
Nodes (11): CircuitBreaker, NodeCache, RateLimiter, SeenSet, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures() (+3 more)

### Community 46 - "DemoTests"
Cohesion: 0.31
Nodes (3): analyze(), DemoTests, segments()

### Community 47 - "test_facebook_rules.py"
Cohesion: 0.19
Nodes (14): TextNode, facebook_det_results(), _doc(), _node(), score(), test_not_applicable_rules_stay_out_of_score_denominator(), test_platform_typography_rules_not_applicable(), test_rejects_other_sources() (+6 more)

### Community 48 - "demo.py"
Cohesion: 0.19
Nodes (9): candidates(), evidence(), metadata(), normalize(), run(), signals_in(), transcript(), request() (+1 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.17
Nodes (9): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), _zla() (+1 more)

### Community 51 - "parametrize"
Cohesion: 0.10
Nodes (4): TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZaleznosci, TestZgodnosciKolejkiMiedzySerwisami

### Community 52 - "scaling.py"
Cohesion: 0.12
Nodes (15): CZĘŚĆ A — Autoskaler, Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera, _connection(), _int(), _parse(), QueuePolicy, _rq_backlog_reader() (+7 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.18
Nodes (13): feed_fold_evidence(), platform_rule_override(), test_feed_fold_hybrid_evidence_from_document_text(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "InvestWatch — stan projektu"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego, 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły (+8 more)

### Community 56 - "test_pool.py"
Cohesion: 0.16
Nodes (11): PoolExecutor, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne(), test_apply_startuje_brakujace_workery(), test_apply_zamyka_nadmiarowe_workery(), test_martwy_worker_jest_zastepowany() (+3 more)

### Community 57 - "pytest"
Cohesion: 0.22
Nodes (12): _merge_meta(), load_scaling_config(), test_kolizja_podnosi_blad(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+4 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "is_flagged"
Cohesion: 0.33
Nodes (3): is_flagged(), Co już jest (gotowe i przetestowane), TestIsFlagged

### Community 61 - "test_idempotency_gate.py"
Cohesion: 0.25
Nodes (11): Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), _simhash_int(), simhash_hex(), _doc(), test_brak_simhasha_nie_wywraca_bramy(), test_identyczny_material_nie_idzie_na_gpu() (+3 more)

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.18
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth

### Community 63 - "router.py"
Cohesion: 0.27
Nodes (6): _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _matches_any(), TestHasProfitClaims

### Community 64 - "health.py"
Cohesion: 0.20
Nodes (3): _Handler, _no_states(), _scaling_response()

### Community 65 - "cosine"
Cohesion: 0.27
Nodes (3): _cosine(), cosine(), TestCosine

### Community 67 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.14
Nodes (14): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+6 more)

### Community 68 - "json"
Cohesion: 0.23
Nodes (8): main(), doc_from_node(), load_case(), main(), print_table(), score_one(), update_gold(), test_document_matches_frozen_contract()

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
Cohesion: 0.20
Nodes (10): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba (+2 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 77 - "_client"
Cohesion: 0.35
Nodes (4): evaluate_batch_2(), _client(), _doc(), TestOverrideWBatch2

### Community 79 - "facebook_rules.py"
Cohesion: 0.44
Nodes (6): Evidence, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.17
Nodes (7): Publisher, download_direct(), collect_ads_from_dom(), merge_nodes(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram Modułu 1 — plan implementacji"
Cohesion: 0.25
Nodes (7): CZĘŚĆ B — Detektor zmian, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 5: Kontrakt `ChangeEvent` i diff reguł

### Community 82 - "api"
Cohesion: 0.25
Nodes (8): build, build, networks, ports, profiles, context, api, build

### Community 83 - "change_detect.py"
Cohesion: 0.18
Nodes (10): _basis(), event(), detect_disappeared(), _have_embeddings(), _new_event(), _rule_phrase(), _transitions(), ChangeSimilarity (+2 more)

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.29
Nodes (7): environment, environment, API_BASE_URL, DATABASE_URL, OLLAMA_BASE_URL, S3_ENDPOINT, VALKEY_URL

### Community 86 - "pool.py"
Cohesion: 0.19
Nodes (5): Zadanie 4: Executor `pool`, _default_spawn(), DryRunExecutor, ScalingDecision, test_dry_run_nic_nie_startuje()

### Community 87 - "knn_score"
Cohesion: 0.14
Nodes (8): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h), classify_similarity(), knn_score(), TestClassifySimilarity, TestKnnScore

### Community 88 - "test_gen_examples.py"
Cohesion: 0.19
Nodes (7): browser(), chromium_available(), _launch(), test_host_replaced_path_and_params_kept(), test_uppercase_scheme_and_s3_untouched(), test_urls_inside_text_and_nested_structures(), sanitize()

### Community 89 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "Engine"
Cohesion: 0.17
Nodes (10): Engine, EvidenceKind, TextNode, ViewportProbe, _center_y(), _matches(), measure_geometry(), _pick_viewport() (+2 more)

### Community 92 - "re"
Cohesion: 0.22
Nodes (6): normalize(), risk_sentences(), split_sentences(), _words(), TestRiskSentences, test_committed_examples_have_no_external_hosts()

### Community 93 - "test_demo.py"
Cohesion: 0.18
Nodes (3): find_targets(), host(), make_clips()

### Community 96 - "nginx"
Cohesion: 0.40
Nodes (5): image, networks, ports, volumes, nginx

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.40
Nodes (5): web, depends_on, networks, ports, profiles

### Community 99 - "scan"
Cohesion: 0.38
Nodes (5): load_inputs(), main(), save(), scan(), validate_inputs()

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 678 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `test_stt.py`, `test_worker.py`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `worker.py`, `_client`, `RenderProbe`, `test_contracts.py`, `evaluate_batch_4`, `LocalBlobStore`, `test_preconditions.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `Verdict`, `batching.py`, `assess_rule_3`, `test_rules_hybrid.py`, `test_lang_consistency.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `scraper/contracts.py`, `test_facebook_rules.py`, `test_idempotency_gate.py`, `cosine`, `json`, `6. Kontrakty danych (ZAMROŻONE o 12:30)`, `_client`, `facebook_rules.py`, `change_detect.py`, `Engine`, `TestGranicyKontraktu`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 57 inferred relationships involving `AdDocument` (e.g. with `6.1 `AdDocument` — to, co produkuje scraper` and `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"`) actually correct?**
  _`AdDocument` has 57 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08106219426974144 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `Verdict` to `test_registry.py`, `risk_score`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `_client`, `test_contracts.py`, `AdDocument`, `evaluate_batch_4`, `Integracja serwisów — kto wywołuje kogo`, `test_preconditions.py`, `OllamaClient`, `analyze`, `batching.py`, `assess_rule_3`, `test_lang_consistency.py`, `test_facebook_rules.py`, `max_breach_severity`, `TranscriptSegment`, `json`, `_client`, `facebook_rules.py`, `change_detect.py`, `Engine`, `re`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_worker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07137254901960784 - nodes in this community are weakly interconnected._