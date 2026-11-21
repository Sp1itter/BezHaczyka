# Graph Report - modul1-domkniecie  (2026-11-21)

## Corpus Check
- 321 files · ~1,240,276 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 42 file(s) not represented in the graph (top: (none) 18, .gz 8, .example 3)

## Summary
- 3907 nodes · 10398 edges · 206 communities (174 shown, 32 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 1075 edges (avg confidence: 0.92)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `0d879c51`
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
- Zbior zloty (gold set)
- InvestWatch — dokument projektowy (design doc)
- evaluate_batch_1
- classify_scope
- _file
- test_config.py
- analyzer/contracts.py
- test_collector.py
- test_lang_consistency.py
- test_scaling_runtime.py
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- Engine
- LocalCorpusSource
- Enum
- OllamaClient
- Integracja serwisów — kto wywołuje kogo
- test_casedb_adapter.py
- meta_json.py
- RuntimeError
- test_facebook_contract.py
- json
- analyze
- www.py
- re
- test_change_detect.py
- test_rules_det_fallback.py
- assess_rule_3
- scheduler.py
- test_guards.py
- FacebookAdsSource
- test_stt_pipeline.py
- test_render_probe.py
- scraper/contracts.py
- CircuitBreaker
- os
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
- UrlStore
- dashboard/src/lib/labels.js
- infra – stos Docker Compose (projekt `investwatch`)
- seed.py
- health.py
- casedb/store.py
- test_demo.py
- AGENTS.md - services/casedb
- InvestWatch — stan projektu
- services
- postgres
- risk_score
- scraper: Moduł 1 (facebook, youtube, www)
- resolve
- healthcheck
- postgres
- analyzer/worker.py
- TestWorkeraZDetResults
- test_pipeline.py
- test_pipeline.py
- collect_ads_from_dom
- Harmonogram i orkiestracja — dokument projektowy
- api
- ingest.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- media.py
- test_eval_rules.py
- casedb
- test_rules_det.py
- seaweedfs
- test_rule_13.py
- _doc
- test_api.py
- re
- Registry
- collect.py
- api/store.py
- dashboard
- youtube.py
- knf.py
- dashboard/src/App.jsx
- evaluate_batch_2
- test_casedb_bridge.py
- RuleResult
- BaseModel
- test_casedb.py
- llm.py
- parse_args
- default_config
- change_detect.py
- AnalyzerConfig
- eval_module1.py
- scraper-worker
- environment
- typing
- resolver.py
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- lexicons.py
- web/package.json
- README.md
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- knf_snapshot.py
- logging
- _rule_6
- cosine
- scheduler
- dashboard/package.json
- AlertHub
- test_pipeline.py
- knf_registry.py
- InvestWatch
- client.js
- T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)
- YouTubeSource
- Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)
- Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)
- weights
- AdDocument
- ollama
- Rotator
- check_compliance.py
- _default_spawn
- data.js
- views/Calibration.jsx
- from_facebook_node
- reresolve.py
- server.js
- components/Calibration.jsx
- test_report_module1.py
- Module1.jsx
- test_live_polaczenie_i_claim_zerowego_limitu
- Global Constraints
- collector/scoring.py
- Global Constraints
- context
- FakeConn
- casedb_batch.py
- jobs
- test_www.py
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- casedb_bridge.py
- preconditions.py
- test_gold_set.py
- knn_score
- read_registry_csv
- TestGranicyKontraktu
- .test_niedostepny_model_daje_none_nie_wyjatek
- has_disclosure
- Moduł 1 – przepływ danych i kontrakty
- casedb
- parametrize
- scripts
- _Extractor
- api (osoba C)
- _Cur
- worker
- dashboard
- 10. Pozyskiwanie danych i bezpieczeństwo demo
- 8. Logika modułów
- 9. Scoring, threshold i metryki
- Zbiór z etykietami Modułu 1
- finding_to_ai_result
- facebook
- S3BlobStore
- 2. Cele, nie-cele, anty-cele
- 4. Rozważone podejścia
- T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle)
- _fake_llm
- TestZaleznosci
- queries_from_registry
- FakeConn
- audit.sh
- casedb

## God Nodes (most connected - your core abstractions)
1. `Verdict` - 216 edges
2. `AdDocument` - 203 edges
3. `RuleResult` - 133 edges
4. `analyze()` - 76 edges
5. `Engine` - 66 edges
6. `OllamaClient` - 62 edges
7. `EvidenceKind` - 61 edges
8. `FacebookAdsSource` - 61 edges
9. `Evidence` - 53 edges
10. `EntityResolution` - 52 edges

## Surprising Connections (you probably didn't know these)
- `Osoba C — `services/api`, `services/web`` --references--> `ApiClient`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/api_client.py
- `Zadanie 5: Kontrakt `ChangeEvent` i diff reguł` --references--> `diff_rule_results()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-harmonogram-implementacja.md → services/analyzer/analyzer/change_detect.py
- `B — analyzer` --references--> `knn_score()`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-plan-24h.md → services/analyzer/analyzer/embeddings.py
- `Jak dodac pozycje` --references--> `risk_score()`  [INFERRED]
  fixtures/gold/README.md → services/analyzer/analyzer/scoring.py
- `4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py

## Import Cycles
- None detected.

## Communities (206 total, 32 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.12
Nodes (19): build_config(), coverage_report(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key(), _with_hybrid(), _all_pass_handler() (+11 more)

### Community 4 - "test_stt.py"
Cohesion: 0.08
Nodes (37): _default_transcriber(), run(), _transcribe(), rate_anomaly(), risk_timing(), RiskTiming, speech_rate(), SttError (+29 more)

### Community 5 - "test_worker.py"
Cohesion: 0.07
Nodes (41): ChangeEvent, health_payload(), analyze_document(), handle_job(), Integracja z bazą (casedb, Moduł 1), _api(), handler(), _api_no_get() (+33 more)

### Community 6 - "Relation"
Cohesion: 0.09
Nodes (16): Routing, _blank(), _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), mask_non_claims(), _matches_any() (+8 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "httpx"
Cohesion: 0.05
Nodes (41): _download(), _max_bytes(), resolve_media(), _s3_to_http(), advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _client() (+33 more)

### Community 9 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.18
Nodes (10): 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 5. Architektura, 7. Mapowanie 18 reguł na silniki, InvestWatch — dokument projektowy (design doc) (+2 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.09
Nodes (7): classify_scope(), _find_any(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania, TestZwykleInstrumenty

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.11
Nodes (19): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+11 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.07
Nodes (29): _bodies(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case(), is_partial_transcript(), mark_partial(), AdvertiserRef (+21 more)

### Community 16 - "test_collector.py"
Cohesion: 0.09
Nodes (32): reprioritize(), affiliate_params(), score(), cand(), cfg(), FakeSource, files(), _golden() (+24 more)

### Community 17 - "test_lang_consistency.py"
Cohesion: 0.15
Nodes (5): assess_rule_10(), _result(), detect_language(), TestAssessRule10, TestDetectLanguage

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.12
Nodes (16): Co zmieniło się po review zespołu (wersja 2), Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate, Podział roli, Rejestr ryzyk, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min) (+8 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "Engine"
Cohesion: 0.09
Nodes (18): Engine, Evidence, EvidenceKind, missing_det_placeholders(), _na(), _result(), _crashed_rule_result(), guard_partial_result() (+10 more)

### Community 23 - "LocalCorpusSource"
Cohesion: 0.16
Nodes (7): run(), LocalCorpusSource, results(), test_document_id_independent_of_url(), test_documents_follow_contract(), test_page_verdicts_match_labels(), test_source_protocol_and_discover_urls()

### Community 24 - "Enum"
Cohesion: 0.13
Nodes (30): App(), TABS, Alerts(), Evidence(), FindingDetail(), Module3(), ORDER, verdictOf() (+22 more)

### Community 25 - "OllamaClient"
Cohesion: 0.08
Nodes (14): OllamaClient, evaluate_batch_3(), evaluate_batch_4(), _client_returning_fail(), _client_that_must_not_be_called(), handler(), _doc(), TestBramkiWsadu3 (+6 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.29
Nodes (7): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem

### Community 28 - "test_casedb_adapter.py"
Cohesion: 0.29
Nodes (13): case_to_document(), is_partial(), _load(), test_asset_audio_video_trafiaja_do_media(), test_brak_wszystkiego_nie_rzuca(), test_content_transcript_ma_priorytet_nad_raw(), test_facebook_bez_raw_sklada_dokument_z_content(), test_facebook_raw_uzupelnia_transkrypcje_i_media_z_content_assets() (+5 more)

### Community 29 - "meta_json.py"
Cohesion: 0.09
Nodes (37): Publisher, ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards(), clean_text() (+29 more)

### Community 30 - "RuntimeError"
Cohesion: 0.09
Nodes (27): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+19 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.08
Nodes (19): fetch(), _fb_source_factory(), main(), FacebookConfig, canonical_ad_url(), LocalBlobStore, test_no_proxy_by_default(), doc() (+11 more)

### Community 32 - "json"
Cohesion: 0.07
Nodes (23): test_analyzable_text_zawiera_transkrypcje(), test_finding_moze_nalezec_do_wielu_modulow(), test_przyklad_waliduje_sie_przeciw_modelowi(), test_rule_result_ma_dowod_dla_kazdego_werdyktu(), test_tempo_segmentu_transkryptu_jest_liczone(), doc_from_node(), load_case(), main() (+15 more)

### Community 33 - "analyze"
Cohesion: 0.07
Nodes (19): analyze(), AnalyzerConfig, _ensure_transcript(), _ensure_vector_representation(), EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie (+11 more)

### Community 34 - "www.py"
Cohesion: 0.10
Nodes (5): _is_page_link(), _origin(), _Page, WebPageSource, BlobStore

### Community 35 - "re"
Cohesion: 0.13
Nodes (7): AdDocument, Finding, document_row(), finding_row(), _row_to_document(), SqlStore, UpsertResult

### Community 36 - "test_change_detect.py"
Cohesion: 0.26
Nodes (24): detect_change(), diff_rule_results(), ChangeKind, RiskLevel, _doc(), _finding(), _r(), test_brak_embeddingu_degraduje_do_simhasha_bez_wyjatku() (+16 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.24
Nodes (21): det_fallback_results(), _by(), _doc(), _doc2(), _node(), _run(), test_brak_probe_nic_nie_liczy(), test_brak_wezla_ryzyka_to_na_ze_wskazaniem_reguly_3() (+13 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.07
Nodes (17): TranscriptSegment, assess_rule_3(), _result(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline(), Proximity (+9 more)

### Community 39 - "scheduler.py"
Cohesion: 0.09
Nodes (19): expand(), JobSpec, load_schedule(), main(), register(), _registry_queries(), run_once(), Task (+11 more)

### Community 40 - "test_guards.py"
Cohesion: 0.13
Nodes (34): Verdict, apply_guards(), apply_rule_10_override(), mentions_historical_performance(), _res(), _run(), test_12a_jeden_rok_pass_zamieniony_na_fail(), test_12a_nie_zamienia_fail_na_pass() (+26 more)

### Community 41 - "FacebookAdsSource"
Cohesion: 0.10
Nodes (5): SourceBlocked, SourceError, FacebookAdsSource, test_facebook_uses_shared_rotator_per_context(), test_discover_replay_yields_canonical_urls()

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.20
Nodes (4): ad_archive_id(), resolve_media_path(), _doc(), TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.13
Nodes (16): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_nodes_are_not_visible_even_with_layout_box() (+8 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.09
Nodes (22): AdvertiserRef, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities, EvidenceKind (+14 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.09
Nodes (11): CircuitBreaker, NodeCache, RateLimiter, SeenSet, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures() (+3 more)

### Community 46 - "os"
Cohesion: 0.12
Nodes (22): build_facebook_source(), build_source(), discover_job(), _enqueue_analysis(), _fetch(), fetch_job(), _job_id(), recheck_job() (+14 more)

### Community 47 - "store.py"
Cohesion: 0.17
Nodes (16): BBox, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score(), test_not_applicable_rules_stay_out_of_score_denominator() (+8 more)

### Community 48 - "guards.py"
Cohesion: 0.20
Nodes (13): normalize(), _guard_rule_12a(), _guard_rule_12b(), _guard_rule_14(), _guard_rule_16(), _guard_rule_17(), _guard_rule_2(), historical_years_covered() (+5 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.21
Nodes (9): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), _zla() (+1 more)

### Community 51 - "parametrize"
Cohesion: 0.09
Nodes (19): alert_payload(), coverage(), create_app(), get_document(), get_finding(), health(), list_findings(), patch_finding() (+11 more)

### Community 52 - "scaling.py"
Cohesion: 0.18
Nodes (9): _connection(), _int(), _parse(), QueuePolicy, _rq_backlog_reader(), _read(), _rq_worker_counter(), _count() (+1 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.14
Nodes (13): feed_fold_evidence(), FeedFoldEvidence, platform_rule_override(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "stt.py"
Cohesion: 0.10
Nodes (6): _first_match_start(), normalize_text(), TestBudowanieZCasedb, TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZgodnosciKolejkiMiedzySerwisami

### Community 55 - "test_partial_guard.py"
Cohesion: 0.35
Nodes (9): _doc(), _rule(), _run(), test_partial_fail_braku_staje_sie_na(), test_partial_fail_obecnosci_zostaje(), test_partial_regula_10_i_pass_bez_zmian(), test_pelna_transkrypcja_bez_zmian(), test_reguly_brakujacego_zastrzezenia_sa_degradowane() (+1 more)

### Community 56 - "test_pool.py"
Cohesion: 0.11
Nodes (16): Zadanie 4: Executor `pool`, DryRunExecutor, PoolExecutor, ScalingConfig, ScalingDecision, _d(), FakeSpawn, FakeWorker (+8 more)

### Community 57 - "pytest"
Cohesion: 0.19
Nodes (13): load_scaling_config(), ScalingConfigError, validate_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+5 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.13
Nodes (15): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+7 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "UrlStore"
Cohesion: 0.14
Nodes (6): Scored, _now(), PostgresUrlStore, SqliteUrlStore, UpsertOutcome, UrlStore

### Community 61 - "dashboard/src/lib/labels.js"
Cohesion: 0.18
Nodes (21): LEVELS, RiskBadge(), StatTile(), AssigneeSelect(), AssigneeTag(), FindingDetail(), VERDICT, FindingsTable() (+13 more)

### Community 62 - "infra – stos Docker Compose (projekt `investwatch`)"
Cohesion: 0.25
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, infra – stos Docker Compose (projekt `investwatch`), Metryki do panelu, Ollama, Serwisy, Szybki start: caly stos jedną komendą, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), Uwagi eksploatacyjne

### Community 63 - "seed.py"
Cohesion: 0.32
Nodes (4): main(), seed(), open_store(), test_seed_loads_contract_examples()

### Community 64 - "health.py"
Cohesion: 0.12
Nodes (5): _Handler, _no_states(), _scaling_response(), _FakeApi, test_worker_bez_configu_uzywa_pelnego_potoku()

### Community 65 - "casedb/store.py"
Cohesion: 0.13
Nodes (13): cases_for_recheck(), claim(), get_document(), _jsonb(), _plain(), report_module1(), save_ai_result(), save_change_event() (+5 more)

### Community 66 - "test_demo.py"
Cohesion: 0.18
Nodes (13): from_ad_document(), from_youtube(), youtube_video_id(), add_asset(), Asset, Case, case_id_for(), Content (+5 more)

### Community 67 - "AGENTS.md - services/casedb"
Cohesion: 0.14
Nodes (13): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+5 more)

### Community 68 - "InvestWatch — stan projektu"
Cohesion: 0.14
Nodes (13): 2. Pomiary na żywym modelu, 3. Trafność Modułu 2 — pomiary na żywym Bieliku 4.5B (21.11, noc), 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły, InvestWatch — stan projektu (+5 more)

### Community 69 - "services"
Cohesion: 0.10
Nodes (19): name, networks, investwatch, image, networks, ports, volumes, services (+11 more)

### Community 70 - "postgres"
Cohesion: 0.19
Nodes (15): depends_on, depends_on, condition, depends_on, casedb, postgres, scraper-worker, seaweedfs (+7 more)

### Community 71 - "risk_score"
Cohesion: 0.07
Nodes (15): coverage(), failed_rules(), is_flagged(), max_breach_severity(), risk_level(), risk_score(), _rule(), TestCoverage (+7 more)

### Community 72 - "scraper: Moduł 1 (facebook, youtube, www)"
Cohesion: 0.33
Nodes (6): Collector i flota (praca ciągła), `.env`, Jak to działa, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: Moduł 1 (facebook, youtube, www)

### Community 73 - "resolve"
Cohesion: 0.17
Nodes (27): resolve(), doc(), _firm(), test_active_firm_beats_historical_duplicate_and_inactive_reason(), test_affiliate_variants(), test_affiliate_without_disclosure(), test_agent_publisher_is_authorized(), test_diacritics_and_case_insensitive() (+19 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (10): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+2 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 76 - "analyzer/worker.py"
Cohesion: 0.11
Nodes (12): ApiClient, ApiError, _check_local(), Finding, _vector_of(), _build_det_results(), _detect_and_save_change(), make_store() (+4 more)

### Community 78 - "test_pipeline.py"
Cohesion: 0.13
Nodes (18): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 6: Klasyfikacja zdarzenia, Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), _simhash_int(), hamming_distance() (+10 more)

### Community 79 - "test_pipeline.py"
Cohesion: 0.21
Nodes (9): AdDocument, Evidence, RuleResult, Verdict, _platform(), _result(), _risk_nodes(), _rule6() (+1 more)

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.48
Nodes (4): collect_ads_from_dom(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.22
Nodes (8): CZĘŚĆ A — Autoskaler, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera

### Community 82 - "api"
Cohesion: 0.25
Nodes (8): build, environment, networks, ports, restart, volumes, GOLD_LABELS_PATH, api

### Community 83 - "ingest.py"
Cohesion: 0.33
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.40
Nodes (5): env_file, extra_hosts, networks, restart, analyzer

### Community 86 - "media.py"
Cohesion: 0.24
Nodes (3): download_direct(), download_ytdlp(), probe_duration()

### Community 87 - "test_eval_rules.py"
Cohesion: 0.23
Nodes (6): _row(), test_kolejnosc_regul_numeryczna(), test_metryki_macierz_pomylek(), test_pending_nie_wchodzi_do_macierzy(), test_tabela_zawiera_reguly(), test_walidacja_odrzuca_nieznana_regule()

### Community 88 - "casedb"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "test_rules_det.py"
Cohesion: 0.17
Nodes (20): Rule, evaluate_det(), by_id(), doc_with(), node(), test_base_copy_matches_analyzer(), test_clean_warning_passes_all(), test_facebook_source_delegates_to_platform_rules() (+12 more)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): entrypoint, image, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.13
Nodes (27): TextNode, ViewportProbe, assess_rule_13(), _na(), _result(), _center_y(), _first_match_offset(), _norm_for() (+19 more)

### Community 92 - "_doc"
Cohesion: 0.15
Nodes (7): _json_default(), _load(), main(), _to_csv(), _write(), connect(), migrate()

### Community 93 - "test_api.py"
Cohesion: 0.18
Nodes (22): client(), load(), _postgres_store(), seeded(), store(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless(), test_document_upsert_returns_200_second_time() (+14 more)

### Community 94 - "re"
Cohesion: 0.16
Nodes (7): normalize(), risk_sentences(), split_sentences(), _words(), _normalize(), TestRiskSentences, test_committed_examples_have_no_external_hosts()

### Community 95 - "Registry"
Cohesion: 0.14
Nodes (13): Task 2: Pełny rejestr KNF w dopasowaniu (zagraniczne firmy, agenci, cofnięte zezwolenia), normalize_name(), registry_entries(), Firm, _handle_key(), host_of(), Registry, env() (+5 more)

### Community 96 - "collect.py"
Cohesion: 0.16
Nodes (9): collect_facebook_query(), CollectReport, run_collector(), write_stats(), CollectorConfig, CollectorConfigFiles, main(), seed_synthetic() (+1 more)

### Community 97 - "api/store.py"
Cohesion: 0.12
Nodes (4): FlagsUnavailable, _iso(), PostgresStore, ReportUnavailable

### Community 98 - "dashboard"
Cohesion: 0.12
Nodes (16): condition, build, depends_on, environment, networks, ports, restart, api (+8 more)

### Community 99 - "youtube.py"
Cohesion: 0.07
Nodes (36): dictionary_from_registry(), _domains(), evidence(), find_targets(), _group(), host(), is_language(), language_factory() (+28 more)

### Community 100 - "knf.py"
Cohesion: 0.12
Nodes (13): load_snapshot(), lookup(), name_key(), read_snapshot(), knf_agent_keys(), _knf_country(), sync_registry_from_knf(), _snap() (+5 more)

### Community 101 - "dashboard/src/App.jsx"
Cohesion: 0.13
Nodes (15): connectAlerts(), App(), FILTER_GROUPS, timeRange(), VIEWS, Flyout(), Toasts(), FilterBar() (+7 more)

### Community 102 - "evaluate_batch_2"
Cohesion: 0.31
Nodes (4): evaluate_batch_2(), _client(), _doc(), TestOverrideWBatch2

### Community 103 - "test_casedb_bridge.py"
Cohesion: 0.14
Nodes (10): claim(), process_cases(), set_status(), _ai(), FakeConn, _no_psycopg(), test_blad_analizy_ustawia_error_i_nie_przerywa(), boom() (+2 more)

### Community 104 - "RuleResult"
Cohesion: 0.25
Nodes (10): RuleResult, RuleBase, _DetRule, Rule4FontSize, Rule5Contrast, Rule6Hidden, Rule7OneClick, Rule8Responsive (+2 more)

### Community 105 - "BaseModel"
Cohesion: 0.15
Nodes (10): AGENTS.md - services/casedb, API modulu 1 (store.py), Dla modulu jobow (nastepny krok), Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+2 more)

### Community 106 - "test_casedb.py"
Cohesion: 0.15
Nodes (26): Okresowa aktualizacja, packaged_registry_path(), content_hash(), latest_finding(), load_registry(), record_document(), _doc(), _finding() (+18 more)

### Community 107 - "llm.py"
Cohesion: 0.12
Nodes (9): LlmError, load_prompt(), _all_not_applicable(), _build_result(), evaluate_batch(), _normalize_for_match(), _not_applicable(), quote_is_verifiable() (+1 more)

### Community 115 - "default_config"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, Osoba A — `services/scraper` (zmergowane, PR #2), Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`), Osoba C — `services/api`, `services/web`, default_config(), analyzer — Moduł 2 (analiza AI), Brama zakresu, Konfiguracja (+8 more)

### Community 116 - "change_detect.py"
Cohesion: 0.19
Nodes (9): _basis(), event(), detect_disappeared(), _have_embeddings(), _new_event(), _rule_phrase(), _transitions(), ChangeSimilarity (+1 more)

### Community 117 - "AnalyzerConfig"
Cohesion: 0.25
Nodes (7): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Rejestr KNF (snapshot), Testy, Wymagania

### Community 118 - "eval_module1.py"
Cohesion: 0.18
Nodes (15): _lab(), _res(), test_compare_case_reports_each_field(), test_evaluate_empty_and_no_positive_class(), test_evaluate_metrics(), test_firm_correct_case_insensitive_and_null(), test_labels_file_is_well_formed(), compare_case() (+7 more)

### Community 119 - "scraper-worker"
Cohesion: 0.20
Nodes (10): replicas, deploy, deploy, env_file, image, networks, restart, shm_size (+2 more)

### Community 120 - "environment"
Cohesion: 0.24
Nodes (13): environment, ANALYZER_STORE, API_BASE_URL, DATABASE_URL, FB_FIXTURES_DIR, OLLAMA_BASE_URL, S3_ACCESS_KEY, S3_ENDPOINT (+5 more)

### Community 121 - "typing"
Cohesion: 0.15
Nodes (9): default_worker_id(), make_fetcher(), make_pipeline(), pipeline(), process_one(), run_fleet(), _save_document(), wants_analysis() (+1 more)

### Community 122 - "resolver.py"
Cohesion: 0.12
Nodes (10): document_text(), extract_urls(), find_affiliate_link(), _inactive_reason(), _is_affiliate(), knf_name_matchable(), Match, _on_domain() (+2 more)

### Community 123 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### Community 124 - "lexicons.py"
Cohesion: 0.16
Nodes (7): ConfigFile, Lexicons, _load_yaml(), parse_lexicons(), parse_personas(), Persona, _term_re()

### Community 125 - "web/package.json"
Cohesion: 0.11
Nodes (21): dependencies, react@18.3.1, react-dom@18.3.1, recharts@2.13.3, devDependencies, vite@5.4.11, @vitejs/plugin-react@4.3.4, react (+13 more)

### Community 126 - "README.md"
Cohesion: 0.20
Nodes (3): Skan zależności, Uruchomienie (dev), web (osoba C)

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Korekty niespojnosci danych (nie dopasowanie do wyniku), Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

### Community 131 - "knf_snapshot.py"
Cohesion: 0.14
Nodes (8): CardParser, clean(), fetch(), last_page(), main(), parse_cards(), parse_revoked(), snapshot()

### Community 132 - "logging"
Cohesion: 0.08
Nodes (18): serve(), main(), _start_health_server(), run(), _job_slug(), schedule_facebook(), main(), register() (+10 more)

### Community 133 - "_rule_6"
Cohesion: 0.27
Nodes (11): _dominant_font_px(), _evidence(), _na(), _result(), _risk_hits(), _rule_4(), _rule_5(), _rule_6() (+3 more)

### Community 134 - "cosine"
Cohesion: 0.27
Nodes (3): _cosine(), cosine(), TestCosine

### Community 135 - "scheduler"
Cohesion: 0.25
Nodes (8): command, env_file, image, networks, restart, shm_size, volumes, scheduler

### Community 136 - "dashboard/package.json"
Cohesion: 0.13
Nodes (20): concurrently, ws, dependencies, react@18.3.1, react-dom@18.3.1, recharts@2.13.3, ws@8.23.0, devDependencies (+12 more)

### Community 138 - "test_pipeline.py"
Cohesion: 0.16
Nodes (5): classify_similarity(), embed_document_text(), tokenize(), TestClassifySimilarity, TestNormalizacjaITokeny

### Community 139 - "knf_registry.py"
Cohesion: 0.17
Nodes (10): fetch_register(), fold(), main(), make_id(), merge(), name_key(), parse_entities(), _plausible() (+2 more)

### Community 140 - "InvestWatch"
Cohesion: 0.25
Nodes (8): Bezpieczeństwo łańcucha dostaw, Instalacja Dockera na Windows, InvestWatch, Po `git pull`, Quick Start, Serwisy, Struktura, Wymagania

### Community 141 - "client.js"
Cohesion: 0.17
Nodes (14): allFindings(), api, cache, http(), invalidate(), patch(), items, applyFilters() (+6 more)

### Community 142 - "T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)"
Cohesion: 0.50
Nodes (4): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)

### Community 143 - "YouTubeSource"
Cohesion: 0.12
Nodes (8): TranscriptSegment, _handle(), _published_at(), _QuietLogger, video_id(), YouTubeSource, request(), test_keywords_never_qualify()

### Community 144 - "Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY), Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości

### Community 145 - "Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości, Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)

### Community 146 - "weights"
Cohesion: 0.10
Nodes (19): analyzer_min_priority, instrument_lane_min, lexicon, finfluencer, impersonation_hook, instrument, non_instrument, scam_lure (+11 more)

### Community 148 - "AdDocument"
Cohesion: 0.09
Nodes (18): AdDocument, _casedb(), DbStore, _normalize_doc(), StoreError, test_close(), test_error_wrapped_with_rollback(), test_get_document_and_commit() (+10 more)

### Community 149 - "ollama"
Cohesion: 0.33
Nodes (6): image, networks, profiles, restart, volumes, ollama

### Community 150 - "Rotator"
Cohesion: 0.22
Nodes (9): proxies(), Rotator, _split(), user_agents(), test_from_env(), test_proxies_list_fallback_and_empty(), test_rotator_picks_from_lists(), test_rotator_without_proxy_and_headers() (+1 more)

### Community 151 - "check_compliance.py"
Cohesion: 0.27
Nodes (12): check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file(), _lines() (+4 more)

### Community 153 - "data.js"
Cohesion: 0.18
Nodes (16): ANALYSTS, FIRMS, HUMAN_ONLY, levelFor(), makeFinding(), makeFindings(), makeGold(), pick() (+8 more)

### Community 154 - "views/Calibration.jsx"
Cohesion: 0.26
Nodes (10): Breakdown(), TrendChart(), Panel(), useApi(), confusion(), sweep(), Alerts(), Calibration() (+2 more)

### Community 155 - "from_facebook_node"
Cohesion: 0.18
Nodes (6): _finserv(), from_facebook_node(), Candidate, candidate_from_row(), from_page(), html_text()

### Community 156 - "reresolve.py"
Cohesion: 0.18
Nodes (7): _Cur, _FakeConn, test_run_skips_bad_cases_and_continues(), test_summarize_counts_changes(), main(), run(), summarize()

### Community 157 - "server.js"
Cohesion: 0.18
Nodes (14): ALERT_EVERY_MS, applyFilters(), count(), findings, gold, io, listParam(), PORT (+6 more)

### Community 158 - "components/Calibration.jsx"
Cohesion: 0.30
Nodes (11): axis, Calibration(), SERIES, bestF1(), confusion(), coverage(), effectiveFails(), ratio() (+3 more)

### Community 159 - "test_report_module1.py"
Cohesion: 0.15
Nodes (5): SqliteStore, pg(), test_csv_exports_all_rows_beyond_page(), test_csv_formula_injection_neutralised(), test_sqlite_returns_503()

### Community 160 - "Module1.jsx"
Cohesion: 0.41
Nodes (11): EMPTY, Module1(), getModule1Report(), buildQuery(), clip(), csvUrl(), flagLabel(), FLAGS (+3 more)

### Community 162 - "Global Constraints"
Cohesion: 0.17
Nodes (10): Global Constraints, Moduł 1 — profesjonalne domknięcie, Spec (wiążący), Task 1: Zbiór z etykietami Modułu 1 i ewaluacja (PRZED zmianami resolvera), Task 3: Relacja oficjalny/podmiot trzeci, ujawnienia, ponowne rozwiązanie bazy, Task 4: Raport Modułu 1 — flagi naruszeń, kampanie, zrzut, Task 5: API — raport Modułu 1 (JSON + CSV), Task 6: Zakładka „Moduł 1” w działającym panelu (`services/web`) (+2 more)

### Community 163 - "collector/scoring.py"
Cohesion: 0.24
Nodes (5): normalize(), creative_key(), landing_key(), _publisher_is_official(), test_keys()

### Community 164 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Decyzje, Docelowa topologia (`infra/docker-compose.yml`, projekt `investwatch`), Global Constraints, Pełna infrastruktura w Dockerze — projekt i plan, Spec (wiążący), Task 1: Analyzer zapisuje dokument w API przed findingiem, Task 2: Obraz scrapera, launchery workera i harmonogramu, Task 3: Compose — wszystkie serwisy, `.env.example` (+1 more)

### Community 165 - "context"
Cohesion: 0.27
Nodes (10): build, context, dockerfile, build, networks, profiles, restart, build (+2 more)

### Community 166 - "FakeConn"
Cohesion: 0.20
Nodes (3): fake_casedb(), rec(), FakeConn

### Community 167 - "casedb_batch.py"
Cohesion: 0.31
Nodes (5): main(), make_analyzer(), analyze_case(), run_file(), summarize()

### Community 168 - "jobs"
Cohesion: 0.20
Nodes (10): jobs, enabled, interval_minutes, kind, limit, name, older_than_minutes, queries (+2 more)

### Community 169 - "test_www.py"
Cohesion: 0.33
Nodes (7): make(), test_demo_fixture_pages(), test_discover_same_domain_limited_no_binaries(), test_fetch_text_links_publisher_and_ua(), test_rejects_non_http(), test_robots_disallow_and_robots_error_allows(), test_status_mapping()

### Community 170 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.22
Nodes (9): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6. Kontrakty danych (ZAMROŻONE o 12:30) (+1 more)

### Community 171 - "casedb_bridge.py"
Cohesion: 0.31
Nodes (4): fetch_case(), _jsonb(), _plain(), save_ai_result()

### Community 172 - "preconditions.py"
Cohesion: 0.33
Nodes (4): _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_tax()

### Community 174 - "knn_score"
Cohesion: 0.36
Nodes (3): 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba, knn_score(), TestKnnScore

### Community 175 - "read_registry_csv"
Cohesion: 0.29
Nodes (3): Gdzie co jest, read_registry_csv(), _split()

### Community 178 - "has_disclosure"
Cohesion: 0.32
Nodes (6): has_disclosure(), _negated(), test_disclosure(), test_disclosure_negation(), test_new_disclosure_phrases(), test_non_disclosures()

### Community 179 - "Moduł 1 – przepływ danych i kontrakty"
Cohesion: 0.29
Nodes (6): Jedno źródło prawdy: casedb, Kontrakt zadania analizy (kolejka `q:gpu`), Moduł 1 – przepływ danych i kontrakty, Przepływ, Uruchomienie i harmonogram, Źródła

### Community 180 - "casedb"
Cohesion: 0.29
Nodes (7): build, command, environment, networks, restart, volumes, casedb

### Community 182 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, mock, preview, test, web

### Community 184 - "api (osoba C)"
Cohesion: 0.33
Nodes (4): api (osoba C), Endpointy, Quick start bez Dockera (SQLite), Testy

### Community 187 - "dashboard"
Cohesion: 0.33
Nodes (5): dashboard, Punkty połączenia z bazą, Uruchomienie (dev), Uruchomienie (Docker), Widoki

### Community 188 - "10. Pozyskiwanie danych i bezpieczeństwo demo"
Cohesion: 0.40
Nodes (5): 10. Pozyskiwanie danych i bezpieczeństwo demo, Bezpieczeństwo demo (anty-cel: „demo zależne od wifi"), Cybersec (kryterium oceniane wprost), Kolejka i harmonogram, Pluginowalne źródła

### Community 189 - "8. Logika modułów"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 190 - "9. Scoring, threshold i metryki"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 191 - "Zbiór z etykietami Modułu 1"
Cohesion: 0.40
Nodes (4): Rubryka etykiet, Uczciwość pomiaru, Użycie, Zbiór z etykietami Modułu 1

### Community 192 - "finding_to_ai_result"
Cohesion: 0.40
Nodes (3): analyzer_version(), finding_to_ai_result(), test_wersja_stabilna_i_z_prefiksem()

### Community 193 - "facebook"
Cohesion: 0.40
Nodes (4): facebook, q, tag, type

### Community 195 - "2. Cele, nie-cele, anty-cele"
Cohesion: 0.50
Nodes (4): 2. Cele, nie-cele, anty-cele, Anty-cele (to by oznaczało porażkę, nawet gdyby „działało"), Cele (musi być), Nie-cele (świadomie pomijamy)

### Community 196 - "4. Rozważone podejścia"
Cohesion: 0.50
Nodes (4): 4. Rozważone podejścia, Podejście A — „wszystko do LLM-a", Podejście B — „wszystko na regułach deterministycznych", Podejście C — hybryda warstwowa **[WYBRANE]**

### Community 197 - "T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle)

### Community 199 - "_fake_llm"
Cohesion: 0.50
Nodes (3): _fake_llm(), test_tryb_plikowy_z_fake_llm(), failing()

### Community 201 - "queries_from_registry"
Cohesion: 0.50
Nodes (4): queries_from_registry, knf_ids, limit, phrases

## Knowledge Gaps
- **10 isolated node(s):** `casedb`, `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1290 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `_rule_6`, `cosine`, `test_worker.py`, `httpx`, `test_pipeline.py`, `evaluate_batch_1`, `analyzer/contracts.py`, `YouTubeSource`, `test_collector.py`, `_client`, `Engine`, `LocalCorpusSource`, `OllamaClient`, `test_casedb_adapter.py`, `reresolve.py`, `test_facebook_contract.py`, `json`, `analyze`, `www.py`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `FacebookAdsSource`, `test_stt_pipeline.py`, `scraper/contracts.py`, `os`, `store.py`, `TestGranicyKontraktu`, `stt.py`, `test_partial_guard.py`, `eval_rules.py`, `resolve`, `analyzer/worker.py`, `TestWorkeraZDetResults`, `test_pipeline.py`, `test_pipeline.py`, `test_rules_det.py`, `test_rule_13.py`, `evaluate_batch_2`, `RuleResult`, `llm.py`, `change_detect.py`, `eval_module1.py`, `typing`, `resolver.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 178 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 178 INFERRED edges - model-reasoned connections that need verification._
- **What connects `casedb`, `Analytical / AI Modules`, `Web Dashboard` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11942959001782531 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `test_guards.py` to `test_registry.py`, `_rule_6`, `httpx`, `test_pipeline.py`, `evaluate_batch_1`, `analyzer/contracts.py`, `test_lang_consistency.py`, `_client`, `Engine`, `OllamaClient`, `json`, `analyze`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `casedb_batch.py`, `store.py`, `guards.py`, `test_partial_guard.py`, `eval_rules.py`, `risk_score`, `TestWorkeraZDetResults`, `test_pipeline.py`, `test_rules_det.py`, `test_rule_13.py`, `re`, `evaluate_batch_2`, `RuleResult`, `llm.py`, `change_detect.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 108 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 108 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._