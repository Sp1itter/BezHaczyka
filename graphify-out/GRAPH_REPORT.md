# Graph Report - infra-docker-full  (2026-11-21)

## Corpus Check
- 202 files · ~1,156,709 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 15, .gz 8, .example 3)

## Summary
- 2917 nodes · 7421 edges · 162 communities (124 shown, 38 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 764 edges (avg confidence: 0.93)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `1fe2ed88`
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
- test_module3.py
- test_lang_consistency.py
- test_scaling_runtime.py
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- RuleResult
- AdDocument
- Enum
- test_casedb_bridge.py
- Integracja serwisów — kto wywołuje kogo
- casedb_adapter.py
- meta_json.py
- RuntimeError
- test_facebook_contract.py
- OllamaClient
- analyze
- argparse
- re
- test_change_detect.py
- test_rules_det_fallback.py
- assess_rule_3
- rules_hybrid.py
- test_guards.py
- FacebookAdsSource
- test_stt_pipeline.py
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- analyze
- store.py
- guards.py
- gpu
- test_scaling_endpoint.py
- parametrize
- scaling.py
- feed_fold_evidence
- stt.py
- test_partial_guard.py
- test_pool.py
- pytest
- eval_rules.py
- QueueState
- transcribe
- AnalyzerConfig
- infra - punkt startowy dla Osoby C (API + dashboard)
- test_facebook_rules.py
- os
- default_config
- test_demo.py
- AGENTS.md - services/casedb
- InvestWatch — stan projektu
- services
- valkey
- export.py
- scraper: FacebookAdsSource (Meta Ad Library)
- test_demo.py
- healthcheck
- postgres
- ApiClient
- test_integration_scraper.py
- test_pipeline.py
- test_pipeline.py
- collect_ads_from_dom
- Harmonogram i orkiestracja — dokument projektowy
- casedb
- ingest.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- json
- test_eval_rules.py
- casedb
- risk_level
- seaweedfs
- test_rule_13.py
- _doc
- test_api.py
- module3.py
- batching.py
- Engine
- PostgresStore
- context
- demo.py
- ApiClient
- evaluate_batch_2
- test_casedb_bridge.py
- quote_is_verifiable
- BaseModel
- test_casedb.py
- batching.py
- parse_args
- default_config
- change_detect.py
- AnalyzerConfig
- TestPolskaOdmiana
- scraper-ingest
- environment
- TranscriptSegment
- Enum
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- quote_is_verifiable
- stt.py
- web (osoba C)
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- rule_3_runner
- re
- _rule_6
- test_pipeline.py
- scheduler
- scraper-render
- AlertHub
- classify_similarity
- x-scraper
- InvestWatch
- is_flagged
- T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)
- TranscriptSegment
- Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)
- Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)
- _llm
- typing
- ollama
- _ensure_vector_representation
- is_language
- _default_spawn
- _build_det_results
- test_worker_imports_without_rq

## God Nodes (most connected - your core abstractions)
1. `Verdict` - 200 edges
2. `AdDocument` - 154 edges
3. `RuleResult` - 111 edges
4. `analyze()` - 71 edges
5. `Engine` - 62 edges
6. `OllamaClient` - 61 edges
7. `EvidenceKind` - 60 edges
8. `Evidence` - 51 edges
9. `AnalyzerConfig` - 50 edges
10. `FacebookAdsSource` - 49 edges

## Surprising Connections (you probably didn't know these)
- `Osoba C — `services/api`, `services/web`` --references--> `ApiClient`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/api_client.py
- `Zadanie 5: Kontrakt `ChangeEvent` i diff reguł` --references--> `diff_rule_results()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-harmonogram-implementacja.md → services/analyzer/analyzer/change_detect.py
- `B — analyzer` --references--> `knn_score()`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-plan-24h.md → services/analyzer/analyzer/embeddings.py
- `Układ repozytorium` --references--> `Rule`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/rules_llm/base.py
- `4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py

## Import Cycles
- None detected.

## Communities (162 total, 38 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.08
Nodes (25): build_config(), coverage_report(), default_config(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _with_hybrid() (+17 more)

### Community 4 - "test_stt.py"
Cohesion: 0.17
Nodes (19): Transcript, rate_anomaly(), risk_timing(), test_rate_anomaly_fast_disclaimer(), test_rate_anomaly_single_segment(), test_rate_anomaly_too_few_segments(), test_rate_anomaly_zero_median(), test_risk_before_profit_gives_negative_gap() (+11 more)

### Community 5 - "test_worker.py"
Cohesion: 0.19
Nodes (20): handle_job(), _api(), _api_no_get(), test_api_error_on_get_returns_none(), test_api_error_on_post_returns_none(), test_blad_post_document_daje_none_bez_findingu(), test_findings_out_dir_zapisuje_json_nawet_gdy_api_pada(), test_flat_payload_z_det_results() (+12 more)

### Community 6 - "Relation"
Cohesion: 0.07
Nodes (19): Relation, ScopeStatus, _blank(), _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), mask_non_claims() (+11 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "httpx"
Cohesion: 0.16
Nodes (16): _download(), _max_bytes(), resolve_media(), _s3_to_http(), _client(), test_http_download_and_cache_reuse(), handler(), test_http_error_status_returns_none() (+8 more)

### Community 9 - "risk_score"
Cohesion: 0.15
Nodes (9): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set), risk_score(), _rule(), TestNotApplicableNieWchodziDoMianownika (+1 more)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.05
Nodes (43): 10. Pozyskiwanie danych i bezpieczeństwo demo, 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 4. Rozważone podejścia (+35 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.11
Nodes (6): classify_scope(), _find_any(), TestCfdNaKryptoZostajeWZakresie, TestNiepewneIdaDoTriage, TestPozaZakresemTylkoBezOpakowania, TestZwykleInstrumenty

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.12
Nodes (18): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+10 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.08
Nodes (20): AdvertiserRef, BBox, Embedding, Entities, EvidenceKind, Finding, InvestmentFirmRef, Publisher (+12 more)

### Community 16 - "test_module3.py"
Cohesion: 0.33
Nodes (14): assess_shadow_advisory(), _boom(), _client(), wrapped(), _doc(), _ok(), handler(), test_autoryzowany_nie_jest_fail() (+6 more)

### Community 17 - "test_lang_consistency.py"
Cohesion: 0.12
Nodes (8): assess_rule_10(), detect_language(), risk_sentences(), split_sentences(), _words(), TestAssessRule10, TestDetectLanguage, TestRiskSentences

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.20
Nodes (10): evaluate_batch_3(), _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence() (+2 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.09
Nodes (21): A — scraper + reguły DET, B — analyzer, C — api + web, Co zmieniło się po review zespołu (wersja 2), Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate (+13 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "RuleResult"
Cohesion: 0.13
Nodes (9): Evidence, RuleResult, _crashed_rule_result(), _na(), _result(), RuleBase, _no_supervision_reference(), _result() (+1 more)

### Community 23 - "AdDocument"
Cohesion: 0.16
Nodes (5): analyze(), _doc(), _rule(), _runner(), TestAnalyze

### Community 24 - "Enum"
Cohesion: 0.06
Nodes (62): react, react-dom, recharts, vite, @vitejs/plugin-react, dependencies, react@18.3.1, react-dom@18.3.1 (+54 more)

### Community 25 - "test_casedb_bridge.py"
Cohesion: 0.08
Nodes (13): evaluate_batch_4(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_historical_performance(), mentions_tax(), _client_returning_fail(), _client_that_must_not_be_called() (+5 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.13
Nodes (12): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, analyze_document() (+4 more)

### Community 28 - "casedb_adapter.py"
Cohesion: 0.11
Nodes (26): analyzer_version(), _bodies(), case_to_document(), finding_to_ai_result(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case() (+18 more)

### Community 29 - "meta_json.py"
Cohesion: 0.08
Nodes (36): doc_from_node(), Publisher, ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), _cards(), clean_text() (+28 more)

### Community 30 - "RuntimeError"
Cohesion: 0.07
Nodes (30): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+22 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.14
Nodes (8): canonical_ad_url(), doc(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_identity_and_url(), test_login_redirect_blocked_and_overlays_removed_without_clicks(), test_non_dco_ad_without_testid_is_scoped_from_sponsored_label(), test_replay_without_fixture_is_a_source_error()

### Community 32 - "OllamaClient"
Cohesion: 0.08
Nodes (15): embed_document_text(), OllamaClient, TestEmbedDocumentText, handler(), _real_client(), load_case(), main(), print_table() (+7 more)

### Community 33 - "analyze"
Cohesion: 0.14
Nodes (7): AnalyzerConfig, EntityResolution, _det(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults, TestRegulyR4, TestWarstwyWektorowej

### Community 34 - "argparse"
Cohesion: 0.09
Nodes (11): main(), main(), FacebookConfig, blob_store_from_env(), BlobStore, LocalBlobStore, S3BlobStore, source() (+3 more)

### Community 35 - "re"
Cohesion: 0.17
Nodes (4): finding_row(), _row_to_document(), SqlStore, UpsertResult

### Community 36 - "test_change_detect.py"
Cohesion: 0.26
Nodes (24): detect_change(), diff_rule_results(), ChangeKind, RiskLevel, _doc(), _finding(), _r(), test_brak_embeddingu_degraduje_do_simhasha_bez_wyjatku() (+16 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.24
Nodes (21): det_fallback_results(), _by(), _doc(), _doc2(), _node(), _run(), test_brak_probe_nic_nie_liczy(), test_brak_wezla_ryzyka_to_na_ze_wskazaniem_reguly_3() (+13 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.12
Nodes (9): assess_rule_3(), _result(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestProporcjonalnosciCzcionki (+1 more)

### Community 39 - "rules_hybrid.py"
Cohesion: 0.09
Nodes (13): TextNode, ViewportProbe, _center_y(), _first_match_offset(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline() (+5 more)

### Community 40 - "test_guards.py"
Cohesion: 0.16
Nodes (32): Verdict, apply_rule_10_override(), _res(), _run(), test_12a_jeden_rok_pass_zamieniony_na_fail(), test_12a_nie_zamienia_fail_na_pass(), test_12a_pelny_okres_zostaje_pass(), test_12b_pass_bez_walut_i_oplat_to_fail() (+24 more)

### Community 41 - "FacebookAdsSource"
Cohesion: 0.13
Nodes (4): MediaItem, SourceBlocked, SourceError, FacebookAdsSource

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.11
Nodes (6): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), TestKorpusuNaTejMaszynie, TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.18
Nodes (13): AdvertiserRef, ChangeEvent, ChangeSimilarity, Embedding, Entities, Finding, InvestmentFirmRef, MediaItem (+5 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.08
Nodes (16): build_facebook_source(), discover_job(), fetch_job(), _redis(), Jak to działa, CircuitBreaker, NodeCache, RateLimiter (+8 more)

### Community 46 - "analyze"
Cohesion: 0.31
Nodes (3): analyze(), DemoTests, segments()

### Community 47 - "store.py"
Cohesion: 0.16
Nodes (17): BBox, RenderProbe, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score() (+9 more)

### Community 48 - "guards.py"
Cohesion: 0.16
Nodes (14): normalize(), apply_guards(), _guard_rule_12a(), _guard_rule_12b(), _guard_rule_14(), _guard_rule_16(), _guard_rule_17(), _guard_rule_2() (+6 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.16
Nodes (12): scaling_payload(), _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera() (+4 more)

### Community 51 - "parametrize"
Cohesion: 0.10
Nodes (15): alert_payload(), coverage(), create_app(), get_document(), get_finding(), health(), list_findings(), patch_finding() (+7 more)

### Community 52 - "scaling.py"
Cohesion: 0.11
Nodes (18): CZĘŚĆ A — Autoskaler, Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera, Zadanie 3: Endpoint `/scaling`, Zadanie 4: Executor `pool`, _connection(), _int(), _parse() (+10 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.18
Nodes (13): feed_fold_evidence(), platform_rule_override(), test_feed_fold_hybrid_evidence_from_document_text(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "stt.py"
Cohesion: 0.13
Nodes (3): TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZgodnosciKolejkiMiedzySerwisami

### Community 55 - "test_partial_guard.py"
Cohesion: 0.35
Nodes (9): _doc(), _rule(), _run(), test_partial_fail_braku_staje_sie_na(), test_partial_fail_obecnosci_zostaje(), test_partial_regula_10_i_pass_bez_zmian(), test_pelna_transkrypcja_bez_zmian(), test_reguly_brakujacego_zastrzezenia_sa_degradowane() (+1 more)

### Community 56 - "test_pool.py"
Cohesion: 0.12
Nodes (14): DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne(), test_apply_startuje_brakujace_workery() (+6 more)

### Community 57 - "pytest"
Cohesion: 0.19
Nodes (13): load_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany(), test_plik_yaml_zgodny_z_domyslna_konfiguracja(), test_uszkodzony_yaml_daje_domyslna_konfiguracje() (+5 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.14
Nodes (14): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+6 more)

### Community 59 - "QueueState"
Cohesion: 0.27
Nodes (13): _no_states(), decide(), QueueState, test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie(), test_limit_globalny_zdejmuje_z_kolejki_o_najmniejszym_backlogu() (+5 more)

### Community 60 - "transcribe"
Cohesion: 0.14
Nodes (12): _default_transcriber(), run(), SttError, transcribe(), test_transcribe_empty_result(), test_transcribe_passes_through_stt_error(), boom(), test_transcribe_skips_empty_segments() (+4 more)

### Community 61 - "AnalyzerConfig"
Cohesion: 0.14
Nodes (3): _doc(), TestKolejnosciEtapow, TestWywolaniaTranskrypcji

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.14
Nodes (9): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - stos docker-compose (projekt `investwatch`), Metryki do panelu, Ollama, Serwisy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth (+1 more)

### Community 63 - "test_facebook_rules.py"
Cohesion: 0.14
Nodes (9): AdDocument, Finding, main(), seed(), document_row(), _iso(), open_store(), SqliteStore (+1 more)

### Community 64 - "os"
Cohesion: 0.11
Nodes (5): _Handler, health_payload(), _scaling_response(), TestPowtarzalnosciModelu, TestZaleznosci

### Community 65 - "default_config"
Cohesion: 0.18
Nodes (9): add_asset(), Asset, Case, claim(), save_ai_result(), save_case(), set_columns(), set_status() (+1 more)

### Community 66 - "test_demo.py"
Cohesion: 0.24
Nodes (7): from_ad_document(), from_youtube(), youtube_video_id(), case_id_for(), Content, test_facebook_mapping_keeps_document_id_and_drops_embedding(), test_youtube_mapping_is_stable()

### Community 67 - "AGENTS.md - services/casedb"
Cohesion: 0.15
Nodes (12): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 6. Idempotencja — warunek, żeby to nie było śmietnikiem (+4 more)

### Community 68 - "InvestWatch — stan projektu"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Trafność Modułu 2 — pomiary na żywym Bieliku 4.5B (21.11, noc), 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły, InvestWatch — stan projektu (+8 more)

### Community 69 - "services"
Cohesion: 0.13
Nodes (14): name, networks, investwatch, image, networks, ports, volumes, services (+6 more)

### Community 70 - "valkey"
Cohesion: 0.36
Nodes (8): seaweedfs, valkey, depends_on, depends_on, depends_on, condition, condition, depends_on

### Community 71 - "export.py"
Cohesion: 0.16
Nodes (6): coverage(), failed_rules(), max_breach_severity(), TestCoverage, TestFailedRules, TestMaxBreachSeverity

### Community 72 - "scraper: FacebookAdsSource (Meta Ad Library)"
Cohesion: 0.20
Nodes (6): `.env`, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: FacebookAdsSource (Meta Ad Library), start_background(), Demo INVESTWATCH

### Community 73 - "test_demo.py"
Cohesion: 0.14
Nodes (7): 6. Do udoskonalenia — uszeregowane po wpływie na demo, evidence(), find_targets(), host(), make_clips(), normalize(), signals_in()

### Community 74 - "healthcheck"
Cohesion: 0.24
Nodes (14): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+6 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 76 - "ApiClient"
Cohesion: 0.23
Nodes (6): Task 1: Analyzer zapisuje dokument w API przed findingiem, ApiClient, ApiError, _check_local(), _resolve_document(), test_external_base_url_rejected()

### Community 77 - "test_integration_scraper.py"
Cohesion: 0.15
Nodes (3): _doc(), TestGranicyKontraktu, TestWorkeraZDetResults

### Community 78 - "test_pipeline.py"
Cohesion: 0.10
Nodes (21): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 6: Klasyfikacja zdarzenia, Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), _simhash_int(), hamming_distance() (+13 more)

### Community 79 - "test_pipeline.py"
Cohesion: 0.40
Nodes (7): Evidence, RuleResult, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.48
Nodes (4): collect_ads_from_dom(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.33
Nodes (5): Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach)

### Community 82 - "casedb"
Cohesion: 0.09
Nodes (23): depends_on, build, condition, depends_on, environment, networks, ports, restart (+15 more)

### Community 83 - "ingest.py"
Cohesion: 0.33
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.22
Nodes (9): build, env_file, environment, extra_hosts, networks, restart, API_BASE_URL, OLLAMA_BASE_URL (+1 more)

### Community 86 - "json"
Cohesion: 0.09
Nodes (11): items(), test_tylko_jedna_reklama_ma_render_probe(), main(), download_direct(), download_ytdlp(), probe_duration(), ads_from_html(), test_document_matches_frozen_contract() (+3 more)

### Community 87 - "test_eval_rules.py"
Cohesion: 0.23
Nodes (6): _row(), test_kolejnosc_regul_numeryczna(), test_metryki_macierz_pomylek(), test_pending_nie_wchodzi_do_macierzy(), test_tabela_zawiera_reguly(), test_walidacja_odrzuca_nieznana_regule()

### Community 88 - "casedb"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "risk_level"
Cohesion: 0.18
Nodes (4): 5. Typy zdarzeń, risk_level(), TestEskalacjiPoNajciezszymNaruszeniu, TestRiskLevel

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.24
Nodes (18): assess_rule_13(), rule_13_runner(), _doc(), _node(), test_brak_wynikow_historycznych_to_not_applicable(), test_cytat_to_doslowny_tekst_wezla(), test_naglowek_z_wynikiem_najwiekszy_to_fail(), test_niewidoczny_wezel_historyczny_nie_liczy_sie() (+10 more)

### Community 92 - "_doc"
Cohesion: 0.17
Nodes (6): _load(), main(), _write(), connect(), migrate(), conn()

### Community 93 - "test_api.py"
Cohesion: 0.18
Nodes (21): client(), load(), seeded(), store(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless(), test_document_upsert_returns_200_second_time(), test_embedding_survives_roundtrip() (+13 more)

### Community 94 - "module3.py"
Cohesion: 0.15
Nodes (9): load_prompt(), advisory_signals(), mentions_financial_instrument(), _na(), _result(), _normalize(), test_falszywy_przyjaciel_newsletter(), test_fleksja_sygnalow() (+1 more)

### Community 95 - "batching.py"
Cohesion: 0.15
Nodes (6): candidates(), metadata(), QuietLogger, run(), worker(), ydl_options()

### Community 96 - "Engine"
Cohesion: 0.31
Nodes (8): Engine, missing_det_placeholders(), _doc(), _res(), test_nie_dubluje_regul_ze_scrapera(), test_placeholdery_nie_zmieniaja_ryzyka_a_obnizaja_coverage(), test_powod_gdy_probe_jest_ale_brak_wyniku(), test_wszystkie_pieciu_gdy_brak_wynikow_i_probe()

### Community 98 - "context"
Cohesion: 0.20
Nodes (10): context, build, build, build, web, build, networks, ports (+2 more)

### Community 99 - "demo.py"
Cohesion: 0.20
Nodes (7): load_inputs(), main(), save(), scan(), transcript(), request(), validate_inputs()

### Community 102 - "evaluate_batch_2"
Cohesion: 0.35
Nodes (4): evaluate_batch_2(), _client(), _doc(), TestOverrideWBatch2

### Community 103 - "test_casedb_bridge.py"
Cohesion: 0.06
Nodes (22): claim(), connect(), fetch_case(), _jsonb(), _plain(), process_cases(), save_ai_result(), set_status() (+14 more)

### Community 105 - "BaseModel"
Cohesion: 0.18
Nodes (9): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+1 more)

### Community 107 - "batching.py"
Cohesion: 0.21
Nodes (5): LlmError, _all_not_applicable(), _build_result(), evaluate_batch(), _not_applicable()

### Community 114 - "parse_args"
Cohesion: 0.15
Nodes (6): serve(), main(), parse_args(), _start_health_server(), run(), TestFlagiKolejkiWWorkerze

### Community 115 - "default_config"
Cohesion: 0.13
Nodes (15): analyzer — Moduł 2 (analiza AI), analyzer — Moduły Analityczne / AI, Brama zakresu, Brama zakresu — najważniejsza decyzja domenowa, Co trzeba zrobić dalej (kolejność ma znaczenie), Konfiguracja, Mapa plików, Quick Start (+7 more)

### Community 116 - "change_detect.py"
Cohesion: 0.15
Nodes (11): _basis(), _cosine(), event(), detect_disappeared(), _have_embeddings(), _new_event(), _rule_phrase(), _transitions() (+3 more)

### Community 117 - "AnalyzerConfig"
Cohesion: 0.29
Nodes (6): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Testy, Wymagania

### Community 119 - "scraper-ingest"
Cohesion: 0.18
Nodes (11): replicas, command, deploy, env_file, image, networks, restart, shm_size (+3 more)

### Community 120 - "environment"
Cohesion: 0.51
Nodes (11): FB_FIXTURES_DIR, S3_ACCESS_KEY, S3_ENDPOINT, S3_SECRET_KEY, SCRAPER_OUTPUT_FUNC, SCRAPER_OUTPUT_QUEUE, VALKEY_URL, environment (+3 more)

### Community 121 - "TranscriptSegment"
Cohesion: 0.24
Nodes (6): TranscriptSegment, speech_rate(), _fake_transcriber(), licznik(), test_speech_rate_basic(), test_speech_rate_zero_duration_no_crash()

### Community 122 - "Enum"
Cohesion: 0.29
Nodes (7): ChangeKind, Engine, EvidenceKind, Relation, RiskLevel, ScopeStatus, Verdict

### Community 123 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### Community 125 - "stt.py"
Cohesion: 0.22
Nodes (4): _first_match_start(), normalize_text(), RiskTiming, test_normalize_strips_diacritics()

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Korekty niespojnosci danych (nie dopasowanie do wyniku), Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

### Community 132 - "re"
Cohesion: 0.06
Nodes (36): Decyzje, Docelowa topologia (`infra/docker-compose.yml`, projekt `investwatch`), Global Constraints, Pełna infrastruktura w Dockerze — projekt i plan, Spec (wiążący), Task 2: Obraz scrapera, launchery workera i harmonogramu, Task 3: Compose — wszystkie serwisy, `.env.example`, Task 4: Dokumentacja uruchomienia i instrukcja „po git pull” dla czatów (+28 more)

### Community 133 - "_rule_6"
Cohesion: 0.19
Nodes (13): AdDocument, _dominant_font_px(), _evidence(), _na(), _result(), _risk_hits(), _rule_4(), _rule_5() (+5 more)

### Community 134 - "test_pipeline.py"
Cohesion: 0.18
Nodes (4): cosine(), knn_score(), TestCosine, TestKnnScore

### Community 135 - "scheduler"
Cohesion: 0.25
Nodes (8): command, env_file, image, networks, restart, shm_size, volumes, scheduler

### Community 136 - "scraper-render"
Cohesion: 0.25
Nodes (8): command, env_file, image, networks, restart, shm_size, volumes, scraper-render

### Community 139 - "x-scraper"
Cohesion: 0.29
Nodes (7): x-scraper, env_file, image, networks, restart, shm_size, volumes

### Community 140 - "InvestWatch"
Cohesion: 0.29
Nodes (6): Instalacja Dockera na Windows, InvestWatch, Po `git pull`, Struktura, Uruchomienie, Wymagania sprzętowe

### Community 141 - "is_flagged"
Cohesion: 0.33
Nodes (3): is_flagged(), Co już jest (gotowe i przetestowane), TestIsFlagged

### Community 142 - "T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)"
Cohesion: 0.50
Nodes (4): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)

### Community 144 - "Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY), Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości

### Community 145 - "Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości, Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)

### Community 146 - "_llm"
Cohesion: 0.29
Nodes (5): handler(), _llm(), test_document_id_nie_wola_post_document(), test_health_ollama_down_is_degraded_not_fatal(), test_health_ollama_up()

### Community 149 - "ollama"
Cohesion: 0.33
Nodes (6): image, networks, profiles, restart, volumes, ollama

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1011 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `_rule_6` to `test_registry.py`, `rule_3_runner`, `test_worker.py`, `test_pipeline.py`, `evaluate_batch_1`, `analyzer/contracts.py`, `test_module3.py`, `test_lang_consistency.py`, `_client`, `InvestWatch — plan wykonawczy 23 h`, `typing`, `_ensure_vector_representation`, `AdDocument`, `RuleResult`, `test_casedb_bridge.py`, `casedb_adapter.py`, `meta_json.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `argparse`, `re`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_hybrid.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `store.py`, `parametrize`, `test_partial_guard.py`, `pytest`, `eval_rules.py`, `AnalyzerConfig`, `test_facebook_rules.py`, `ApiClient`, `test_integration_scraper.py`, `test_pipeline.py`, `test_pipeline.py`, `json`, `test_rule_13.py`, `test_api.py`, `module3.py`, `Engine`, `evaluate_batch_2`, `batching.py`, `change_detect.py`, `TranscriptSegment`, `stt.py`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Are the 163 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 163 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07764705882352942 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `test_guards.py` to `test_registry.py`, `_rule_6`, `Relation`, `test_pipeline.py`, `risk_score`, `evaluate_batch_1`, `analyzer/contracts.py`, `test_module3.py`, `test_lang_consistency.py`, `_client`, `RuleResult`, `AdDocument`, `test_casedb_bridge.py`, `casedb_adapter.py`, `OllamaClient`, `analyze`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_hybrid.py`, `store.py`, `guards.py`, `test_partial_guard.py`, `eval_rules.py`, `export.py`, `test_integration_scraper.py`, `test_pipeline.py`, `risk_level`, `test_rule_13.py`, `module3.py`, `Engine`, `evaluate_batch_2`, `test_casedb_bridge.py`, `batching.py`, `change_detect.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 75 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 75 INFERRED edges - model-reasoned connections that need verification._
- **Should `Relation` be split into smaller, more focused modules?**
  _Cohesion score 0.0726764500349406 - nodes in this community are weakly interconnected._