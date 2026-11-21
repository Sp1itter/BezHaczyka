# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 174 files · ~1,144,771 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: .gz 8, (none) 7, .example 3)

## Summary
- 2532 nodes · 6414 edges · 156 communities (108 shown, 48 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 496 edges (avg confidence: 0.92)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `13144a6f`
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
- httpx
- risk_score
- InvestWatch — dokument projektowy (design doc)
- evaluate_batch_1
- classify_scope
- _file
- test_config.py
- analyzer/contracts.py
- Verdict
- worker.py
- test_scaling_runtime.py
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- RuleResult
- AdDocument
- test_casedb_bridge.py
- Integracja serwisów — kto wywołuje kogo
- test_casedb_adapter.py
- meta_json.py
- test_facebook_contract.py
- OllamaClient
- analyze
- rules_hybrid.py
- re
- Verdict
- test_rules_det_fallback.py
- assess_rule_3
- rules_det_fallback.py
- test_guards.py
- FacebookAdsSource
- test_stt_pipeline.py
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- DemoTests
- store.py
- guards.py
- gpu
- test_scaling_endpoint.py
- parametrize
- scaling.py
- feed_fold_evidence
- InvestWatch — stan projektu
- test_partial_guard.py
- test_pool.py
- pytest
- eval_rules.py
- QueueState
- stt.py
- db.py
- infra - punkt startowy dla Osoby C (API + dashboard)
- test_facebook_rules.py
- health.py
- default_config
- test_demo.py
- AGENTS.md - services/casedb
- json
- services
- analyzer
- export.py
- scraper: FacebookAdsSource (Meta Ad Library)
- test_idempotency_gate.py
- healthcheck
- postgres
- test_gold_set.py
- test_lang_consistency.py
- CircuitBreaker
- test_pipeline.py
- collect_ads_from_dom
- Harmonogram i orkiestracja — dokument projektowy
- casedb
- ingest.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- check_compliance.py
- test_eval_rules.py
- casedb
- test_preconditions.py
- seaweedfs
- test_rule_13.py
- _doc
- test_det_placeholders.py
- TestGranicyKontraktu
- batching.py
- health_payload
- valkey
- web
- demo.py
- ApiClient
- .test_search_deduplicates_ids_and_respects_candidate_limit
- casedb_batch.py
- FakeConn
- quote_is_verifiable
- AnalyzerConfig
- ._api
- classify_similarity
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- gen_facebook_examples.py
- TestBramkiWsadu4
- TranscriptSegment
- parse_args
- test_gen_examples.py
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- Enum
- math
- TestKorpusuNaTejMaszynie
- TestZaleznosci
- cosine
- facebook_rules.py
- Harmonogram Modułu 1 — plan implementacji
- Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)
- Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)
- knn_score
- TestPowtarzalnosciModelu
- TranscriptSegment
- FeedFoldEvidence
- _default_spawn
- _build_det_results

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 111 edges
2. `Verdict` - 98 edges
3. `RuleResult` - 89 edges
4. `analyze()` - 71 edges
5. `OllamaClient` - 61 edges
6. `Evidence` - 50 edges
7. `AnalyzerConfig` - 48 edges
8. `FacebookAdsSource` - 48 edges
9. `EntityResolution` - 43 edges
10. `Engine` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Osoba A — `services/scraper` (zmergowane, PR #2)` --references--> `FacebookAdsSource`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/scraper/sources/facebook.py
- `Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`)` --references--> `default_config()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/rules_llm/registry.py
- `4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py
- `6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `6.2 `RenderProbe` — geometria renderu, podstawa reguł DET` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (156 total, 48 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.11
Nodes (19): build_config(), coverage_report(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _with_hybrid(), _all_pass_handler() (+11 more)

### Community 4 - "test_stt.py"
Cohesion: 0.22
Nodes (17): risk_timing(), RiskTiming, test_rate_anomaly_fast_disclaimer(), test_rate_anomaly_single_segment(), test_rate_anomaly_zero_median(), test_risk_before_profit_gives_negative_gap(), test_risk_timing_custom_patterns(), test_risk_timing_empty_transcript() (+9 more)

### Community 5 - "test_worker.py"
Cohesion: 0.21
Nodes (17): handle_job(), _api(), handler(), _api_no_get(), test_api_error_on_get_returns_none(), test_api_error_on_post_returns_none(), test_findings_out_dir_zapisuje_json_nawet_gdy_api_pada(), test_flat_payload_z_det_results() (+9 more)

### Community 6 - "Relation"
Cohesion: 0.08
Nodes (16): _blank(), _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), mask_non_claims(), _matches_any(), route() (+8 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "httpx"
Cohesion: 0.18
Nodes (14): _download(), resolve_media(), _client(), test_http_download_and_cache_reuse(), handler(), test_http_error_status_returns_none(), test_http_exception_returns_none(), test_http_size_limit() (+6 more)

### Community 9 - "risk_score"
Cohesion: 0.07
Nodes (15): coverage(), failed_rules(), is_flagged(), max_breach_severity(), risk_level(), risk_score(), _rule(), TestCoverage (+7 more)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.06
Nodes (31): 10. Pozyskiwanie danych i bezpieczeństwo demo, 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 4. Rozważone podejścia (+23 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.07
Nodes (12): Scope, ScopeStatus, classify_scope(), _find_any(), _normalize(), test_cfd_na_krypto_jest_w_zakresie_w_przykladzie(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy (+4 more)

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.11
Nodes (19): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+11 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.10
Nodes (22): _bodies(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case(), event(), _new_event(), mark_partial() (+14 more)

### Community 16 - "Verdict"
Cohesion: 0.18
Nodes (19): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _boom(), _client(), wrapped(), _doc(), _ok() (+11 more)

### Community 17 - "worker.py"
Cohesion: 0.13
Nodes (8): serve(), _max_bytes(), _s3_to_http(), _build_resolution(), main(), _save_finding(), _start_health_server(), run()

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.09
Nodes (22): A — scraper + reguły DET, A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, B — analyzer, C — api + web, C — api + web, Co zmieniło się po review zespołu (wersja 2), Drabinka cięcia zakresu (+14 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "RuleResult"
Cohesion: 0.07
Nodes (23): 5. Architektura, Układ repozytorium, A — scraper + reguły DET, B — analyzer, C — api + web, Podział roli, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle) (+15 more)

### Community 23 - "AdDocument"
Cohesion: 0.12
Nodes (7): analyze(), _ensure_transcript(), _ensure_vector_representation(), _doc(), _rule(), _runner(), TestAnalyze

### Community 25 - "test_casedb_bridge.py"
Cohesion: 0.12
Nodes (10): claim(), connect(), fetch_case(), _jsonb(), _plain(), process_cases(), save_ai_result(), set_status() (+2 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.20
Nodes (8): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, analyze_document()

### Community 28 - "test_casedb_adapter.py"
Cohesion: 0.15
Nodes (17): analyzer_version(), case_to_document(), finding_to_ai_result(), is_partial(), is_partial_transcript(), _load(), test_asset_audio_video_trafiaja_do_media(), test_brak_wszystkiego_nie_rzuca() (+9 more)

### Community 29 - "meta_json.py"
Cohesion: 0.09
Nodes (37): doc_from_node(), Publisher, ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards() (+29 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.08
Nodes (12): Source, SourceBlocked, SourceError, canonical_ad_url(), doc(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_identity_and_url() (+4 more)

### Community 32 - "OllamaClient"
Cohesion: 0.12
Nodes (10): embed_document_text(), LlmError, OllamaClient, TestEmbedDocumentText, handler(), _real_client(), check_embeddings(), main() (+2 more)

### Community 33 - "analyze"
Cohesion: 0.14
Nodes (7): EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults, TestRegulyR4, TestWarstwyWektorowej

### Community 34 - "rules_hybrid.py"
Cohesion: 0.10
Nodes (12): _center_y(), _first_match_offset(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline(), _norm_for(), _pick_viewport() (+4 more)

### Community 35 - "re"
Cohesion: 0.11
Nodes (10): apply_rule_10_override(), assess_rule_10(), detect_language(), risk_sentences(), split_sentences(), _words(), test_regula_10_bez_ryzyka_wymusza_na(), TestAssessRule10 (+2 more)

### Community 36 - "Verdict"
Cohesion: 0.16
Nodes (34): Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, _basis(), _cosine(), detect_change(), detect_disappeared(), diff_rule_results(), _have_embeddings(), _rule_phrase() (+26 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.20
Nodes (23): RenderProbe, ViewportProbe, det_fallback_results(), _by(), _doc(), _doc2(), _node(), _run() (+15 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.11
Nodes (9): assess_rule_3(), _result(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestProporcjonalnosciCzcionki (+1 more)

### Community 39 - "rules_det_fallback.py"
Cohesion: 0.23
Nodes (11): _dominant_font_px(), _evidence(), _na(), _result(), _risk_hits(), _rule_4(), _rule_5(), _rule_6() (+3 more)

### Community 40 - "test_guards.py"
Cohesion: 0.12
Nodes (29): _res(), _run(), test_12a_jeden_rok_pass_zamieniony_na_fail(), test_12a_nie_zamienia_fail_na_pass(), test_12a_pelny_okres_zostaje_pass(), test_12b_pass_bez_walut_i_oplat_to_fail(), test_12b_tylko_waluty_bez_oplat_to_fail(), test_12b_waluty_i_oplaty_zostaje_pass() (+21 more)

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.12
Nodes (6): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), test_real_speech_to_rule_3(), TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.12
Nodes (16): AdDocument, AdvertiserRef, Embedding, Entities, Finding, InvestmentFirmRef, MediaItem, RegistryMatch (+8 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.08
Nodes (12): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, NodeCache, SeenSet (+4 more)

### Community 46 - "DemoTests"
Cohesion: 0.20
Nodes (5): analyze(), is_language(), language_factory(), DemoTests, segments()

### Community 47 - "store.py"
Cohesion: 0.16
Nodes (8): main(), add_asset(), claim(), save_ai_result(), save_case(), set_columns(), set_status(), test_cli_ingest_and_export()

### Community 48 - "guards.py"
Cohesion: 0.17
Nodes (15): normalize(), apply_guards(), _guard_rule_12a(), _guard_rule_12b(), _guard_rule_14(), _guard_rule_16(), _guard_rule_17(), _guard_rule_2() (+7 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.17
Nodes (9): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), _zla() (+1 more)

### Community 51 - "parametrize"
Cohesion: 0.13
Nodes (5): normalize_text(), TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZgodnosciKolejkiMiedzySerwisami, test_normalize_strips_diacritics()

### Community 52 - "scaling.py"
Cohesion: 0.12
Nodes (16): CZĘŚĆ A — Autoskaler, Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera, Zadanie 4: Executor `pool`, _connection(), _int(), _parse(), QueuePolicy (+8 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.18
Nodes (13): feed_fold_evidence(), platform_rule_override(), test_feed_fold_hybrid_evidence_from_document_text(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "InvestWatch — stan projektu"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Trafność Modułu 2 — pomiary na żywym Bieliku 4.5B (21.11, noc), 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły, InvestWatch — stan projektu (+8 more)

### Community 55 - "test_partial_guard.py"
Cohesion: 0.28
Nodes (9): _doc(), _rule(), _run(), test_partial_fail_braku_staje_sie_na(), test_partial_fail_obecnosci_zostaje(), test_partial_regula_10_i_pass_bez_zmian(), test_pelna_transkrypcja_bez_zmian(), test_reguly_brakujacego_zastrzezenia_sa_degradowane() (+1 more)

### Community 56 - "test_pool.py"
Cohesion: 0.12
Nodes (14): DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne(), test_apply_startuje_brakujace_workery() (+6 more)

### Community 57 - "pytest"
Cohesion: 0.27
Nodes (11): load_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany(), test_plik_yaml_zgodny_z_domyslna_konfiguracja(), test_uszkodzony_yaml_daje_domyslna_konfiguracje() (+3 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.13
Nodes (14): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+6 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "stt.py"
Cohesion: 0.15
Nodes (13): _default_transcriber(), run(), SttError, transcribe(), test_stt_error_is_runtime_error(), test_transcribe_empty_result(), test_transcribe_passes_through_stt_error(), boom() (+5 more)

### Community 61 - "db.py"
Cohesion: 0.19
Nodes (4): connect(), migrate(), conn(), worker()

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.15
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth

### Community 63 - "test_facebook_rules.py"
Cohesion: 0.18
Nodes (16): BBox, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score(), test_not_applicable_rules_stay_out_of_score_denominator() (+8 more)

### Community 64 - "health.py"
Cohesion: 0.22
Nodes (3): _Handler, _no_states(), _scaling_response()

### Community 65 - "default_config"
Cohesion: 0.12
Nodes (13): default_config(), analyzer — Moduł 2 (analiza AI), Brama zakresu, Konfiguracja, Mapa plików, Quick Start, Uruchomienie, Weryfikacja cytatu (+5 more)

### Community 66 - "test_demo.py"
Cohesion: 0.18
Nodes (3): find_targets(), host(), make_clips()

### Community 67 - "AGENTS.md - services/casedb"
Cohesion: 0.18
Nodes (9): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+1 more)

### Community 68 - "json"
Cohesion: 0.11
Nodes (11): test_przyklad_waliduje_sie_przeciw_modelowi(), main(), load_case(), main(), print_table(), score_one(), update_gold(), _load() (+3 more)

### Community 69 - "services"
Cohesion: 0.13
Nodes (14): name, name, networks, investwatch, image, networks, ports, volumes (+6 more)

### Community 70 - "analyzer"
Cohesion: 0.20
Nodes (11): depends_on, env_file, extra_hosts, networks, depends_on, depends_on, postgres, valkey (+3 more)

### Community 71 - "export.py"
Cohesion: 0.46
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 72 - "scraper: FacebookAdsSource (Meta Ad Library)"
Cohesion: 0.20
Nodes (6): `.env`, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: FacebookAdsSource (Meta Ad Library), start_background(), Demo INVESTWATCH

### Community 73 - "test_idempotency_gate.py"
Cohesion: 0.28
Nodes (10): Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), simhash_hex(), _doc(), test_brak_simhasha_nie_wywraca_bramy(), test_identyczny_material_nie_idzie_na_gpu(), test_pierwsze_zetkniecie_zawsze_analizujemy() (+2 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 77 - "test_lang_consistency.py"
Cohesion: 0.31
Nodes (4): evaluate_batch_2(), _client(), _doc(), TestOverrideWBatch2

### Community 78 - "CircuitBreaker"
Cohesion: 0.16
Nodes (8): CircuitBreaker, RateLimiter, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures(), test_rate_limiter_spaces_requests(), test_success_resets_failures()

### Community 79 - "test_pipeline.py"
Cohesion: 0.19
Nodes (7): hamming_distance(), is_near_duplicate_simhash(), normalize(), simhash(), tokenize(), TestNormalizacjaITokeny, TestSimhash

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.33
Nodes (5): collect_ads_from_dom(), merge_nodes(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.14
Nodes (13): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+5 more)

### Community 82 - "casedb"
Cohesion: 0.29
Nodes (6): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Testy, Wymagania

### Community 83 - "ingest.py"
Cohesion: 0.19
Nodes (11): from_ad_document(), from_youtube(), youtube_video_id(), Asset, Case, case_id_for(), Content, test_claim_is_exclusive() (+3 more)

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.14
Nodes (11): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki, Co znaczy `is_violation`, Jak dodac pozycje (+3 more)

### Community 85 - "environment"
Cohesion: 0.20
Nodes (10): environment, environment, networks, ports, profiles, API_BASE_URL, OLLAMA_BASE_URL, S3_ENDPOINT (+2 more)

### Community 86 - "check_compliance.py"
Cohesion: 0.22
Nodes (13): test_worker_imports_without_rq(), check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file() (+5 more)

### Community 87 - "test_eval_rules.py"
Cohesion: 0.23
Nodes (6): _row(), test_kolejnosc_regul_numeryczna(), test_metryki_macierz_pomylek(), test_pending_nie_wchodzi_do_macierzy(), test_tabela_zawiera_reguly(), test_walidacja_odrzuca_nieznana_regule()

### Community 88 - "casedb"
Cohesion: 0.33
Nodes (6): environment, networks, restart, volumes, DATABASE_URL, casedb

### Community 89 - "test_preconditions.py"
Cohesion: 0.20
Nodes (7): evaluate_batch_3(), evaluate_batch_4(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_historical_performance(), mentions_tax()

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.17
Nodes (20): TextNode, assess_rule_13(), _na(), _result(), rule_13_runner(), _doc(), _node(), test_brak_wynikow_historycznych_to_not_applicable() (+12 more)

### Community 92 - "_doc"
Cohesion: 0.20
Nodes (5): _client_returning_fail(), _client_that_must_not_be_called(), handler(), _doc(), TestBramkiWsadu3

### Community 93 - "test_det_placeholders.py"
Cohesion: 0.14
Nodes (10): Engine, EvidenceKind, Relation, missing_det_placeholders(), _doc(), _res(), test_nie_dubluje_regul_ze_scrapera(), test_placeholdery_nie_zmieniaja_ryzyka_a_obnizaja_coverage() (+2 more)

### Community 95 - "batching.py"
Cohesion: 0.23
Nodes (5): load_prompt(), _all_not_applicable(), _build_result(), evaluate_batch(), _not_applicable()

### Community 96 - "health_payload"
Cohesion: 0.40
Nodes (4): health_payload(), _llm(), test_health_ollama_down_is_degraded_not_fatal(), test_health_ollama_up()

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.20
Nodes (10): build, build, context, build, web, build, depends_on, networks (+2 more)

### Community 99 - "demo.py"
Cohesion: 0.23
Nodes (9): 6. Do udoskonalenia — uszeregowane po wpływie na demo, evidence(), load_inputs(), main(), normalize(), save(), scan(), signals_in() (+1 more)

### Community 100 - "ApiClient"
Cohesion: 0.21
Nodes (5): ApiClient, ApiError, _check_local(), _resolve_document(), test_external_base_url_rejected()

### Community 101 - ".test_search_deduplicates_ids_and_respects_candidate_limit"
Cohesion: 0.15
Nodes (6): candidates(), metadata(), QuietLogger, run(), worker(), ydl_options()

### Community 102 - "casedb_batch.py"
Cohesion: 0.18
Nodes (8): _fake_llm(), test_tryb_plikowy_z_fake_llm(), failing(), main(), make_analyzer(), analyze_case(), run_file(), summarize()

### Community 103 - "FakeConn"
Cohesion: 0.15
Nodes (6): _ai(), _Cur, FakeConn, test_blad_analizy_ustawia_error_i_nie_przerywa(), boom(), test_kolejnosc_statusow_i_upsert()

### Community 104 - "quote_is_verifiable"
Cohesion: 0.27
Nodes (3): _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable

### Community 117 - "AnalyzerConfig"
Cohesion: 0.15
Nodes (6): AnalyzerConfig, _doc(), _fake_transcriber(), TestKolejnosciEtapow, TestWywolaniaTranskrypcji, licznik()

### Community 123 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.20
Nodes (10): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba (+2 more)

### Community 124 - "gen_facebook_examples.py"
Cohesion: 0.17
Nodes (7): download_ytdlp(), main(), FacebookConfig, LocalBlobStore, source(), main(), pick_ad()

### Community 126 - "TranscriptSegment"
Cohesion: 0.17
Nodes (7): TranscriptSegment, _first_match_start(), rate_anomaly(), speech_rate(), test_rate_anomaly_too_few_segments(), test_speech_rate_basic(), test_speech_rate_zero_duration_no_crash()

### Community 128 - "test_gen_examples.py"
Cohesion: 0.16
Nodes (8): browser(), chromium_available(), _launch(), test_committed_examples_have_no_external_hosts(), test_host_replaced_path_and_params_kept(), test_uppercase_scheme_and_s3_untouched(), test_urls_inside_text_and_nested_structures(), sanitize()

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Korekty niespojnosci danych (nie dopasowanie do wyniku), Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

### Community 131 - "Enum"
Cohesion: 0.31
Nodes (6): Engine, EvidenceKind, Relation, RiskLevel, ScopeStatus, Verdict

### Community 142 - "facebook_rules.py"
Cohesion: 0.44
Nodes (6): Evidence, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 143 - "Harmonogram Modułu 1 — plan implementacji"
Cohesion: 0.25
Nodes (7): CZĘŚĆ B — Detektor zmian, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 6: Klasyfikacja zdarzenia

### Community 144 - "Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY), Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości

### Community 145 - "Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości, Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 862 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **48 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `RuleResult` to `test_registry.py`, `evaluate_batch_1`, `facebook_rules.py`, `analyzer/contracts.py`, `Verdict`, `worker.py`, `_client`, `AdDocument`, `test_casedb_adapter.py`, `meta_json.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `rules_hybrid.py`, `re`, `Verdict`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_det_fallback.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `scraper/contracts.py`, `test_partial_guard.py`, `eval_rules.py`, `stt.py`, `test_facebook_rules.py`, `json`, `test_idempotency_gate.py`, `test_lang_consistency.py`, `test_pipeline.py`, `test_preconditions.py`, `test_rule_13.py`, `_doc`, `test_det_placeholders.py`, `batching.py`, `ApiClient`, `AnalyzerConfig`, `6. Kontrakty danych (ZAMROŻONE o 12:30)`, `gen_facebook_examples.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `AdDocument` (e.g. with `6.1 `AdDocument` — to, co produkuje scraper` and `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"`) actually correct?**
  _`AdDocument` has 37 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10952380952380952 - nodes in this community are weakly interconnected._
- **Why does `RuleResult` connect `RuleResult` to `test_registry.py`, `risk_score`, `evaluate_batch_1`, `facebook_rules.py`, `analyzer/contracts.py`, `Verdict`, `worker.py`, `InvestWatch — plan wykonawczy 23 h`, `AdDocument`, `analyze`, `rules_hybrid.py`, `re`, `Verdict`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_det_fallback.py`, `test_guards.py`, `scraper/contracts.py`, `guards.py`, `test_partial_guard.py`, `test_facebook_rules.py`, `json`, `test_lang_consistency.py`, `test_pipeline.py`, `test_preconditions.py`, `test_rule_13.py`, `test_det_placeholders.py`, `batching.py`, `6. Kontrakty danych (ZAMROŻONE o 12:30)`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 61 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Should `Relation` be split into smaller, more focused modules?**
  _Cohesion score 0.08181818181818182 - nodes in this community are weakly interconnected._