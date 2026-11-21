# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 164 files · ~1,128,392 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: .gz 8, (none) 7, .example 3)

## Summary
- 2425 nodes · 6194 edges · 141 communities (99 shown, 42 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 530 edges (avg confidence: 0.92)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `b9d3f7a5`
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
- casedb_adapter.py
- FacebookAdsSource
- test_stt_pipeline.py
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- DemoTests
- store.py
- demo.py
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
- router.py
- health.py
- casedb_batch.py
- test_demo.py
- AGENTS.md - services/casedb
- pathlib
- services
- analyzer
- export.py
- scraper: FacebookAdsSource (Meta Ad Library)
- simhash
- healthcheck
- postgres
- test_gold_set.py
- test_lang_consistency.py
- _save_finding
- test_casedb.py
- collect_ads_from_dom
- Harmonogram i orkiestracja — dokument projektowy
- casedb
- ingest.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- test_worker_imports_without_rq
- test_eval_rules.py
- casedb
- Zbior zloty (gold set)
- seaweedfs
- test_rule_13.py
- preconditions.py
- test_det_placeholders.py
- TestGranicyKontraktu
- QuietLogger
- health_payload
- valkey
- web
- scan
- ApiClient
- .test_search_deduplicates_ids_and_respects_candidate_limit
- analyze
- json
- AnalyzerConfig
- ._api
- classify_similarity
- TestPolskaOdmiana
- media.py
- is_flagged
- normalize_text
- parse_args
- scraper/tests/conftest.py
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- is_language
- math
- TestKorpusuNaTejMaszynie
- TestZaleznosci

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 111 edges
2. `Verdict` - 104 edges
3. `RuleResult` - 86 edges
4. `analyze()` - 71 edges
5. `OllamaClient` - 61 edges
6. `AnalyzerConfig` - 48 edges
7. `FacebookAdsSource` - 48 edges
8. `Evidence` - 44 edges
9. `EntityResolution` - 43 edges
10. `Engine` - 39 edges

## Surprising Connections (you probably didn't know these)
- `6.1 `AdDocument` — to, co produkuje scraper` --references--> `AdDocument`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"` --references--> `AdDocument`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `6.2 `RenderProbe` — geometria renderu, podstawa reguł DET` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Jak wagi jury przekładają się na decyzje projektowe` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (141 total, 42 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.11
Nodes (19): build_config(), coverage_report(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _with_hybrid(), _all_pass_handler() (+11 more)

### Community 4 - "test_stt.py"
Cohesion: 0.20
Nodes (19): rate_anomaly(), risk_timing(), RiskTiming, test_rate_anomaly_fast_disclaimer(), test_rate_anomaly_single_segment(), test_rate_anomaly_too_few_segments(), test_rate_anomaly_zero_median(), test_risk_before_profit_gives_negative_gap() (+11 more)

### Community 5 - "test_worker.py"
Cohesion: 0.22
Nodes (16): handle_job(), _api(), _api_no_get(), test_api_error_on_get_returns_none(), test_api_error_on_post_returns_none(), test_findings_out_dir_zapisuje_json_nawet_gdy_api_pada(), test_flat_payload_z_det_results(), test_get_document_raises_api_error() (+8 more)

### Community 6 - "Relation"
Cohesion: 0.13
Nodes (10): Relation, Routing, route(), RoutingDecision, RoutingInput, _inp(), TestR1WlasnyMaterialFirmy, TestR2PodmiotTrzeci (+2 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "httpx"
Cohesion: 0.14
Nodes (16): _download(), _max_bytes(), resolve_media(), _s3_to_http(), _client(), test_http_download_and_cache_reuse(), handler(), test_http_error_status_returns_none() (+8 more)

### Community 9 - "risk_score"
Cohesion: 0.10
Nodes (11): failed_rules(), max_breach_severity(), risk_level(), risk_score(), _rule(), TestEskalacjiPoNajciezszymNaruszeniu, TestFailedRules, TestMaxBreachSeverity (+3 more)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.06
Nodes (32): 10. Pozyskiwanie danych i bezpieczeństwo demo, 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 4. Rozważone podejścia (+24 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.10
Nodes (10): Scope, ScopeStatus, classify_scope(), _find_any(), _normalize(), test_cfd_na_krypto_jest_w_zakresie_w_przykladzie(), TestCfdNaKryptoZostajeWZakresie, TestNiepewneIdaDoTriage (+2 more)

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.11
Nodes (19): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+11 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.16
Nodes (13): AdvertiserRef, BBox, Embedding, Entities, InvestmentFirmRef, MediaItem, Publisher, RegistryMatch (+5 more)

### Community 16 - "Verdict"
Cohesion: 0.11
Nodes (22): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable, _boom(), _client() (+14 more)

### Community 17 - "worker.py"
Cohesion: 0.15
Nodes (6): serve(), _build_det_results(), _build_resolution(), main(), _start_health_server(), run()

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.08
Nodes (28): A — scraper + reguły DET, A — scraper + reguły DET, A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, B — analyzer, B — analyzer, C — api + web, C — api + web (+20 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "RuleResult"
Cohesion: 0.10
Nodes (17): Układ repozytorium, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), Engine, Evidence, EvidenceKind, RuleResult, _na(), _result() (+9 more)

### Community 23 - "AdDocument"
Cohesion: 0.12
Nodes (7): normalize(), tokenize(), _doc(), _rule(), _runner(), TestAnalyze, TestNormalizacjaITokeny

### Community 25 - "test_casedb_bridge.py"
Cohesion: 0.07
Nodes (16): claim(), connect(), fetch_case(), _jsonb(), _plain(), process_cases(), save_ai_result(), set_status() (+8 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.20
Nodes (8): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, analyze_document()

### Community 28 - "test_casedb_adapter.py"
Cohesion: 0.15
Nodes (17): analyzer_version(), case_to_document(), finding_to_ai_result(), is_partial(), is_partial_transcript(), _load(), test_asset_audio_video_trafiaja_do_media(), test_brak_wszystkiego_nie_rzuca() (+9 more)

### Community 29 - "meta_json.py"
Cohesion: 0.07
Nodes (39): doc_from_node(), ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards(), clean_text() (+31 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.07
Nodes (19): main(), FacebookConfig, canonical_ad_url(), blob_store_from_env(), BlobStore, LocalBlobStore, S3BlobStore, doc() (+11 more)

### Community 32 - "OllamaClient"
Cohesion: 0.09
Nodes (13): embed_document_text(), LlmError, OllamaClient, TestEmbedDocumentText, handler(), TestPowtarzalnosciModelu, main(), print_table() (+5 more)

### Community 33 - "analyze"
Cohesion: 0.14
Nodes (7): EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults, TestRegulyR4, TestWarstwyWektorowej

### Community 34 - "rules_hybrid.py"
Cohesion: 0.13
Nodes (10): _center_y(), _matches(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline(), _pick_viewport(), Proximity (+2 more)

### Community 35 - "re"
Cohesion: 0.05
Nodes (32): normalize(), _first_match_offset(), apply_rule_10_override(), assess_rule_10(), detect_language(), risk_sentences(), split_sentences(), _words() (+24 more)

### Community 36 - "Verdict"
Cohesion: 0.14
Nodes (38): Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, _basis(), _cosine(), detect_change(), event(), detect_disappeared(), diff_rule_results(), _have_embeddings() (+30 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.25
Nodes (15): det_fallback_results(), _by(), _doc(), _node(), _run(), test_brak_probe_nic_nie_liczy(), test_brak_wezla_ryzyka_to_na_ze_wskazaniem_reguly_3(), test_facebook_nie_dostaje_fallbacku_typografia_meta() (+7 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.10
Nodes (10): assess_rule_3(), _result(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestProporcjonalnosciCzcionki (+2 more)

### Community 39 - "rules_det_fallback.py"
Cohesion: 0.33
Nodes (9): _evidence(), _na(), _result(), _risk_hits(), _rule_4(), _rule_5(), _rule_6(), _rule_7() (+1 more)

### Community 40 - "casedb_adapter.py"
Cohesion: 0.21
Nodes (6): _bodies(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case(), mark_partial()

### Community 41 - "FacebookAdsSource"
Cohesion: 0.09
Nodes (6): NavigationGuard, neutralize_overlays(), Source, SourceBlocked, SourceError, FacebookAdsSource

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.14
Nodes (5): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.22
Nodes (13): run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals(), test_cta_block_link_is_not_behind_interaction_but_text_link_is(), test_media_check_below_viewport_after_scroll() (+5 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.07
Nodes (43): AdDocument, AdvertiserRef, BBox, Embedding, Engine, Entities, Evidence, EvidenceKind (+35 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.08
Nodes (16): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, CircuitBreaker, NodeCache (+8 more)

### Community 46 - "DemoTests"
Cohesion: 0.31
Nodes (3): analyze(), DemoTests, segments()

### Community 47 - "store.py"
Cohesion: 0.21
Nodes (8): add_asset(), Asset, Case, save_ai_result(), save_case(), set_columns(), set_status(), test_roundtrip_export()

### Community 48 - "demo.py"
Cohesion: 0.24
Nodes (5): evidence(), find_targets(), host(), normalize(), signals_in()

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.16
Nodes (12): scaling_payload(), _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera() (+4 more)

### Community 51 - "parametrize"
Cohesion: 0.13
Nodes (3): TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZgodnosciKolejkiMiedzySerwisami

### Community 52 - "scaling.py"
Cohesion: 0.13
Nodes (15): CZĘŚĆ A — Autoskaler, Zadanie 2: Funkcja decyzyjna autoskalera, Zadanie 3: Endpoint `/scaling`, Zadanie 4: Executor `pool`, _connection(), _int(), _parse(), QueuePolicy (+7 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.14
Nodes (13): feed_fold_evidence(), FeedFoldEvidence, platform_rule_override(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "InvestWatch — stan projektu"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego, 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły (+8 more)

### Community 55 - "test_partial_guard.py"
Cohesion: 0.28
Nodes (9): _doc(), _rule(), _run(), test_partial_fail_braku_staje_sie_na(), test_partial_fail_obecnosci_zostaje(), test_partial_regula_10_i_pass_bez_zmian(), test_pelna_transkrypcja_bez_zmian(), test_reguly_brakujacego_zastrzezenia_sa_degradowane() (+1 more)

### Community 56 - "test_pool.py"
Cohesion: 0.10
Nodes (15): _default_spawn(), DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne() (+7 more)

### Community 57 - "pytest"
Cohesion: 0.19
Nodes (14): Zadanie 1: Konfiguracja skalowania i jej walidacja, load_scaling_config(), ScalingConfigError, test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+6 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.13
Nodes (15): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+7 more)

### Community 59 - "QueueState"
Cohesion: 0.30
Nodes (12): decide(), QueueState, test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie(), test_limit_globalny_zdejmuje_z_kolejki_o_najmniejszym_backlogu(), test_nie_schodzi_ponizej_min_ani_nie_rosnie_powyzej_max() (+4 more)

### Community 60 - "stt.py"
Cohesion: 0.14
Nodes (13): _default_transcriber(), run(), SttError, transcribe(), test_stt_error_is_runtime_error(), test_transcribe_empty_result(), test_transcribe_passes_through_stt_error(), boom() (+5 more)

### Community 61 - "db.py"
Cohesion: 0.21
Nodes (3): connect(), migrate(), conn()

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.18
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth

### Community 63 - "router.py"
Cohesion: 0.24
Nodes (6): _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _matches_any(), TestHasProfitClaims

### Community 64 - "health.py"
Cohesion: 0.20
Nodes (3): _Handler, _no_states(), _scaling_response()

### Community 65 - "casedb_batch.py"
Cohesion: 0.15
Nodes (9): default_config(), test_default_config_ma_wszystkie_runnery_modulu_2(), test_default_config_wpina_whisper_gdy_wlaczony(), test_worker_bez_configu_uzywa_pelnego_potoku(), main(), make_analyzer(), analyze_case(), run_file() (+1 more)

### Community 67 - "AGENTS.md - services/casedb"
Cohesion: 0.18
Nodes (9): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+1 more)

### Community 68 - "pathlib"
Cohesion: 0.11
Nodes (7): _fake_llm(), _no_psycopg(), test_tryb_plikowy_z_fake_llm(), failing(), load_case(), score_one(), update_gold()

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

### Community 73 - "simhash"
Cohesion: 0.05
Nodes (35): CZĘŚĆ B — Detektor zmian, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 6: Klasyfikacja zdarzenia, Zadanie 7: Brama idempotencji przed kolejką GPU (+27 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 77 - "test_lang_consistency.py"
Cohesion: 0.35
Nodes (4): evaluate_batch_2(), _client(), _doc(), TestOverrideWBatch2

### Community 79 - "test_casedb.py"
Cohesion: 0.29
Nodes (3): claim(), test_claim_is_exclusive(), worker()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.48
Nodes (4): collect_ads_from_dom(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.14
Nodes (14): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+6 more)

### Community 82 - "casedb"
Cohesion: 0.29
Nodes (6): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Testy, Wymagania

### Community 83 - "ingest.py"
Cohesion: 0.22
Nodes (7): from_ad_document(), from_youtube(), youtube_video_id(), case_id_for(), Content, test_facebook_mapping_keeps_document_id_and_drops_embedding(), test_youtube_mapping_is_stable()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.20
Nodes (10): environment, environment, networks, ports, profiles, API_BASE_URL, OLLAMA_BASE_URL, S3_ENDPOINT (+2 more)

### Community 87 - "test_eval_rules.py"
Cohesion: 0.23
Nodes (6): _row(), test_kolejnosc_regul_numeryczna(), test_metryki_macierz_pomylek(), test_pending_nie_wchodzi_do_macierzy(), test_tabela_zawiera_reguly(), test_walidacja_odrzuca_nieznana_regule()

### Community 88 - "casedb"
Cohesion: 0.33
Nodes (6): environment, networks, restart, volumes, DATABASE_URL, casedb

### Community 89 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.17
Nodes (20): TextNode, assess_rule_13(), _na(), _result(), rule_13_runner(), _doc(), _node(), test_brak_wynikow_historycznych_to_not_applicable() (+12 more)

### Community 92 - "preconditions.py"
Cohesion: 0.09
Nodes (13): AdDocument, load_prompt(), evaluate_batch_3(), evaluate_batch_4(), evaluate_batch(), mentions_historical_performance(), _client_returning_fail(), _client_that_must_not_be_called() (+5 more)

### Community 93 - "test_det_placeholders.py"
Cohesion: 0.16
Nodes (9): missing_det_placeholders(), coverage(), _doc(), _res(), test_nie_dubluje_regul_ze_scrapera(), test_placeholdery_nie_zmieniaja_ryzyka_a_obnizaja_coverage(), test_powod_gdy_probe_jest_ale_brak_wyniku(), test_wszystkie_pieciu_gdy_brak_wynikow_i_probe() (+1 more)

### Community 96 - "health_payload"
Cohesion: 0.33
Nodes (5): health_payload(), handler(), _llm(), test_health_ollama_down_is_degraded_not_fatal(), test_health_ollama_up()

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.20
Nodes (10): build, build, context, build, web, build, depends_on, networks (+2 more)

### Community 99 - "scan"
Cohesion: 0.38
Nodes (5): load_inputs(), main(), save(), scan(), validate_inputs()

### Community 100 - "ApiClient"
Cohesion: 0.21
Nodes (5): ApiClient, ApiError, _check_local(), _resolve_document(), test_external_base_url_rejected()

### Community 101 - ".test_search_deduplicates_ids_and_respects_candidate_limit"
Cohesion: 0.25
Nodes (4): candidates(), metadata(), run(), ydl_options()

### Community 102 - "analyze"
Cohesion: 0.16
Nodes (5): analyze(), _crashed_rule_result(), _ensure_transcript(), _ensure_vector_representation(), guard_partial_result()

### Community 103 - "json"
Cohesion: 0.13
Nodes (11): test_analyzable_text_zawiera_transkrypcje(), test_przyklad_waliduje_sie_przeciw_modelowi(), test_tempo_segmentu_transkryptu_jest_liczone(), main(), _load(), main(), _write(), test_cli_ingest_and_export() (+3 more)

### Community 117 - "AnalyzerConfig"
Cohesion: 0.17
Nodes (4): AnalyzerConfig, _doc(), TestKolejnosciEtapow, TestWywolaniaTranskrypcji

### Community 124 - "media.py"
Cohesion: 0.24
Nodes (3): download_direct(), download_ytdlp(), probe_duration()

### Community 125 - "is_flagged"
Cohesion: 0.14
Nodes (10): is_flagged(), analyzer — Moduły Analityczne / AI, Brama zakresu — najważniejsza decyzja domenowa, Co już jest (gotowe i przetestowane), Co trzeba zrobić dalej (kolejność ma znaczenie), Quick start, Regeneracja przykładów kontraktów, Weryfikacja cytatu — zabezpieczenie przed halucynacją (+2 more)

### Community 126 - "normalize_text"
Cohesion: 0.22
Nodes (6): _first_match_start(), normalize_text(), speech_rate(), test_normalize_strips_diacritics(), test_speech_rate_basic(), test_speech_rate_zero_duration_no_crash()

### Community 128 - "scraper/tests/conftest.py"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.33
Nodes (5): Cel, Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 828 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `preconditions.py` to `test_registry.py`, `evaluate_batch_1`, `analyzer/contracts.py`, `Verdict`, `worker.py`, `_client`, `InvestWatch — plan wykonawczy 23 h`, `RuleResult`, `AdDocument`, `test_casedb_adapter.py`, `meta_json.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `rules_hybrid.py`, `Verdict`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_det_fallback.py`, `casedb_adapter.py`, `FacebookAdsSource`, `scraper/contracts.py`, `test_partial_guard.py`, `eval_rules.py`, `stt.py`, `pathlib`, `simhash`, `test_lang_consistency.py`, `test_rule_13.py`, `test_det_placeholders.py`, `ApiClient`, `analyze`, `json`, `AnalyzerConfig`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `AdDocument` (e.g. with `6.1 `AdDocument` — to, co produkuje scraper` and `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"`) actually correct?**
  _`AdDocument` has 38 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11428571428571428 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `Verdict` to `test_registry.py`, `risk_score`, `evaluate_batch_1`, `analyzer/contracts.py`, `Verdict`, `_client`, `RuleResult`, `AdDocument`, `OllamaClient`, `analyze`, `rules_hybrid.py`, `re`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_det_fallback.py`, `scraper/contracts.py`, `test_partial_guard.py`, `eval_rules.py`, `casedb_batch.py`, `pathlib`, `test_lang_consistency.py`, `test_rule_13.py`, `preconditions.py`, `test_det_placeholders.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Should `Relation` be split into smaller, more focused modules?**
  _Cohesion score 0.13054187192118227 - nodes in this community are weakly interconnected._