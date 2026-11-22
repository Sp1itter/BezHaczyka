# Graph Report - plan-sprint-final  (2026-11-22)

## Corpus Check
- 356 files · ~1,246,316 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 36 file(s) not represented in the graph (top: (none) 15, .gz 8, .example 3)

## Summary
- 4722 nodes · 12934 edges · 208 communities (171 shown, 37 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 1301 edges (avg confidence: 0.92)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `b48fc443`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_autoscaler.py
- Development Documentation and Skills
- test_registry.py
- os
- test_stt.py
- test_worker.py
- route
- test_evaluate.py
- httpx
- test_summary.py
- datetime
- Finding
- test_scope_gate.py
- _file
- test_config.py
- OllamaClient
- test_collector.py
- test_lang_consistency.py
- test_scaling_runtime.py
- test_batches.py
- test_autoscaler_hardening.py
- rules
- Engine
- LocalCorpusSource
- Module1Report.jsx
- App.jsx
- Integracja serwisów — kto wywołuje kogo
- Transcript
- meta_json.py
- RuntimeError
- test_facebook_contract.py
- LocalBlobStore
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
- NodeCache
- SourceGone
- test_llm_speed.py
- test_live_regressions.py
- q:gpu
- autoscaler.py
- parametrize
- ui.jsx
- feed_fold_evidence
- test_module3.py
- ScopeStatus
- test_pool.py
- scaling.py
- eval_rules.py
- QueueState
- UrlStore
- gen_facebook_examples.py
- infra – stos Docker Compose (projekt `investwatch`)
- api/store.py
- health.py
- casedb/store.py
- test_batches.py
- requalify.py
- test_tools_reanalyze_dedupe.py
- services
- postgres
- risk_score
- build_source
- resolve
- healthcheck
- postgres
- ApiError
- TestWorkeraZDetResults
- test_pipeline.py
- Autoscaler
- ref_node_assert
- labels.js
- api
- ingest.py
- router.py
- environment
- module3.py
- test_eval_rules.py
- casedb
- test_rules_det.py
- seaweedfs
- test_rule_13.py
- _doc
- test_api.py
- youtube.py
- Registry
- lexicons.py
- PostgresStore
- web
- test_youtube.py
- knf.py
- Overview.jsx
- FakeStore
- test_casedb_bridge.py
- AdDocument
- BaseModel
- test_casedb.py
- quote_is_verifiable
- parse_args
- analyzer — Moduł 2 (analiza AI)
- CircuitBreaker
- AnalyzerConfig
- eval_module1.py
- scraper-worker
- environment
- SourceBlocked
- .mentions
- test_module3_wiring.py
- web/package.json
- web (osoba C)
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- knf_snapshot.py
- test_launchers.py
- FindingPage.jsx
- environment
- scheduler
- MediaPreview.jsx
- AlertHub
- check_compliance.py
- knf_registry.py
- local_blob_reader
- ollama
- transcribe
- YouTubeSource
- Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)
- Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)
- weights
- AdDocument
- batching.py
- Rotator
- valkey
- collections_abc
- TestAnalyze
- Connection
- synthetic.py
- reresolve.py
- pipeline.py
- services
- test_alerts_db.py
- _QuietLogger
- test_discover_canonical_unique_and_limiter
- test_crawler.py
- test_invalid_url_and_gone
- RateLimiter
- export_gold_documents.py
- FakeConn
- tiktok.py
- jobs
- test_packaging.py
- docker-socket-proxy
- FakeRedis
- browser_pool.py
- test_gold_set.py
- read_registry_csv
- ollama-pull
- TestGranicyKontraktu
- test_idempotency_gate.py
- jobs.py
- Moduł 1 – przepływ danych i kontrakty
- test_requalify.py
- Shell.jsx
- test_contracts_copy.py
- scraper-worker-render
- backfill_summaries.py
- state.py
- test_spojnosc.py
- scope_gate.py
- TestCfdNaKryptoZostajeWZakresie
- casedb_batch.py
- resources
- Zbiór z etykietami Modułu 1
- nginx
- facebook
- _Extractor
- Zbior zloty (gold set)
- TestPozaZakresemBezOceny
- test_www_sends_rotated_ua_and_proxy_per_request
- render_queue_for
- FakeConn
- TestKorpusuNaTejMaszynie
- discover_queue_for
- SECURITY-AUDIT-scraper.md
- audit.sh
- casedb
- module2-live-regressions/README.md
- test_cfd_na_krypto_jest_w_zakresie_w_przykladzie

## God Nodes (most connected - your core abstractions)
1. `Verdict` - 250 edges
2. `AdDocument` - 239 edges
3. `RuleResult` - 153 edges
4. `analyze()` - 95 edges
5. `Engine` - 72 edges
6. `OllamaClient` - 72 edges
7. `create_app()` - 72 edges
8. `EvidenceKind` - 69 edges
9. `FacebookAdsSource` - 66 edges
10. `AnalyzerConfig` - 65 edges

## Surprising Connections (you probably didn't know these)
- `Jak dodac pozycje` --references--> `risk_score()`  [INFERRED]
  fixtures/gold/README.md → services/analyzer/analyzer/scoring.py
- `Co A wrzuca do kolejki` --references--> `analyze_document()`  [INFERRED]
  docs/INTEGRACJA.md → services/analyzer/analyzer/worker.py
- `Kontrakt zadania analizy (kolejka `q:gpu`)` --references--> `analyze_document()`  [INFERRED]
  docs/MODUL1-ARCHITEKTURA.md → services/analyzer/analyzer/worker.py
- `Okresowa aktualizacja` --references--> `detect_change()`  [INFERRED]
  docs/MODUL1-ARCHITEKTURA.md → services/analyzer/analyzer/change_detect.py
- `Endpointy` --references--> `risk_level()`  [INFERRED]
  services/api/README.md → services/analyzer/analyzer/scoring.py

## Import Cycles
- None detected.

## Communities (208 total, 37 thin omitted)

### Community 0 - "test_autoscaler.py"
Cohesion: 0.06
Nodes (28): Clock, FakeBackend, FakeExecutor, test_apply_nie_trzyma_locka(), test_payload_bez_valkeya_jest_zdegradowany_a_nie_500(), test_tick_przekazuje_id_zajetych_workerow_do_executora(), apply(), test_update_odrzuca_wartosci_poza_granicami() (+20 more)

### Community 2 - "test_registry.py"
Cohesion: 0.08
Nodes (25): rule_3_runner(), build_config(), coverage_report(), default_config(), expected_rule_ids(), _merge_meta(), module2_runners(), _rule_sort_key() (+17 more)

### Community 3 - "os"
Cohesion: 0.09
Nodes (20): connect(), apply_plan(), _aware(), has_work(), load(), main(), plan(), work_time() (+12 more)

### Community 4 - "test_stt.py"
Cohesion: 0.13
Nodes (27): Transcript, TranscriptSegment, _first_match_start(), normalize_text(), rate_anomaly(), risk_timing(), RiskTiming, speech_rate() (+19 more)

### Community 5 - "test_worker.py"
Cohesion: 0.07
Nodes (37): analyze_document(), handle_job(), Integracja z bazą (casedb, Moduł 1), _api(), handler(), _api_no_get(), FakeStore, test_analysis_exception_sets_error_status_and_reraises() (+29 more)

### Community 6 - "route"
Cohesion: 0.15
Nodes (7): route(), RoutingDecision, _inp(), TestR1WlasnyMaterialFirmy, TestR2PodmiotTrzeci, TestR3DoradztwoBezZezwolenia, TestR4Triage

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "httpx"
Cohesion: 0.05
Nodes (26): _download(), _max_bytes(), resolve_media(), _s3_to_http(), evaluate_batch_1(), _client(), _doc(), _generate_handler() (+18 more)

### Community 9 - "test_summary.py"
Cohesion: 0.12
Nodes (32): build_summary(), FakeClient, _finding(), pg_conn(), _reason(), _rule(), test_auth_polarity_authorized(), test_auth_polarity_unauthorized() (+24 more)

### Community 10 - "datetime"
Cohesion: 0.08
Nodes (18): _curl_session(), ddgs_search(), host_of(), is_candidate(), keep_url(), LiveWebSource, _on(), _search_limiter() (+10 more)

### Community 11 - "Finding"
Cohesion: 0.12
Nodes (23): Finding, LlmError, load_prompt(), _advertiser(), _auth_state(), _authorization(), check_llm_reply(), _correction() (+15 more)

### Community 12 - "test_scope_gate.py"
Cohesion: 0.11
Nodes (4): TestBrakSygnaluFinansowego, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.08
Nodes (30): _deep_merge(), get_threshold(), load_thresholds(), _dominant_font_px(), _evidence(), _na(), _result(), _risk_hits() (+22 more)

### Community 15 - "OllamaClient"
Cohesion: 0.09
Nodes (15): _keep_alive(), _num_ctx(), OllamaClient, _shared_client(), test_wspolny_klient_http_jest_reuzywany(), TestPowtarzalnosciModelu, load_case(), main() (+7 more)

### Community 16 - "test_collector.py"
Cohesion: 0.08
Nodes (36): collect_facebook_query(), Lexicons, affiliate_params(), Candidate, creative_key(), landing_key(), _publisher_is_official(), score() (+28 more)

### Community 17 - "test_lang_consistency.py"
Cohesion: 0.08
Nodes (15): evaluate_batch_2(), apply_rule_10_override(), assess_rule_10(), _result(), detect_language(), risk_sentences(), split_sentences(), _words() (+7 more)

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.11
Nodes (9): _connection(), read_queue_states(), _rq_backlog_reader(), _read(), _rq_worker_counter(), _count(), test_read_queue_states_uzywa_czytnika_idle(), TestOdczytuStanuKolejek (+1 more)

### Community 19 - "test_batches.py"
Cohesion: 0.10
Nodes (13): evaluate_batch_3(), evaluate_batch_4(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_tax(), _client_returning_fail(), _client_that_must_not_be_called() (+5 more)

### Community 20 - "test_autoscaler_hardening.py"
Cohesion: 0.11
Nodes (24): detect_project(), names(), _setup(), test_bez_busy_ids_zachowanie_jak_dawniej(), test_scale_down_zdejmuje_bezczynny_zamiast_zajetego_o_wyzszym_numerze(), test_stop_uzywa_180_s(), test_update_ignoruje_kolejki_tylko_do_odczytu(), test_update_przyjmuje_wartosci_graniczne() (+16 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "Engine"
Cohesion: 0.12
Nodes (22): Engine, Evidence, EvidenceKind, missing_det_placeholders(), RuleBase, _no_supervision_reference(), _doc(), _res() (+14 more)

### Community 23 - "LocalCorpusSource"
Cohesion: 0.08
Nodes (9): run(), AdDocument, Source, LocalCorpusSource, results(), test_document_id_independent_of_url(), test_documents_follow_contract(), test_page_verdicts_match_labels() (+1 more)

### Community 24 - "Module1Report.jsx"
Cohesion: 0.19
Nodes (15): api, http(), patch(), buildQuery(), clip(), csvUrl(), flagLabel(), FLAGS (+7 more)

### Community 25 - "App.jsx"
Cohesion: 0.14
Nodes (23): connectAlerts(), App(), ErrorBoundary, EmptyState(), FilterBar(), PageHeader(), SortableTable(), confusion() (+15 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.15
Nodes (11): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, api (osoba C) (+3 more)

### Community 28 - "Transcript"
Cohesion: 0.11
Nodes (25): analyzer_version(), _bodies(), case_to_document(), finding_to_ai_result(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case() (+17 more)

### Community 29 - "meta_json.py"
Cohesion: 0.07
Nodes (40): doc_from_node(), _finserv(), from_facebook_node(), ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), _cards() (+32 more)

### Community 30 - "RuntimeError"
Cohesion: 0.09
Nodes (27): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+19 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.07
Nodes (20): fetch(), canonical_ad_url(), doc(), source(), test_auto_mode_falls_back_to_fixture_when_breaker_open(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_document_matches_frozen_contract() (+12 more)

### Community 32 - "LocalBlobStore"
Cohesion: 0.11
Nodes (10): download_direct(), download_ytdlp(), probe_duration(), main(), FacebookConfig, LocalBlobStore, test_facebook_uses_shared_rotator_per_context(), test_no_proxy_by_default() (+2 more)

### Community 33 - "analyze"
Cohesion: 0.10
Nodes (15): analyze(), AnalyzerConfig, _ensure_transcript(), EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults (+7 more)

### Community 34 - "www.py"
Cohesion: 0.09
Nodes (17): SourceError, _is_page_link(), _origin(), _Page, WebPageSource, test_contract_copy_matches_analyzer(), test_www_block_statuses_raise_source_blocked(), test_worker_requires_queue() (+9 more)

### Community 35 - "re"
Cohesion: 0.10
Nodes (5): AdDocument, document_row(), _iso(), _row_to_document(), SqlStore

### Community 36 - "test_change_detect.py"
Cohesion: 0.09
Nodes (45): _basis(), _cosine(), detect_change(), event(), detect_disappeared(), diff_rule_results(), _have_embeddings(), _new_event() (+37 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.22
Nodes (23): RenderProbe, ViewportProbe, det_fallback_results(), _by(), _doc(), _doc2(), _node(), _run() (+15 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.07
Nodes (22): TextNode, assess_rule_3(), _result(), _center_y(), _first_match_offset(), _matches(), measure_geometry(), measure_proximity() (+14 more)

### Community 39 - "scheduler.py"
Cohesion: 0.09
Nodes (19): expand(), JobSpec, load_schedule(), main(), register(), _registry_queries(), run_once(), Task (+11 more)

### Community 40 - "test_guards.py"
Cohesion: 0.16
Nodes (32): Verdict, mentions_historical_performance(), _res(), _run(), test_12a_jeden_rok_pass_zamieniony_na_fail(), test_12a_nie_zamienia_fail_na_pass(), test_12a_pelny_okres_zostaje_pass(), test_12b_pass_bez_walut_i_oplat_to_fail() (+24 more)

### Community 41 - "FacebookAdsSource"
Cohesion: 0.09
Nodes (7): MediaItem, NavigationGuard, _abort_heavy(), FacebookAdsSource, FakePage, test_facebook_detects_block_pages(), test_facebook_normal_page_is_not_block()

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.12
Nodes (6): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), test_real_speech_to_rule_3(), TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.16
Nodes (15): neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_nodes_are_not_visible_even_with_layout_box(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.07
Nodes (42): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+34 more)

### Community 46 - "SourceGone"
Cohesion: 0.07
Nodes (28): Publisher, fetch_job(), SourceGone, _ydl_extract(), doc(), env(), FakeConn, FakeSource (+20 more)

### Community 47 - "test_llm_speed.py"
Cohesion: 0.12
Nodes (22): fit_material(), _num_predict(), _doc(), _ids(), _mk_runner(), runner(), _mock(), _res() (+14 more)

### Community 48 - "test_live_regressions.py"
Cohesion: 0.09
Nodes (30): has_investment_recommendation(), normalize(), apply_guards(), _guard_rule_12a(), _guard_rule_12b(), _guard_rule_14(), _guard_rule_16(), _guard_rule_17() (+22 more)

### Community 49 - "q:gpu"
Cohesion: 0.09
Nodes (22): cpus, max, memory_mb, min, scale_down_idle_s, scale_up_backlog, max, min (+14 more)

### Community 50 - "autoscaler.py"
Cohesion: 0.11
Nodes (9): build_executor(), _iso(), main(), make_handler(), do_GET(), do_PUT(), _send(), serve() (+1 more)

### Community 51 - "parametrize"
Cohesion: 0.05
Nodes (52): _alert_loop(), alert_payload(), _autoscaler_call(), _contract_mock(), coverage(), create_app(), _autoscaler(), _backfill_frames() (+44 more)

### Community 52 - "ui.jsx"
Cohesion: 0.15
Nodes (22): PAGE_SIZE, TrendChart(), FilterDrawer(), FilterForm(), StatusPill(), useCollapse(), isOpen(), items (+14 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.14
Nodes (13): feed_fold_evidence(), FeedFoldEvidence, platform_rule_override(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "test_module3.py"
Cohesion: 0.30
Nodes (15): assess_shadow_advisory(), run_module3(), _boom(), _client(), wrapped(), _doc(), _ok(), handler() (+7 more)

### Community 55 - "ScopeStatus"
Cohesion: 0.16
Nodes (15): ScopeStatus, classify_scope(), test_gra_bez_sygnalu_finansowego_poza_zakresem(), test_inwestowanie_i_brokerzy_nie_wypadaja_z_zakresu(), test_jedna_znizka_nie_wyklucza(), test_lokata_i_kod_promocyjny_poza_zakresem(), test_procent_z_okresem_to_obietnica(), test_procent_ze_znakiem_z_kontekstem_finansowym_to_zysk() (+7 more)

### Community 56 - "test_pool.py"
Cohesion: 0.13
Nodes (14): DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne(), test_apply_startuje_brakujace_workery() (+6 more)

### Community 57 - "scaling.py"
Cohesion: 0.10
Nodes (24): apply_overrides(), env_ollama_parallel(), env_overrides(), _int(), load_scaling_config(), make_valkey_state_provider(), _provider(), _num() (+16 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.13
Nodes (15): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+7 more)

### Community 59 - "QueueState"
Cohesion: 0.13
Nodes (22): decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_pojemnosci_ollamy(), test_gpu_rosnie_do_max_przy_duzym_backlogu(), test_gpu_schodzi_o_jeden_po_progu_bezczynnosci_60s() (+14 more)

### Community 60 - "UrlStore"
Cohesion: 0.13
Nodes (9): reprioritize(), Scored, _now(), open_store(), PostgresUrlStore, SqliteUrlStore, UpsertOutcome, UrlStore (+1 more)

### Community 61 - "gen_facebook_examples.py"
Cohesion: 0.12
Nodes (13): collect_ads_from_dom(), ads_from_html(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive(), test_committed_examples_have_no_external_hosts(), test_host_replaced_path_and_params_kept(), test_uppercase_scheme_and_s3_untouched() (+5 more)

### Community 62 - "infra – stos Docker Compose (projekt `investwatch`)"
Cohesion: 0.20
Nodes (9): Autoskaler analyzerów, Budowanie na kontrakcie bez uruchamiania analizy, infra – stos Docker Compose (projekt `investwatch`), Metryki do panelu, Ollama, Serwisy, Szybki start: caly stos jedną komendą, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać) (+1 more)

### Community 63 - "api/store.py"
Cohesion: 0.16
Nodes (8): Finding, main(), seed(), finding_row(), InvalidId, open_store(), UpsertResult, test_seed_loads_contract_examples()

### Community 64 - "health.py"
Cohesion: 0.18
Nodes (5): _Handler, health_payload(), _llm(), test_health_ollama_down_is_degraded_not_fatal(), test_health_ollama_up()

### Community 65 - "casedb/store.py"
Cohesion: 0.12
Nodes (19): from_ad_document(), from_youtube(), youtube_video_id(), add_asset(), Asset, Case, case_id_for(), Content (+11 more)

### Community 66 - "test_batches.py"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 67 - "requalify.py"
Cohesion: 0.18
Nodes (10): _rows(), dictionary_from_registry(), is_language(), language_factory(), mentions(), test_language_filter(), candidates(), main() (+2 more)

### Community 68 - "test_tools_reanalyze_dedupe.py"
Cohesion: 0.14
Nodes (13): _Conn, _Cur, _load(), _row(), test_dedupe_bez_pracy_zostaje_najnowszy_bez_kopiowania(), test_dedupe_praca_na_zachowanym_wierszu_nie_jest_kopiowana(), test_dedupe_praca_z_najpozniej_zmienionego_wiersza(), test_dedupe_zdarzenia_liczone_jako_praca() (+5 more)

### Community 69 - "services"
Cohesion: 0.11
Nodes (18): build, command, environment, networks, restart, volumes, name, networks (+10 more)

### Community 70 - "postgres"
Cohesion: 0.18
Nodes (18): depends_on, depends_on, condition, depends_on, casedb, ollama-pull, postgres, scraper-worker (+10 more)

### Community 71 - "risk_score"
Cohesion: 0.07
Nodes (19): RiskLevel, coverage(), _escalation_floor(), failed_rules(), is_flagged(), max_breach_severity(), risk_level(), risk_score() (+11 more)

### Community 72 - "build_source"
Cohesion: 0.05
Nodes (29): build_facebook_source(), build_source(), _enqueue_analysis(), _fetch(), _youtube_content(), Collector i flota (praca ciągła), Jak to działa, Korpus demo (nagrać wieczorem przed demo) (+21 more)

### Community 73 - "resolve"
Cohesion: 0.13
Nodes (33): document_text(), has_disclosure(), resolve(), with_official_flag(), doc(), _firm(), test_active_firm_beats_historical_duplicate_and_inactive_reason(), test_affiliate_variants() (+25 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (12): healthcheck, healthcheck, interval, retries, start_period, test, timeout, healthcheck (+4 more)

### Community 75 - "postgres"
Cohesion: 0.18
Nodes (11): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, cpus, environment, image, mem_limit, networks (+3 more)

### Community 76 - "ApiError"
Cohesion: 0.18
Nodes (6): ApiClient, ApiError, _check_local(), make_store(), test_external_base_url_rejected(), test_store_selection_from_env()

### Community 78 - "test_pipeline.py"
Cohesion: 0.06
Nodes (17): classify_similarity(), cosine(), embed_document_text(), hamming_distance(), is_near_duplicate_simhash(), knn_score(), simhash(), simhash_hex() (+9 more)

### Community 79 - "Autoscaler"
Cohesion: 0.16
Nodes (4): Autoscaler, Backend, handler(), handler()

### Community 80 - "ref_node_assert"
Cohesion: 0.12
Nodes (13): fmtTs(), fmtValue(), fmtViewport(), formatEvidence(), isHttp(), safeHttpUrl(), CATEGORY, categoryOf() (+5 more)

### Community 81 - "labels.js"
Cohesion: 0.11
Nodes (19): LEVELS, ANALYSTS, ASSIGNED_BY, DECISION, HUMAN_ONLY, MODULE, RISK, RISK_COLOR (+11 more)

### Community 82 - "api"
Cohesion: 0.17
Nodes (15): build, build, cpus, mem_limit, networks, ports, restart, volumes (+7 more)

### Community 83 - "ingest.py"
Cohesion: 0.46
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "router.py"
Cohesion: 0.14
Nodes (11): _blank(), _has_any(), has_profit_claims(), looks_like_advisory_business(), mask_non_claims(), _matches_any(), _percent_is_return(), test_myslnik_slowny_nie_jest_znakiem_procentu() (+3 more)

### Community 85 - "environment"
Cohesion: 0.25
Nodes (8): cpus, env_file, extra_hosts, mem_limit, networks, restart, stop_grace_period, analyzer

### Community 86 - "module3.py"
Cohesion: 0.13
Nodes (13): advisory_signals(), has_instrument_mention(), mentions_financial_instrument(), _na(), _result(), find_recommendations(), _is_negated(), _normalize() (+5 more)

### Community 87 - "test_eval_rules.py"
Cohesion: 0.23
Nodes (6): _row(), test_kolejnosc_regul_numeryczna(), test_metryki_macierz_pomylek(), test_pending_nie_wchodzi_do_macierzy(), test_tabela_zawiera_reguly(), test_walidacja_odrzuca_nieznana_regule()

### Community 88 - "casedb"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "test_rules_det.py"
Cohesion: 0.25
Nodes (18): evaluate_det(), by_id(), doc_with(), node(), test_clean_warning_passes_all(), test_facebook_source_delegates_to_platform_rules(), test_no_probe_and_no_warning_are_not_applicable(), test_r4_small_font_fails_with_measurement() (+10 more)

### Community 90 - "seaweedfs"
Cohesion: 0.25
Nodes (8): cpus, entrypoint, image, mem_limit, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.23
Nodes (19): assess_rule_13(), _na(), _result(), rule_13_runner(), _doc(), _node(), test_brak_wynikow_historycznych_to_not_applicable(), test_cytat_to_doslowny_tekst_wezla() (+11 more)

### Community 92 - "_doc"
Cohesion: 0.13
Nodes (9): _json_default(), _load(), main(), _to_csv(), _write(), connect(), migrate(), claim() (+1 more)

### Community 93 - "test_api.py"
Cohesion: 0.08
Nodes (45): youtube_video_id(), client(), load(), seeded(), store(), test_assign_and_release(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless() (+37 more)

### Community 94 - "youtube.py"
Cohesion: 0.09
Nodes (23): caption_url(), captions_from_json3(), _domains(), evidence(), find_targets(), _group(), host(), normalize() (+15 more)

### Community 95 - "Registry"
Cohesion: 0.13
Nodes (14): Firm, _handle_key(), _inactive_reason(), knf_name_matchable(), Registry, test_build_source_youtube_uses_registry_rows(), test_run_skips_bad_cases_and_continues(), reg() (+6 more)

### Community 96 - "lexicons.py"
Cohesion: 0.16
Nodes (9): CollectorConfigFiles, ConfigFile, _load_yaml(), parse_lexicons(), parse_personas(), Persona, cfg(), files() (+1 more)

### Community 97 - "PostgresStore"
Cohesion: 0.09
Nodes (6): FlagsUnavailable, PostgresStore, ReportUnavailable, pg(), _postgres_store(), pg()

### Community 98 - "web"
Cohesion: 0.20
Nodes (10): condition, api, web, build, cpus, depends_on, mem_limit, networks (+2 more)

### Community 99 - "test_youtube.py"
Cohesion: 0.20
Nodes (17): make_clips(), info(), make(), MemStore, patched(), segs(), test_clip_short_with_target_and_signal(), test_distant_target_does_not_create_clip() (+9 more)

### Community 100 - "knf.py"
Cohesion: 0.11
Nodes (14): load_snapshot(), lookup(), name_key(), read_snapshot(), knf_agent_keys(), _knf_country(), registry_entries(), sync_registry_from_knf() (+6 more)

### Community 101 - "Overview.jsx"
Cohesion: 0.49
Nodes (7): react, RulesPanel(), useApi(), SOURCE, Overview(), QueueCard(), SourcesPanel()

### Community 102 - "FakeStore"
Cohesion: 0.14
Nodes (7): FakeStore, test_worker_posts_finding_before_summary(), test_worker_saves_summary(), test_worker_summary_disabled(), test_worker_summary_error_does_not_break_save(), test_worker_summary_write_failure_keeps_finding(), boom()

### Community 103 - "test_casedb_bridge.py"
Cohesion: 0.07
Nodes (19): claim(), fetch_case(), _jsonb(), _plain(), process_cases(), save_ai_result(), set_status(), _ai() (+11 more)

### Community 104 - "AdDocument"
Cohesion: 0.09
Nodes (20): AdDocument, RuleResult, Rule, test_analyzable_text_zawiera_transkrypcje(), test_rule_result_ma_dowod_dla_kazdego_werdyktu(), test_tempo_segmentu_transkryptu_jest_liczone(), TestInterfejsRule, Rule (+12 more)

### Community 105 - "BaseModel"
Cohesion: 0.20
Nodes (8): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column(), test_add_column_rejects_injection()

### Community 106 - "test_casedb.py"
Cohesion: 0.17
Nodes (23): Okresowa aktualizacja, content_hash(), load_registry(), record_document(), report_module1(), save_finding(), _doc(), _finding() (+15 more)

### Community 107 - "quote_is_verifiable"
Cohesion: 0.27
Nodes (3): _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable

### Community 114 - "parse_args"
Cohesion: 0.09
Nodes (11): serve(), _build_det_results(), _detect_and_save_change(), main(), _make_summary(), parse_args(), _resolve_document(), _save_finding() (+3 more)

### Community 115 - "analyzer — Moduł 2 (analiza AI)"
Cohesion: 0.20
Nodes (9): analyzer — Moduł 2 (analiza AI), Brama zakresu, Konfiguracja, Mapa plików, Quick Start, Uruchomienie, Weryfikacja cytatu, Wymagania sprzętowe (+1 more)

### Community 116 - "CircuitBreaker"
Cohesion: 0.20
Nodes (12): CircuitBreaker, _fb(), test_breaker_redis_opens_after_threshold_and_closes_after_cooldown(), test_breaker_redis_window_and_success_reset(), test_breaker_shared_between_workers_via_redis(), test_facebook_block_opens_breaker_and_stops_live_requests(), blocked(), test_facebook_generic_error_does_not_open_breaker() (+4 more)

### Community 117 - "AnalyzerConfig"
Cohesion: 0.25
Nodes (7): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Rejestr KNF (snapshot), Testy, Wymagania

### Community 118 - "eval_module1.py"
Cohesion: 0.18
Nodes (15): _lab(), _res(), test_compare_case_reports_each_field(), test_evaluate_empty_and_no_positive_class(), test_evaluate_metrics(), test_firm_correct_case_insensitive_and_null(), test_labels_file_is_well_formed(), compare_case() (+7 more)

### Community 119 - "scraper-worker"
Cohesion: 0.15
Nodes (13): replicas, deploy, cpus, deploy, env_file, image, mem_limit, networks (+5 more)

### Community 120 - "environment"
Cohesion: 0.16
Nodes (22): environment, environment, ALERT_LOOKBACK_S, ALERT_POLL_S, ANALYZER_STORE, API_BASE_URL, AUTOSCALER_URL, DATABASE_URL (+14 more)

### Community 121 - "SourceBlocked"
Cohesion: 0.11
Nodes (15): CollectReport, run_collector(), write_stats(), CollectorConfig, default_worker_id(), make_fetcher(), make_pipeline(), pipeline() (+7 more)

### Community 122 - ".mentions"
Cohesion: 0.20
Nodes (6): extract_urls(), find_affiliate_link(), host_of(), _is_affiliate(), Match, _on_domain()

### Community 123 - "test_module3_wiring.py"
Cohesion: 0.21
Nodes (14): Relation, _build_resolution(), _doc(), _fake_client(), _runner(), test_bramka_doradcze_docieraja_do_modelu(), test_bramka_niedoradcze(), test_disclaimer_nie_wola_modelu() (+6 more)

### Community 125 - "web/package.json"
Cohesion: 0.11
Nodes (20): react-dom, recharts, vite, @vitejs/plugin-react, dependencies, react@18.3.1, react-dom@18.3.1, recharts@2.13.3 (+12 more)

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Korekty niespojnosci danych (nie dopasowanie do wyniku), Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

### Community 131 - "knf_snapshot.py"
Cohesion: 0.07
Nodes (16): test_finding_moze_nalezec_do_wielu_modulow(), test_przyklad_waliduje_sie_przeciw_modelowi(), main(), main(), test_example_validates(), bench(), latest_urls(), main() (+8 more)

### Community 132 - "test_launchers.py"
Cohesion: 0.13
Nodes (11): _job_slug(), schedule_facebook(), main(), register(), FakeScheduler, _Job, test_job_slug_fallback_hash_for_empty(), test_job_slug_strips_polish_and_punctuation() (+3 more)

### Community 133 - "FindingPage.jsx"
Cohesion: 0.23
Nodes (17): CopyButton(), ErrorState(), groupOf(), GROUPS, RELATION, VERDICT, fmtDate(), pct() (+9 more)

### Community 134 - "environment"
Cohesion: 0.11
Nodes (19): command, cpus, depends_on, environment, mem_limit, networks, restart, docker-socket-proxy (+11 more)

### Community 135 - "scheduler"
Cohesion: 0.20
Nodes (10): command, cpus, env_file, image, mem_limit, networks, restart, shm_size (+2 more)

### Community 136 - "MediaPreview.jsx"
Cohesion: 0.27
Nodes (15): base(), candidatesFor(), MediaPreview(), TextCard(), VIDEO_SOURCES, VideoFrame(), RiskBadge(), VerificationCard() (+7 more)

### Community 138 - "check_compliance.py"
Cohesion: 0.27
Nodes (12): check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file(), _lines() (+4 more)

### Community 139 - "knf_registry.py"
Cohesion: 0.09
Nodes (16): normalize(), normalize(), _term_re(), fold_words(), _negated(), surface_form(), fetch_register(), fold() (+8 more)

### Community 140 - "local_blob_reader"
Cohesion: 0.14
Nodes (9): local_blob_reader(), read(), local_blob_writer(), write(), s3_reader_from_env(), s3_writer_from_env(), test_backfill_frames(), test_backfill_frames_rejects_host_off_allowlist() (+1 more)

### Community 141 - "ollama"
Cohesion: 0.11
Nodes (18): resources, OLLAMA_CONTEXT_LENGTH, OLLAMA_FLASH_ATTENTION, OLLAMA_KEEP_ALIVE, OLLAMA_KV_CACHE_TYPE, OLLAMA_MAX_LOADED_MODELS, OLLAMA_NUM_PARALLEL, cpus (+10 more)

### Community 142 - "transcribe"
Cohesion: 0.16
Nodes (13): _default_transcriber(), run(), SttError, transcribe(), test_stt_error_is_runtime_error(), test_transcribe_empty_result(), test_transcribe_passes_through_stt_error(), boom() (+5 more)

### Community 143 - "YouTubeSource"
Cohesion: 0.20
Nodes (5): _handle(), _published_at(), video_id(), YouTubeSource, test_youtube_options_use_rotator()

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
Nodes (19): _casedb(), DbStore, StoreError, _vector_of(), test_close(), test_error_wrapped_with_rollback(), test_get_document_and_commit(), test_get_document_invalid() (+11 more)

### Community 149 - "batching.py"
Cohesion: 0.23
Nodes (9): LlmTruncatedError, _all_not_applicable(), _build_result(), evaluate_batch(), _mark_truncated(), _not_applicable(), platform_ad_meta(), test_ucieta_odpowiedz_ponawiana_z_podwojonym_limitem() (+1 more)

### Community 150 - "Rotator"
Cohesion: 0.20
Nodes (11): proxies(), Rotator, _split(), user_agents(), test_rotator_copies_input_lists(), test_rotator_from_env_rotates_ua_and_proxy_per_call(), test_from_env(), test_proxies_list_fallback_and_empty() (+3 more)

### Community 151 - "valkey"
Cohesion: 0.29
Nodes (7): valkey, cpus, image, mem_limit, networks, ports, volumes

### Community 152 - "collections_abc"
Cohesion: 0.12
Nodes (4): ComposeExecutor, _default_spawn(), _is_busy(), _number()

### Community 153 - "TestAnalyze"
Cohesion: 0.21
Nodes (4): _doc(), _rule(), _runner(), TestAnalyze

### Community 154 - "Connection"
Cohesion: 0.12
Nodes (10): API modulu 1 (store.py), cases_for_recheck(), _fold(), get_document(), latest_finding(), mark_gone(), normalize_name(), save_vectors() (+2 more)

### Community 155 - "synthetic.py"
Cohesion: 0.24
Nodes (3): candidate_from_row(), from_page(), html_text()

### Community 156 - "reresolve.py"
Cohesion: 0.17
Nodes (6): _Cur, _FakeConn, test_summarize_counts_changes(), main(), run(), summarize()

### Community 157 - "pipeline.py"
Cohesion: 0.17
Nodes (6): _crashed_rule_result(), guard_partial_result(), _module3_runner(), _run_module2(), _run_one(), RoutingInput

### Community 158 - "services"
Cohesion: 0.14
Nodes (13): depends_on, ollama, ollama-pull, condition, profiles, condition, profiles, required (+5 more)

### Community 159 - "test_alerts_db.py"
Cohesion: 0.12
Nodes (16): poll_alerts_once(), SqliteStore, _finding(), _poll(), test_bad_env_falls_back(), test_direct_db_high_alerts_once(), test_low_does_not_alert(), test_low_updated_to_high_alerts_once() (+8 more)

### Community 162 - "test_crawler.py"
Cohesion: 0.20
Nodes (6): discover_job(), FakeQueue, ListSource, test_discover_job_enqueues_each_url_once(), test_discover_job_facebook_dedups_by_ad_id(), test_discover_job_seen_is_per_source()

### Community 164 - "RateLimiter"
Cohesion: 0.23
Nodes (7): RateLimiter, FakeClock, test_limiter_memory_enforces_min_interval(), test_limiter_no_wait_when_interval_already_passed(), test_limiter_redis_shared_between_workers(), test_limiter_zero_interval_never_sleeps(), test_rate_limiter_spaces_requests()

### Community 165 - "export_gold_documents.py"
Cohesion: 0.22
Nodes (5): test_committed_gold_documents_are_complete(), test_exported_files_are_sanitized(), _dump(), export(), main()

### Community 166 - "FakeConn"
Cohesion: 0.20
Nodes (3): fake_casedb(), rec(), FakeConn

### Community 167 - "tiktok.py"
Cohesion: 0.09
Nodes (22): MediaItem, Transcript, TranscriptSegment, _download_video(), LiveTikTokSource, segments_from_vtt(), TikTokSource, video_id() (+14 more)

### Community 168 - "jobs"
Cohesion: 0.13
Nodes (14): jobs, enabled, interval_minutes, kind, limit, name, older_than_minutes, queries (+6 more)

### Community 169 - "test_packaging.py"
Cohesion: 0.22
Nodes (7): _copied(), _local_imports(), _reachable(), test_dockerfile_copies_every_module_reachable_from_worker(), test_queues_from_env(), test_queues_from_env_rejects_unknown_queue(), queues_from_env()

### Community 170 - "docker-socket-proxy"
Cohesion: 0.15
Nodes (13): cpus, environment, image, mem_limit, networks, restart, volumes, CONTAINERS (+5 more)

### Community 172 - "browser_pool.py"
Cohesion: 0.27
Nodes (6): _close(), enabled(), _get(), reset(), shared_browser(), browser_cm()

### Community 174 - "read_registry_csv"
Cohesion: 0.23
Nodes (7): Gdzie co jest, packaged_registry_path(), read_registry_csv(), _split(), test_cli_ingest_and_export(), test_load_registry(), test_read_registry_csv_packaged_and_custom()

### Community 175 - "ollama-pull"
Cohesion: 0.18
Nodes (11): ollama, OLLAMA_HOST, OLLAMA_MODELS_PULL, condition, depends_on, entrypoint, environment, image (+3 more)

### Community 177 - "test_idempotency_gate.py"
Cohesion: 0.40
Nodes (8): GateDecision, should_analyze(), _doc(), test_brak_simhasha_nie_wywraca_bramy(), test_identyczny_material_nie_idzie_na_gpu(), test_pierwsze_zetkniecie_zawsze_analizujemy(), test_reason_zawsze_niepusty(), test_zmieniony_material_idzie_na_gpu_z_powodem()

### Community 178 - "jobs.py"
Cohesion: 0.27
Nodes (7): _clear_pending(), _job_id(), _mark_done(), _pending_key(), recheck_job(), _seen_key(), test_recheck_goes_to_low_priority_shared_queue()

### Community 179 - "Moduł 1 – przepływ danych i kontrakty"
Cohesion: 0.05
Nodes (31): Bezpieczeństwo łańcucha dostaw, Czego nie oddaliśmy asystentowi, Jak pracowaliśmy z asystentami AI, Jak sprawdzaliśmy, czy model ocenia dobrze, Narzędzia, Przebieg pracy, Instalacja Dockera na Windows, Licencje komponentów (+23 more)

### Community 181 - "Shell.jsx"
Cohesion: 0.31
Nodes (8): MenuIcon(), savePinned(), Shell(), storedPinned(), BRAND, DEFAULT_USER, ICON, NAV_GROUPS

### Community 182 - "test_contracts_copy.py"
Cohesion: 0.28
Nodes (3): _load_analyzer(), test_fixtures_validate(), test_schema_identical_with_analyzer()

### Community 183 - "scraper-worker-render"
Cohesion: 0.22
Nodes (9): cpus, env_file, image, mem_limit, networks, restart, shm_size, volumes (+1 more)

### Community 184 - "backfill_summaries.py"
Cohesion: 0.33
Nodes (5): _normalize_doc(), backfill(), _doc_of(), _finding_of(), main()

### Community 185 - "state.py"
Cohesion: 0.28
Nodes (3): SeenSet, test_seen_set_redis_dedup(), test_seen_set_and_node_cache_in_memory()

### Community 186 - "test_spojnosc.py"
Cohesion: 0.07
Nodes (6): TestBudowanieZCasedb, TestFleksjiWRouterze, TestPortHealth, TestWzorcowOsiCzasu, TestZaleznosci, TestZgodnosciKolejkiMiedzySerwisami

### Community 187 - "scope_gate.py"
Cohesion: 0.32
Nodes (4): _broker_with_context(), _find_any(), has_financial_signal(), _has_return_rate()

### Community 189 - "casedb_batch.py"
Cohesion: 0.36
Nodes (3): main(), make_analyzer(), run_file()

### Community 190 - "resources"
Cohesion: 0.29
Nodes (6): resources, deploy, devices, reservations, services, ollama

### Community 191 - "Zbiór z etykietami Modułu 1"
Cohesion: 0.40
Nodes (4): Rubryka etykiet, Uczciwość pomiaru, Użycie, Zbiór z etykietami Modułu 1

### Community 192 - "nginx"
Cohesion: 0.29
Nodes (7): cpus, image, mem_limit, networks, ports, volumes, nginx

### Community 193 - "facebook"
Cohesion: 0.40
Nodes (4): facebook, q, tag, type

### Community 195 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 197 - "test_www_sends_rotated_ua_and_proxy_per_request"
Cohesion: 0.40
Nodes (4): test_www_direct_connection_without_proxies(), test_www_sends_rotated_ua_and_proxy_per_request(), fake_client(), handler()

## Knowledge Gaps
- **2 isolated node(s):** `casedb`, `graphify skill`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1528 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `knf_snapshot.py`, `test_stt.py`, `test_worker.py`, `httpx`, `test_summary.py`, `datetime`, `Finding`, `test_config.py`, `OllamaClient`, `YouTubeSource`, `test_lang_consistency.py`, `test_collector.py`, `test_batches.py`, `AdDocument`, `batching.py`, `Engine`, `LocalCorpusSource`, `TestAnalyze`, `Transcript`, `pipeline.py`, `meta_json.py`, `test_facebook_contract.py`, `LocalBlobStore`, `analyze`, `www.py`, `reresolve.py`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `tiktok.py`, `export_gold_documents.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `scraper/contracts.py`, `SourceGone`, `test_llm_speed.py`, `TestGranicyKontraktu`, `test_idempotency_gate.py`, `test_live_regressions.py`, `test_module3.py`, `backfill_summaries.py`, `eval_rules.py`, `gen_facebook_examples.py`, `test_batches.py`, `requalify.py`, `TestPozaZakresemBezOceny`, `build_source`, `resolve`, `ApiError`, `TestWorkeraZDetResults`, `test_pipeline.py`, `module3.py`, `test_rules_det.py`, `test_rule_13.py`, `Registry`, `FakeStore`, `parse_args`, `eval_module1.py`, `SourceBlocked`, `test_module3_wiring.py`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 207 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 207 INFERRED edges - model-reasoned connections that need verification._
- **What connects `casedb`, `graphify skill` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_autoscaler.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05795918367346939 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `test_guards.py` to `test_registry.py`, `httpx`, `test_summary.py`, `Finding`, `test_config.py`, `OllamaClient`, `test_lang_consistency.py`, `test_batches.py`, `batching.py`, `Engine`, `TestAnalyze`, `Transcript`, `pipeline.py`, `analyze`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `scraper/contracts.py`, `test_llm_speed.py`, `test_live_regressions.py`, `test_module3.py`, `eval_rules.py`, `casedb_batch.py`, `test_batches.py`, `risk_score`, `TestWorkeraZDetResults`, `test_pipeline.py`, `module3.py`, `test_rules_det.py`, `test_rule_13.py`, `AdDocument`, `test_module3_wiring.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 130 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 130 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08067375886524823 - nodes in this community are weakly interconnected._