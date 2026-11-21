# Graph Report - panel-finalizacja  (2026-11-21)

## Corpus Check
- 340 files · ~1,250,346 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 42 file(s) not represented in the graph (top: (none) 18, .gz 8, .example 3)

## Summary
- 4116 nodes · 11030 edges · 188 communities (158 shown, 30 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 1142 edges (avg confidence: 0.92)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `268763cd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InvestWatch Platform Architecture
- Development Documentation and Skills
- AdDocument
- InvestWatch Challenge Description
- test_stt.py
- test_worker.py
- Relation
- test_evaluate.py
- httpx
- test_summary.py
- InvestWatch — dokument projektowy (design doc)
- Finding
- classify_scope
- _file
- test_config.py
- analyzer/contracts.py
- test_collector.py
- test_lang_consistency.py
- test_scaling_runtime.py
- test_batches.py
- InvestWatch — plan wykonawczy 23 h
- rules
- Engine
- LocalCorpusSource
- Enum
- rules_hybrid.py
- Integracja serwisów — kto wywołuje kogo
- Transcript
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
- test_jobs.py
- store.py
- RuleResult
- gpu
- test_scaling_endpoint.py
- parametrize
- scaling.py
- feed_fold_evidence
- test_module3.py
- test_partial_guard.py
- test_pool.py
- pytest
- eval_rules.py
- QueueState
- UrlStore
- dashboard/src/lib/labels.js
- infra – stos Docker Compose (projekt `investwatch`)
- api/store.py
- health.py
- casedb/store.py
- findings/FindingDetail.jsx
- youtube.py
- InvestWatch — stan projektu
- services
- postgres
- risk_score
- scraper: Moduł 1 (facebook, youtube, www)
- resolve
- healthcheck
- postgres
- ApiError
- TestWorkeraZDetResults
- test_pipeline.py
- test_pipeline.py
- sort.js
- Harmonogram i orkiestracja — dokument projektowy
- api
- ingest.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- Module1Report.jsx
- test_eval_rules.py
- casedb
- test_rules_det.py
- seaweedfs
- test_rule_13.py
- _doc
- test_api.py
- proximate
- Registry
- logging
- PostgresStore
- dashboard
- test_youtube.py
- knf.py
- dashboard/src/App.jsx
- FakeStore
- test_casedb_bridge.py
- RuleResult
- BaseModel
- test_casedb.py
- quote_is_verifiable
- parse_args
- analyzer — Moduł 2 (analiza AI)
- default_config
- AnalyzerConfig
- eval_module1.py
- scraper-worker
- environment
- typing
- resolver.py
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- Rule
- web/package.json
- README.md
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- knf_snapshot.py
- os
- _rule_6
- cosine
- scheduler
- dashboard/package.json
- AlertHub
- scraper/tests/test_contracts.py
- knf_registry.py
- InvestWatch
- client.js
- evidence.js
- YouTubeSource
- Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)
- Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)
- weights
- AdDocument
- ReportUnavailable
- Rotator
- valkey
- _default_spawn
- data.js
- views/Calibration.jsx
- typing
- reresolve.py
- server.js
- dictionary_from_registry
- test_alerts_db.py
- _QuietLogger
- test_discover_canonical_unique_and_limiter
- Global Constraints
- test_invalid_url_and_gone
- Global Constraints
- context
- FakeConn
- TranscriptSegment
- jobs
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- json
- knn_score
- TestGranicyKontraktu
- Moduł 1 – przepływ danych i kontrakty
- casedb
- scripts
- worker
- dashboard
- 10. Pozyskiwanie danych i bezpieczeństwo demo
- 8. Logika modułów
- 9. Scoring, threshold i metryki
- Zbiór z etykietami Modułu 1
- facebook
- 2. Cele, nie-cele, anty-cele
- audit.sh
- casedb

## God Nodes (most connected - your core abstractions)
1. `Verdict` - 227 edges
2. `AdDocument` - 215 edges
3. `RuleResult` - 141 edges
4. `analyze()` - 77 edges
5. `Engine` - 66 edges
6. `OllamaClient` - 65 edges
7. `EvidenceKind` - 63 edges
8. `FacebookAdsSource` - 61 edges
9. `Evidence` - 55 edges
10. `EntityResolution` - 52 edges

## Surprising Connections (you probably didn't know these)
- `Osoba C — `services/api`, `services/web`` --references--> `ApiClient`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/api_client.py
- `Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`)` --references--> `default_config()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/rules_llm/registry.py
- `4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py
- `6. Do udoskonalenia — uszeregowane po wpływie na demo` --references--> `risk_level()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/scoring.py
- `Co A wrzuca do kolejki` --references--> `analyze_document()`  [INFERRED]
  docs/INTEGRACJA.md → services/analyzer/analyzer/worker.py

## Import Cycles
- None detected.

## Communities (188 total, 30 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "AdDocument"
Cohesion: 0.05
Nodes (30): AdDocument, embed_document_text(), OllamaClient, rule_3_runner(), evaluate_batch_4(), build_config(), expected_rule_ids(), _merge_meta() (+22 more)

### Community 4 - "test_stt.py"
Cohesion: 0.05
Nodes (42): TranscriptSegment, _default_transcriber(), run(), _first_match_start(), normalize_text(), rate_anomaly(), risk_timing(), RiskTiming (+34 more)

### Community 5 - "test_worker.py"
Cohesion: 0.06
Nodes (41): health_payload(), analyze_document(), _build_det_results(), _detect_and_save_change(), handle_job(), Integracja z bazą (casedb, Moduł 1), _api(), handler() (+33 more)

### Community 6 - "Relation"
Cohesion: 0.06
Nodes (23): Relation, Routing, ScopeStatus, _blank(), _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business() (+15 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "httpx"
Cohesion: 0.05
Nodes (26): _download(), _max_bytes(), resolve_media(), _s3_to_http(), evaluate_batch_1(), _client(), _doc(), _generate_handler() (+18 more)

### Community 9 - "test_summary.py"
Cohesion: 0.11
Nodes (32): LlmError, build_summary(), FakeClient, _finding(), pg_conn(), _reason(), _rule(), test_auth_polarity_authorized() (+24 more)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.13
Nodes (14): 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 4. Rozważone podejścia, 5. Architektura, 7. Mapowanie 18 reguł na silniki (+6 more)

### Community 11 - "Finding"
Cohesion: 0.10
Nodes (26): Finding, _normalize_doc(), _advertiser(), _auth_state(), _authorization(), check_llm_reply(), _correction(), _data_values() (+18 more)

### Community 12 - "classify_scope"
Cohesion: 0.09
Nodes (8): classify_scope(), _find_any(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania, TestZwykleInstrumenty

### Community 13 - "_file"
Cohesion: 0.07
Nodes (18): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia, check_external_hosts(), check_forbidden_deps() (+10 more)

### Community 14 - "test_config.py"
Cohesion: 0.11
Nodes (19): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+11 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.09
Nodes (19): AdvertiserRef, Embedding, Entities, InvestmentFirmRef, MediaItem, Publisher, RegistryMatch, Scope (+11 more)

### Community 16 - "test_collector.py"
Cohesion: 0.08
Nodes (32): from_facebook_node(), collect_facebook_query(), CollectReport, seed_synthetic(), creative_key(), landing_key(), SourceBlocked, cand() (+24 more)

### Community 17 - "test_lang_consistency.py"
Cohesion: 0.09
Nodes (13): evaluate_batch_2(), assess_rule_10(), _result(), detect_language(), risk_sentences(), split_sentences(), _words(), _client() (+5 more)

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.12
Nodes (6): make_valkey_state_provider(), _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "test_batches.py"
Cohesion: 0.07
Nodes (22): evaluate_batch_3(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_historical_performance(), mentions_tax(), _by_id(), _client() (+14 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.10
Nodes (19): B — analyzer, C — api + web, Co zmieniło się po review zespołu (wersja 2), Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate, Podział roli (+11 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "Engine"
Cohesion: 0.11
Nodes (14): Engine, Evidence, EvidenceKind, missing_det_placeholders(), _crashed_rule_result(), guard_partial_result(), RuleBase, coverage() (+6 more)

### Community 23 - "LocalCorpusSource"
Cohesion: 0.12
Nodes (9): A — scraper + reguły DET, run(), Source, LocalCorpusSource, results(), test_document_id_independent_of_url(), test_documents_follow_contract(), test_page_verdicts_match_labels() (+1 more)

### Community 24 - "Enum"
Cohesion: 0.08
Nodes (52): App(), TABS, Alerts(), axis, Calibration(), SERIES, Evidence(), FindingDetail() (+44 more)

### Community 25 - "rules_hybrid.py"
Cohesion: 0.12
Nodes (13): ViewportProbe, _center_y(), _first_match_offset(), _matches(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline() (+5 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.15
Nodes (11): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, api (osoba C) (+3 more)

### Community 28 - "Transcript"
Cohesion: 0.09
Nodes (28): analyzer_version(), _bodies(), case_to_document(), finding_to_ai_result(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case() (+20 more)

### Community 29 - "meta_json.py"
Cohesion: 0.08
Nodes (38): doc_from_node(), _finserv(), ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), ads_from_html(), _cards() (+30 more)

### Community 30 - "RuntimeError"
Cohesion: 0.07
Nodes (30): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+22 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.09
Nodes (14): fetch(), canonical_ad_url(), doc(), source(), test_auto_mode_falls_back_to_fixture_when_breaker_open(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls(), test_document_matches_frozen_contract() (+6 more)

### Community 32 - "json"
Cohesion: 0.07
Nodes (19): _fb_source_factory(), download_ytdlp(), probe_duration(), main(), FacebookConfig, LocalBlobStore, test_facebook_uses_shared_rotator_per_context(), test_no_proxy_by_default() (+11 more)

### Community 33 - "analyze"
Cohesion: 0.07
Nodes (19): analyze(), AnalyzerConfig, _ensure_transcript(), _ensure_vector_representation(), EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie (+11 more)

### Community 34 - "www.py"
Cohesion: 0.08
Nodes (17): Pluginowalne źródła, AdDocument, SourceError, SourceGone, _is_page_link(), _origin(), _Page, WebPageSource (+9 more)

### Community 35 - "re"
Cohesion: 0.15
Nodes (4): document_row(), _iso(), _row_to_document(), SqlStore

### Community 36 - "test_change_detect.py"
Cohesion: 0.13
Nodes (37): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 6: Klasyfikacja zdarzenia, _basis(), _cosine(), detect_change(), event(), detect_disappeared() (+29 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.23
Nodes (22): RenderProbe, det_fallback_results(), _by(), _doc(), _doc2(), _node(), _run(), test_brak_probe_nic_nie_liczy() (+14 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.12
Nodes (10): TextNode, assess_rule_3(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestProporcjonalnosciCzcionki (+2 more)

### Community 39 - "scheduler.py"
Cohesion: 0.09
Nodes (19): expand(), JobSpec, load_schedule(), main(), register(), _registry_queries(), run_once(), Task (+11 more)

### Community 40 - "test_guards.py"
Cohesion: 0.16
Nodes (32): Verdict, apply_rule_10_override(), _res(), _run(), test_12a_jeden_rok_pass_zamieniony_na_fail(), test_12a_nie_zamienia_fail_na_pass(), test_12a_pelny_okres_zostaje_pass(), test_12b_pass_bez_walut_i_oplat_to_fail() (+24 more)

### Community 41 - "FacebookAdsSource"
Cohesion: 0.11
Nodes (6): download_direct(), collect_ads_from_dom(), FacebookAdsSource, _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.14
Nodes (7): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), _doc(), TestKorpusuNaTejMaszynie, TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.13
Nodes (16): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_nodes_are_not_visible_even_with_layout_box() (+8 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.12
Nodes (20): AdvertiserRef, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities, EvidenceKind (+12 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.09
Nodes (10): CircuitBreaker, NodeCache, RateLimiter, SeenSet, FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures(), test_rate_limiter_spaces_requests() (+2 more)

### Community 46 - "test_jobs.py"
Cohesion: 0.18
Nodes (8): doc(), env(), FakeConn, FakeSource, test_build_source_www_and_unknown(), test_fetch_job_gone(), test_fetch_job_records_resolves_and_enqueues(), test_fetch_job_unqualified_is_not_analyzed()

### Community 47 - "store.py"
Cohesion: 0.16
Nodes (17): BBox, RenderProbe, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score() (+9 more)

### Community 48 - "RuleResult"
Cohesion: 0.12
Nodes (23): RuleResult, load_prompt(), normalize(), _all_not_applicable(), _build_result(), evaluate_batch(), _normalize_for_match(), _not_applicable() (+15 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.23
Nodes (8): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), test_nieznana_sciezka_nadal_daje_404()

### Community 51 - "parametrize"
Cohesion: 0.07
Nodes (28): _alert_loop(), alert_payload(), coverage(), create_app(), finding_events(), get_document(), get_finding(), health() (+20 more)

### Community 52 - "scaling.py"
Cohesion: 0.18
Nodes (9): _connection(), _int(), _parse(), QueuePolicy, _rq_backlog_reader(), _read(), _rq_worker_counter(), _count() (+1 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.14
Nodes (13): feed_fold_evidence(), FeedFoldEvidence, platform_rule_override(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "test_module3.py"
Cohesion: 0.18
Nodes (21): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _na(), _result(), _boom(), _client(), wrapped() (+13 more)

### Community 55 - "test_partial_guard.py"
Cohesion: 0.35
Nodes (9): _doc(), _rule(), _run(), test_partial_fail_braku_staje_sie_na(), test_partial_fail_obecnosci_zostaje(), test_partial_regula_10_i_pass_bez_zmian(), test_pelna_transkrypcja_bez_zmian(), test_reguly_brakujacego_zastrzezenia_sa_degradowane() (+1 more)

### Community 56 - "test_pool.py"
Cohesion: 0.11
Nodes (16): Zadanie 4: Executor `pool`, DryRunExecutor, PoolExecutor, ScalingConfig, ScalingDecision, _d(), FakeSpawn, FakeWorker (+8 more)

### Community 57 - "pytest"
Cohesion: 0.15
Nodes (16): load_scaling_config(), ScalingConfigError, validate_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+8 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.13
Nodes (15): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+7 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "UrlStore"
Cohesion: 0.14
Nodes (7): reprioritize(), process_one(), _now(), open_store(), PostgresUrlStore, SqliteUrlStore, UrlStore

### Community 61 - "dashboard/src/lib/labels.js"
Cohesion: 0.21
Nodes (11): AssigneeTag(), COLS, StatusSelect(), ANALYSTS, ASSIGNED_BY, DECISION, HUMAN_ONLY, RISK (+3 more)

### Community 62 - "infra – stos Docker Compose (projekt `investwatch`)"
Cohesion: 0.25
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, infra – stos Docker Compose (projekt `investwatch`), Metryki do panelu, Ollama, Serwisy, Szybki start: caly stos jedną komendą, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), Uwagi eksploatacyjne

### Community 63 - "api/store.py"
Cohesion: 0.14
Nodes (9): AdDocument, Finding, main(), seed(), finding_row(), InvalidId, open_store(), UpsertResult (+1 more)

### Community 64 - "health.py"
Cohesion: 0.22
Nodes (3): _Handler, _no_states(), _scaling_response()

### Community 65 - "casedb/store.py"
Cohesion: 0.09
Nodes (26): API modulu 1 (store.py), from_ad_document(), from_youtube(), youtube_video_id(), add_asset(), Asset, Case, case_id_for() (+18 more)

### Community 66 - "findings/FindingDetail.jsx"
Cohesion: 0.23
Nodes (19): RiskBadge(), AssigneeSelect(), Evidence(), FindingDetail(), RulesTable(), summaryLabel(), yn(), AiSuggestion() (+11 more)

### Community 67 - "youtube.py"
Cohesion: 0.16
Nodes (11): evidence(), _handle(), is_language(), language_factory(), normalize(), _published_at(), signals_in(), video_id() (+3 more)

### Community 68 - "InvestWatch — stan projektu"
Cohesion: 0.11
Nodes (17): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Trafność Modułu 2 — pomiary na żywym Bieliku 4.5B (21.11, noc), 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły (+9 more)

### Community 69 - "services"
Cohesion: 0.10
Nodes (20): name, networks, investwatch, image, networks, ports, volumes, image (+12 more)

### Community 70 - "postgres"
Cohesion: 0.19
Nodes (15): depends_on, depends_on, condition, depends_on, casedb, postgres, scraper-worker, seaweedfs (+7 more)

### Community 71 - "risk_score"
Cohesion: 0.05
Nodes (32): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+24 more)

### Community 72 - "scraper: Moduł 1 (facebook, youtube, www)"
Cohesion: 0.29
Nodes (6): Collector i flota (praca ciągła), `.env`, Jak to działa, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: Moduł 1 (facebook, youtube, www)

### Community 73 - "resolve"
Cohesion: 0.14
Nodes (32): _result(), has_disclosure(), resolve(), doc(), _firm(), test_active_firm_beats_historical_duplicate_and_inactive_reason(), test_affiliate_variants(), test_affiliate_without_disclosure() (+24 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (10): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+2 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 76 - "ApiError"
Cohesion: 0.13
Nodes (12): Global Constraints, Panel nadzorcy — finalizacja (osoba B), Spec (wiążący), Task 1: Podsumowanie AI findingu (analyzer), Task 2: API — podsumowanie w odpowiedzi i alerty WebSocket z bazy, Task 4: Panel — widok „Moduł 1 — raport”, ApiClient, ApiError (+4 more)

### Community 78 - "test_pipeline.py"
Cohesion: 0.09
Nodes (20): Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), _simhash_int(), classify_similarity(), hamming_distance(), is_near_duplicate_simhash(), normalize() (+12 more)

### Community 79 - "test_pipeline.py"
Cohesion: 0.32
Nodes (7): Evidence, RuleResult, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "sort.js"
Cohesion: 0.15
Nodes (8): Task 3: Panel — sortowanie i szczegółowy raport pozycji, items, cmp(), KEYS, publisher(), RISK_RANK, sortFindings(), items

### Community 81 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.22
Nodes (8): CZĘŚĆ A — Autoskaler, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera

### Community 82 - "api"
Cohesion: 0.20
Nodes (10): build, environment, networks, ports, restart, volumes, ALERT_LOOKBACK_S, ALERT_POLL_S (+2 more)

### Community 83 - "ingest.py"
Cohesion: 0.39
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.40
Nodes (5): env_file, extra_hosts, networks, restart, analyzer

### Community 86 - "Module1Report.jsx"
Cohesion: 0.32
Nodes (13): buildQuery(), clip(), csvUrl(), flagLabel(), FLAGS, relationLabel(), RELATIONS, safeHref() (+5 more)

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
Cohesion: 0.22
Nodes (20): BBox, assess_rule_13(), _na(), _result(), rule_13_runner(), _doc(), _node(), test_brak_wynikow_historycznych_to_not_applicable() (+12 more)

### Community 92 - "_doc"
Cohesion: 0.10
Nodes (13): Task 5: API — raport Modułu 1 (JSON + CSV), _json_default(), _load(), main(), _to_csv(), _write(), connect(), migrate() (+5 more)

### Community 93 - "test_api.py"
Cohesion: 0.16
Nodes (27): client(), load(), _postgres_store(), seeded(), store(), test_assign_and_release(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless() (+19 more)

### Community 94 - "proximate"
Cohesion: 0.17
Nodes (12): _domains(), find_targets(), _group(), host(), _on_domain(), proximate(), sentences(), _url_host() (+4 more)

### Community 95 - "Registry"
Cohesion: 0.16
Nodes (12): Task 2: Pełny rejestr KNF w dopasowaniu (zagraniczne firmy, agenci, cofnięte zezwolenia), normalize_name(), test_normalize_name(), Publisher, _handle_key(), Registry, test_build_source_youtube_uses_registry_rows(), reg() (+4 more)

### Community 96 - "logging"
Cohesion: 0.10
Nodes (13): run_collector(), write_stats(), CollectorConfig, CollectorConfigFiles, ConfigFile, _load_yaml(), parse_lexicons(), parse_personas() (+5 more)

### Community 97 - "PostgresStore"
Cohesion: 0.09
Nodes (5): PostgresStore, pg(), pg(), test_csv_exports_all_rows_beyond_page(), test_csv_formula_injection_neutralised()

### Community 98 - "dashboard"
Cohesion: 0.12
Nodes (16): condition, build, depends_on, environment, networks, ports, restart, api (+8 more)

### Community 99 - "test_youtube.py"
Cohesion: 0.27
Nodes (12): make_clips(), info(), make(), patched(), segs(), test_clip_short_with_target_and_signal(), test_distant_target_does_not_create_clip(), test_fetch_qualified_document() (+4 more)

### Community 100 - "knf.py"
Cohesion: 0.11
Nodes (14): load_snapshot(), lookup(), name_key(), read_snapshot(), knf_agent_keys(), _knf_country(), registry_entries(), sync_registry_from_knf() (+6 more)

### Community 101 - "dashboard/src/App.jsx"
Cohesion: 0.12
Nodes (15): connectAlerts(), App(), FILTER_GROUPS, timeRange(), VIEWS, ErrorBoundary, Flyout(), Toasts() (+7 more)

### Community 102 - "FakeStore"
Cohesion: 0.14
Nodes (7): FakeStore, test_worker_posts_finding_before_summary(), test_worker_saves_summary(), test_worker_summary_disabled(), test_worker_summary_error_does_not_break_save(), test_worker_summary_write_failure_keeps_finding(), boom()

### Community 103 - "test_casedb_bridge.py"
Cohesion: 0.07
Nodes (20): claim(), connect(), fetch_case(), _jsonb(), _plain(), process_cases(), save_ai_result(), set_status() (+12 more)

### Community 104 - "RuleResult"
Cohesion: 0.21
Nodes (9): RuleBase, _DetRule, Rule4FontSize, Rule5Contrast, Rule6Hidden, Rule7OneClick, Rule8Responsive, _short() (+1 more)

### Community 105 - "BaseModel"
Cohesion: 0.20
Nodes (8): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column()

### Community 106 - "test_casedb.py"
Cohesion: 0.17
Nodes (22): Okresowa aktualizacja, content_hash(), load_registry(), record_document(), report_module1(), save_finding(), _doc(), _finding() (+14 more)

### Community 114 - "parse_args"
Cohesion: 0.15
Nodes (6): serve(), main(), parse_args(), _start_health_server(), run(), TestFlagiKolejkiWWorkerze

### Community 115 - "analyzer — Moduł 2 (analiza AI)"
Cohesion: 0.22
Nodes (9): analyzer — Moduł 2 (analiza AI), Brama zakresu, Konfiguracja, Mapa plików, Quick Start, Uruchomienie, Weryfikacja cytatu, Wymagania sprzętowe (+1 more)

### Community 116 - "default_config"
Cohesion: 0.25
Nodes (5): default_config(), _FakeApi, test_default_config_ma_wszystkie_runnery_modulu_2(), test_default_config_wpina_whisper_gdy_wlaczony(), test_worker_bez_configu_uzywa_pelnego_potoku()

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
Cohesion: 0.22
Nodes (14): environment, environment, ANALYZER_STORE, API_BASE_URL, DATABASE_URL, FB_FIXTURES_DIR, OLLAMA_BASE_URL, S3_ACCESS_KEY (+6 more)

### Community 121 - "typing"
Cohesion: 0.16
Nodes (8): default_worker_id(), make_fetcher(), make_pipeline(), pipeline(), run_fleet(), _save_document(), wants_analysis(), test_analyzer_threshold_and_optional_instrument_lane()

### Community 122 - "resolver.py"
Cohesion: 0.10
Nodes (14): _fold(), document_text(), extract_urls(), find_affiliate_link(), Firm, fold_words(), host_of(), _inactive_reason() (+6 more)

### Community 123 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### Community 125 - "web/package.json"
Cohesion: 0.11
Nodes (21): dependencies, react@18.3.1, react-dom@18.3.1, recharts@2.13.3, devDependencies, vite@5.4.11, @vitejs/plugin-react@4.3.4, react (+13 more)

### Community 126 - "README.md"
Cohesion: 0.22
Nodes (3): Skan zależności, Uruchomienie (dev), web (osoba C)

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Korekty niespojnosci danych (nie dopasowanie do wyniku), Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

### Community 131 - "knf_snapshot.py"
Cohesion: 0.11
Nodes (10): test_broken_lexicon_keeps_last_good_version(), test_unknown_lexicon_kind_rejected(), CardParser, clean(), fetch(), last_page(), main(), parse_cards() (+2 more)

### Community 132 - "os"
Cohesion: 0.06
Nodes (30): build_facebook_source(), build_source(), discover_job(), _enqueue_analysis(), _fetch(), fetch_job(), _job_id(), _job_slug() (+22 more)

### Community 133 - "_rule_6"
Cohesion: 0.29
Nodes (10): _dominant_font_px(), _evidence(), _na(), _result(), _risk_hits(), _rule_4(), _rule_5(), _rule_6() (+2 more)

### Community 135 - "scheduler"
Cohesion: 0.25
Nodes (8): command, env_file, image, networks, restart, shm_size, volumes, scheduler

### Community 136 - "dashboard/package.json"
Cohesion: 0.13
Nodes (20): concurrently, ws, dependencies, react@18.3.1, react-dom@18.3.1, recharts@2.13.3, ws@8.23.0, devDependencies (+12 more)

### Community 138 - "scraper/tests/test_contracts.py"
Cohesion: 0.22
Nodes (3): test_contract_copy_matches_analyzer(), test_example_validates(), test_facebook_golden_examples()

### Community 139 - "knf_registry.py"
Cohesion: 0.10
Nodes (12): _normalize(), _Extractor, fetch_register(), fold(), main(), make_id(), merge(), name_key() (+4 more)

### Community 140 - "InvestWatch"
Cohesion: 0.25
Nodes (8): Bezpieczeństwo łańcucha dostaw, Instalacja Dockera na Windows, InvestWatch, Po `git pull`, Quick Start, Serwisy, Struktura, Wymagania

### Community 141 - "client.js"
Cohesion: 0.26
Nodes (12): allFindings(), cache, http(), invalidate(), patch(), applyFilters(), asList(), count() (+4 more)

### Community 142 - "evidence.js"
Cohesion: 0.54
Nodes (6): fmtTs(), fmtValue(), fmtViewport(), formatEvidence(), isHttp(), safeHttpUrl()

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
Nodes (18): ChangeEvent, _casedb(), DbStore, StoreError, _vector_of(), test_close(), test_error_wrapped_with_rollback(), test_get_document_and_commit() (+10 more)

### Community 150 - "Rotator"
Cohesion: 0.21
Nodes (9): proxies(), Rotator, _split(), user_agents(), test_from_env(), test_proxies_list_fallback_and_empty(), test_rotator_picks_from_lists(), test_rotator_without_proxy_and_headers() (+1 more)

### Community 151 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 153 - "data.js"
Cohesion: 0.18
Nodes (16): ANALYSTS, FIRMS, HUMAN_ONLY, levelFor(), makeFinding(), makeFindings(), makeGold(), pick() (+8 more)

### Community 154 - "views/Calibration.jsx"
Cohesion: 0.19
Nodes (17): api, Breakdown(), LEVELS, TrendChart(), Panel(), StatTile(), FindingsTable(), describe() (+9 more)

### Community 155 - "typing"
Cohesion: 0.09
Nodes (13): Lexicons, normalize(), _term_re(), affiliate_params(), Candidate, _publisher_is_official(), score(), Scored (+5 more)

### Community 156 - "reresolve.py"
Cohesion: 0.16
Nodes (7): _Cur, _FakeConn, test_run_skips_bad_cases_and_continues(), test_summarize_counts_changes(), main(), run(), summarize()

### Community 157 - "server.js"
Cohesion: 0.14
Nodes (18): ALERT_EVERY_MS, applyFilters(), count(), events, findings, gold, io, listParam() (+10 more)

### Community 158 - "dictionary_from_registry"
Cohesion: 0.40
Nodes (3): dictionary_from_registry(), queries_for(), test_dictionary_from_registry_and_queries()

### Community 159 - "test_alerts_db.py"
Cohesion: 0.20
Nodes (13): SqliteStore, _finding(), _poll(), test_bad_env_falls_back(), test_direct_db_high_alerts_once(), test_low_does_not_alert(), test_low_updated_to_high_alerts_once(), test_out_of_order_insert_still_alerts() (+5 more)

### Community 162 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Moduł 1 — profesjonalne domknięcie, Spec (wiążący), Task 1: Zbiór z etykietami Modułu 1 i ewaluacja (PRZED zmianami resolvera), Task 3: Relacja oficjalny/podmiot trzeci, ujawnienia, ponowne rozwiązanie bazy, Task 4: Raport Modułu 1 — flagi naruszeń, kampanie, zrzut, Task 6: Zakładka „Moduł 1” w działającym panelu (`services/web`)

### Community 164 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Decyzje, Docelowa topologia (`infra/docker-compose.yml`, projekt `investwatch`), Global Constraints, Pełna infrastruktura w Dockerze — projekt i plan, Spec (wiążący), Task 1: Analyzer zapisuje dokument w API przed findingiem, Task 2: Obraz scrapera, launchery workera i harmonogramu, Task 3: Compose — wszystkie serwisy, `.env.example` (+1 more)

### Community 165 - "context"
Cohesion: 0.27
Nodes (10): build, context, dockerfile, build, networks, profiles, restart, build (+2 more)

### Community 166 - "FakeConn"
Cohesion: 0.20
Nodes (3): fake_casedb(), rec(), FakeConn

### Community 168 - "jobs"
Cohesion: 0.14
Nodes (14): jobs, enabled, interval_minutes, kind, limit, name, older_than_minutes, queries (+6 more)

### Community 170 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.20
Nodes (10): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba (+2 more)

### Community 173 - "json"
Cohesion: 0.09
Nodes (9): test_finding_moze_nalezec_do_wielu_modulow(), test_przyklad_waliduje_sie_przeciw_modelowi(), test_rule_result_ma_dowod_dla_kazdego_werdyktu(), items(), test_tylko_jedna_reklama_ma_render_probe(), main(), run_file(), main() (+1 more)

### Community 174 - "knn_score"
Cohesion: 0.24
Nodes (6): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h), knn_score(), TestKnnScore

### Community 179 - "Moduł 1 – przepływ danych i kontrakty"
Cohesion: 0.29
Nodes (6): Jedno źródło prawdy: casedb, Kontrakt zadania analizy (kolejka `q:gpu`), Moduł 1 – przepływ danych i kontrakty, Przepływ, Uruchomienie i harmonogram, Źródła

### Community 180 - "casedb"
Cohesion: 0.33
Nodes (6): build, command, networks, restart, volumes, casedb

### Community 182 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, mock, preview, test, web

### Community 186 - "worker"
Cohesion: 0.20
Nodes (4): TestPortHealth, claim(), test_claim_is_exclusive(), worker()

### Community 187 - "dashboard"
Cohesion: 0.33
Nodes (5): dashboard, Punkty połączenia z bazą, Uruchomienie (dev), Uruchomienie (Docker), Widoki

### Community 188 - "10. Pozyskiwanie danych i bezpieczeństwo demo"
Cohesion: 0.50
Nodes (4): 10. Pozyskiwanie danych i bezpieczeństwo demo, Bezpieczeństwo demo (anty-cel: „demo zależne od wifi"), Cybersec (kryterium oceniane wprost), Kolejka i harmonogram

### Community 189 - "8. Logika modułów"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 190 - "9. Scoring, threshold i metryki"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 191 - "Zbiór z etykietami Modułu 1"
Cohesion: 0.40
Nodes (4): Rubryka etykiet, Uczciwość pomiaru, Użycie, Zbiór z etykietami Modułu 1

### Community 193 - "facebook"
Cohesion: 0.40
Nodes (4): facebook, q, tag, type

### Community 195 - "2. Cele, nie-cele, anty-cele"
Cohesion: 0.50
Nodes (4): 2. Cele, nie-cele, anty-cele, Anty-cele (to by oznaczało porażkę, nawet gdyby „działało"), Cele (musi być), Nie-cele (świadomie pomijamy)

## Knowledge Gaps
- **10 isolated node(s):** `casedb`, `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1343 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_stt.py`, `_rule_6`, `Relation`, `test_worker.py`, `httpx`, `test_summary.py`, `os`, `Finding`, `scraper/tests/test_contracts.py`, `analyzer/contracts.py`, `YouTubeSource`, `test_lang_consistency.py`, `test_collector.py`, `test_batches.py`, `AdDocument`, `Engine`, `LocalCorpusSource`, `rules_hybrid.py`, `Transcript`, `meta_json.py`, `reresolve.py`, `test_facebook_contract.py`, `json`, `analyze`, `www.py`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `FacebookAdsSource`, `test_stt_pipeline.py`, `json`, `test_jobs.py`, `store.py`, `RuleResult`, `TestGranicyKontraktu`, `test_module3.py`, `test_partial_guard.py`, `eval_rules.py`, `youtube.py`, `resolve`, `ApiError`, `TestWorkeraZDetResults`, `test_pipeline.py`, `test_pipeline.py`, `test_rules_det.py`, `test_rule_13.py`, `Registry`, `FakeStore`, `RuleResult`, `eval_module1.py`, `typing`, `resolver.py`, `Rule`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 187 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 187 INFERRED edges - model-reasoned connections that need verification._
- **What connects `casedb`, `Analytical / AI Modules`, `Web Dashboard` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AdDocument` be split into smaller, more focused modules?**
  _Cohesion score 0.05134825014343087 - nodes in this community are weakly interconnected._
- **Why does `risk_score()` connect `risk_score` to `analyze`, `Relation`, `assess_rule_3`, `test_guards.py`, `sort.js`, `RuleResult`, `analyzer — Moduł 2 (analiza AI)`, `Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)`, `test_batches.py`, `Engine`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 117 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 117 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05368421052631579 - nodes in this community are weakly interconnected._