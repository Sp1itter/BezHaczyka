# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 197 files · ~1,153,169 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 13, .gz 8, .example 3)

## Summary
- 2722 nodes · 7114 edges · 148 communities (122 shown, 26 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 767 edges (avg confidence: 0.93)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `92bbb757`
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
- re
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
- rules_hybrid.py
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
- AdDocument
- AnalyzerConfig
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
- test_pipeline.py
- test_pipeline.py
- collect_ads_from_dom
- Harmonogram i orkiestracja — dokument projektowy
- casedb
- ingest.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- LocalBlobStore
- test_eval_rules.py
- casedb
- test_preconditions.py
- seaweedfs
- test_rule_13.py
- _doc
- test_api.py
- TestGranicyKontraktu
- batching.py
- health_payload
- valkey
- web
- demo.py
- ApiClient
- .test_search_deduplicates_ids_and_respects_candidate_limit
- casedb_batch.py
- test_casedb_bridge.py
- quote_is_verifiable
- BaseModel
- test_casedb.py
- batching.py
- parse_args
- default_config
- change_detect.py
- AnalyzerConfig
- ._api
- RuleRunner
- make_tts_fixture.ps1
- test_idempotency_gate.py
- migrations/__init__.py
- 6. Kontrakty danych (ZAMROŻONE o 12:30)
- gen_facebook_examples.py
- TestBramkiWsadu4
- web (osoba C)
- analyzer/tests/conftest.py
- Zbior regresyjny Modulu 2 (SYNTETYCZNY)
- registry.py
- gen_facebook_examples.py
- _rule_6
- cosine
- best_threshold
- load_gold
- .test_niedostepny_model_daje_none_nie_wyjatek
- classify_similarity
- max_breach_severity
- TestInterfejsRule
- 2. Cele, nie-cele, anty-cele
- T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)
- TranscriptSegment
- Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)
- Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)
- Drabinka cięcia zakresu

## God Nodes (most connected - your core abstractions)
1. `Verdict` - 200 edges
2. `AdDocument` - 143 edges
3. `RuleResult` - 111 edges
4. `analyze()` - 70 edges
5. `Engine` - 62 edges
6. `OllamaClient` - 62 edges
7. `EvidenceKind` - 60 edges
8. `Evidence` - 51 edges
9. `AnalyzerConfig` - 51 edges
10. `FacebookAdsSource` - 49 edges

## Surprising Connections (you probably didn't know these)
- `Zadanie 5: Kontrakt `ChangeEvent` i diff reguł` --references--> `diff_rule_results()`  [INFERRED]
  docs/superpowers/plans/2026-11-21-harmonogram-implementacja.md → services/analyzer/analyzer/change_detect.py
- `B — analyzer` --references--> `knn_score()`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-plan-24h.md → services/analyzer/analyzer/embeddings.py
- `Układ repozytorium` --references--> `Rule`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/rules_llm/base.py
- `Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`)` --references--> `default_config()`  [INFERRED]
  docs/STAN-PROJEKTU.md → services/analyzer/analyzer/rules_llm/registry.py
- `Jak dodac pozycje` --references--> `risk_score()`  [INFERRED]
  fixtures/gold/README.md → services/analyzer/analyzer/scoring.py

## Import Cycles
- None detected.

## Communities (148 total, 26 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.19
Nodes (13): build_config(), coverage_report(), module2_runners(), _all_pass_handler(), _client(), _doc(), _down_handler(), _entities() (+5 more)

### Community 4 - "test_stt.py"
Cohesion: 0.08
Nodes (37): _default_transcriber(), run(), _transcribe(), rate_anomaly(), risk_timing(), RiskTiming, speech_rate(), SttError (+29 more)

### Community 5 - "test_worker.py"
Cohesion: 0.06
Nodes (46): Co A wrzuca do kolejki, 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Trafność Modułu 2 — pomiary na żywym Bieliku 4.5B (21.11, noc), 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły (+38 more)

### Community 6 - "Relation"
Cohesion: 0.09
Nodes (16): Routing, _blank(), _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), mask_non_claims(), _matches_any() (+8 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.07
Nodes (18): is_flagged(), TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow, TestRaport (+10 more)

### Community 8 - "httpx"
Cohesion: 0.15
Nodes (16): _download(), _max_bytes(), resolve_media(), _s3_to_http(), _client(), test_http_download_and_cache_reuse(), handler(), test_http_error_status_returns_none() (+8 more)

### Community 9 - "risk_score"
Cohesion: 0.14
Nodes (7): risk_level(), risk_score(), _rule(), TestEskalacjiPoNajciezszymNaruszeniu, TestNotApplicableNieWchodziDoMianownika, TestRiskLevel, TestRiskScore

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.18
Nodes (10): 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 5. Architektura, 7. Mapowanie 18 reguł na silniki, InvestWatch — dokument projektowy (design doc) (+2 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.09
Nodes (8): classify_scope(), _find_any(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania, TestZwykleInstrumenty

### Community 13 - "_file"
Cohesion: 0.10
Nodes (6): _file(), TestCalegoRepozytorium, TestCelowScrapowania, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.11
Nodes (19): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+11 more)

### Community 15 - "analyzer/contracts.py"
Cohesion: 0.10
Nodes (19): AdvertiserRef, BBox, Embedding, Entities, Finding, InvestmentFirmRef, Publisher, RegistryMatch (+11 more)

### Community 16 - "Verdict"
Cohesion: 0.13
Nodes (24): LlmError, load_prompt(), advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _na(), _result(), _normalize() (+16 more)

### Community 17 - "re"
Cohesion: 0.06
Nodes (26): evaluate_batch_2(), apply_rule_10_override(), assess_rule_10(), detect_language(), risk_sentences(), split_sentences(), _words(), _client() (+18 more)

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.13
Nodes (5): _provider(), read_queue_states(), TestDostawcyStanu, TestOdczytuStanuKolejek, padajacy()

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.17
Nodes (11): Co zmieniło się po review zespołu (wersja 2), InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate, Rejestr ryzyk, T+10.5 — 22:00–01:30 · Dopięcie i polish (3,5 h), T+14 — 01:30–02:00 · Commit, push, tag, T+14.5 — 02:00–06:00 · Rotacja snu (4 h), T+18.5 — 06:00–08:00 · Dokumentacja i cybersec (2 h) (+3 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "RuleResult"
Cohesion: 0.13
Nodes (17): Engine, Evidence, EvidenceKind, RuleResult, missing_det_placeholders(), _crashed_rule_result(), guard_partial_result(), _result() (+9 more)

### Community 23 - "AdDocument"
Cohesion: 0.19
Nodes (4): _doc(), _rule(), _runner(), TestAnalyze

### Community 24 - "Enum"
Cohesion: 0.06
Nodes (62): react, react-dom, recharts, vite, @vitejs/plugin-react, dependencies, react@18.3.1, react-dom@18.3.1 (+54 more)

### Community 25 - "test_casedb_bridge.py"
Cohesion: 0.09
Nodes (13): evaluate_batch_3(), evaluate_batch_4(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax(), mentions_tax(), _client_returning_fail(), _client_that_must_not_be_called() (+5 more)

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.17
Nodes (10): Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, api (osoba C), Endpointy (+2 more)

### Community 28 - "casedb_adapter.py"
Cohesion: 0.12
Nodes (24): analyzer_version(), _bodies(), case_to_document(), finding_to_ai_result(), _media_from_assets(), _parse_dt(), _segments(), _transcript_from_case() (+16 more)

### Community 29 - "meta_json.py"
Cohesion: 0.09
Nodes (35): doc_from_node(), Publisher, ad_id_from_url(), ad_text(), ad_title(), ads_from_graphql(), _cards(), clean_text() (+27 more)

### Community 30 - "RuntimeError"
Cohesion: 0.10
Nodes (26): AdvertiserRef, BBox, ChangeEvent, ChangeKind, ChangeSimilarity, Embedding, Engine, Entities (+18 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.07
Nodes (16): Source, SourceBlocked, SourceError, canonical_ad_url(), doc(), source(), test_deterministic_document_id(), test_discover_replay_yields_canonical_urls() (+8 more)

### Community 32 - "OllamaClient"
Cohesion: 0.15
Nodes (7): OllamaClient, TestPowtarzalnosciModelu, _real_client(), check_embeddings(), main(), make_doc(), main()

### Community 33 - "analyze"
Cohesion: 0.17
Nodes (8): analyze(), EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults, TestRegulyR4, TestWarstwyWektorowej

### Community 34 - "rules_hybrid.py"
Cohesion: 0.14
Nodes (10): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, FacebookConfig, blob_store_from_env() (+2 more)

### Community 35 - "re"
Cohesion: 0.11
Nodes (5): AdDocument, document_row(), PostgresStore, _row_to_document(), SqlStore

### Community 36 - "test_change_detect.py"
Cohesion: 0.26
Nodes (24): detect_change(), diff_rule_results(), ChangeKind, RiskLevel, _doc(), _finding(), _r(), test_brak_embeddingu_degraduje_do_simhasha_bez_wyjatku() (+16 more)

### Community 37 - "test_rules_det_fallback.py"
Cohesion: 0.26
Nodes (20): det_fallback_results(), _by(), _doc(), _node(), _run(), test_brak_probe_nic_nie_liczy(), test_brak_wezla_ryzyka_to_na_ze_wskazaniem_reguly_3(), test_facebook_nie_dostaje_fallbacku_typografia_meta() (+12 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.11
Nodes (10): TextNode, TranscriptSegment, assess_rule_3(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu (+2 more)

### Community 39 - "rules_hybrid.py"
Cohesion: 0.10
Nodes (13): _dominant_font_px(), _center_y(), _first_match_offset(), _matches(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline() (+5 more)

### Community 40 - "test_guards.py"
Cohesion: 0.16
Nodes (32): Verdict, mentions_historical_performance(), _res(), _run(), test_12a_jeden_rok_pass_zamieniony_na_fail(), test_12a_nie_zamienia_fail_na_pass(), test_12a_pelny_okres_zostaje_pass(), test_12b_pass_bez_walut_i_oplat_to_fail() (+24 more)

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.18
Nodes (3): ad_archive_id(), resolve_media_path(), TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.17
Nodes (14): AdvertiserRef, Embedding, Engine, Entities, EvidenceKind, InvestmentFirmRef, MediaItem, RegistryMatch (+6 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.09
Nodes (11): CircuitBreaker, NodeCache, RateLimiter, SeenSet, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures() (+3 more)

### Community 46 - "analyze"
Cohesion: 0.14
Nodes (6): analyze(), is_language(), language_factory(), make_clips(), DemoTests, segments()

### Community 47 - "store.py"
Cohesion: 0.16
Nodes (17): BBox, RenderProbe, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score() (+9 more)

### Community 48 - "guards.py"
Cohesion: 0.17
Nodes (14): normalize(), apply_guards(), _guard_rule_12a(), _guard_rule_12b(), _guard_rule_14(), _guard_rule_16(), _guard_rule_17(), _guard_rule_2() (+6 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.19
Nodes (9): _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera(), _zla() (+1 more)

### Community 51 - "parametrize"
Cohesion: 0.09
Nodes (15): alert_payload(), AlertHub, coverage(), create_app(), get_document(), get_finding(), health(), list_findings() (+7 more)

### Community 52 - "scaling.py"
Cohesion: 0.11
Nodes (13): Zadanie 2: Funkcja decyzyjna autoskalera, _connection(), _int(), make_valkey_state_provider(), _parse(), QueuePolicy, _rq_backlog_reader(), _read() (+5 more)

### Community 53 - "feed_fold_evidence"
Cohesion: 0.19
Nodes (12): feed_fold_evidence(), platform_rule_override(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched(), test_quote_is_not_cut_at_abbreviation() (+4 more)

### Community 54 - "stt.py"
Cohesion: 0.09
Nodes (6): _first_match_start(), normalize_text(), TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZaleznosci, TestZgodnosciKolejkiMiedzySerwisami

### Community 55 - "test_partial_guard.py"
Cohesion: 0.35
Nodes (9): _doc(), _rule(), _run(), test_partial_fail_braku_staje_sie_na(), test_partial_fail_obecnosci_zostaje(), test_partial_regula_10_i_pass_bez_zmian(), test_pelna_transkrypcja_bez_zmian(), test_reguly_brakujacego_zastrzezenia_sa_degradowane() (+1 more)

### Community 56 - "test_pool.py"
Cohesion: 0.12
Nodes (15): Zadanie 4: Executor `pool`, DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne() (+7 more)

### Community 57 - "pytest"
Cohesion: 0.22
Nodes (12): Zadanie 1: Konfiguracja skalowania i jej walidacja, load_scaling_config(), ScalingConfigError, test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(), test_domyslny_plik_sie_wczytuje(), test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(), test_min_wieksze_od_max_jest_odrzucane(), test_nieznany_executor_jest_odrzucany() (+4 more)

### Community 58 - "eval_rules.py"
Cohesion: 0.14
Nodes (14): Case, compute_metrics(), _entities(), FakeClient, format_table(), _is_placeholder(), load_cases(), main() (+6 more)

### Community 59 - "QueueState"
Cohesion: 0.21
Nodes (17): Zadanie 3: Endpoint `/scaling`, decide(), QueueState, scaling_payload(), test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie() (+9 more)

### Community 60 - "AdDocument"
Cohesion: 0.12
Nodes (8): AdDocument, MediaItem, make_local_transcriber(), test_analyzable_text_zawiera_transkrypcje(), test_tempo_segmentu_transkryptu_jest_liczone(), test_real_speech_to_rule_3(), TestKorpusuNaTejMaszynie, main()

### Community 61 - "AnalyzerConfig"
Cohesion: 0.13
Nodes (8): AnalyzerConfig, _ensure_transcript(), _ensure_vector_representation(), _doc(), _fake_transcriber(), TestKolejnosciEtapow, TestWywolaniaTranskrypcji, licznik()

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.14
Nodes (9): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth (+1 more)

### Community 63 - "test_facebook_rules.py"
Cohesion: 0.16
Nodes (9): Finding, main(), seed(), finding_row(), _iso(), open_store(), SqliteStore, UpsertResult (+1 more)

### Community 64 - "health.py"
Cohesion: 0.22
Nodes (3): _Handler, _no_states(), _scaling_response()

### Community 65 - "default_config"
Cohesion: 0.18
Nodes (9): add_asset(), Asset, Case, claim(), save_ai_result(), save_case(), set_columns(), set_status() (+1 more)

### Community 66 - "test_demo.py"
Cohesion: 0.20
Nodes (7): from_ad_document(), from_youtube(), youtube_video_id(), case_id_for(), Content, test_facebook_mapping_keeps_document_id_and_drops_embedding(), test_youtube_mapping_is_stable()

### Community 67 - "AGENTS.md - services/casedb"
Cohesion: 0.14
Nodes (13): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+5 more)

### Community 68 - "json"
Cohesion: 0.14
Nodes (10): test_przyklad_waliduje_sie_przeciw_modelowi(), test_rule_result_ma_dowod_dla_kazdego_werdyktu(), main(), load_case(), main(), print_table(), score_one(), update_gold() (+2 more)

### Community 69 - "services"
Cohesion: 0.18
Nodes (10): name, name, networks, investwatch, image, networks, ports, volumes (+2 more)

### Community 70 - "analyzer"
Cohesion: 0.29
Nodes (7): depends_on, depends_on, depends_on, postgres, valkey, condition, condition

### Community 71 - "export.py"
Cohesion: 0.20
Nodes (4): coverage(), failed_rules(), TestCoverage, TestFailedRules

### Community 72 - "scraper: FacebookAdsSource (Meta Ad Library)"
Cohesion: 0.20
Nodes (6): `.env`, Korpus demo (nagrać wieczorem przed demo), Quick start, scraper: FacebookAdsSource (Meta Ad Library), start_background(), Demo INVESTWATCH

### Community 73 - "test_idempotency_gate.py"
Cohesion: 0.14
Nodes (12): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba (+4 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 78 - "test_pipeline.py"
Cohesion: 0.16
Nodes (9): Zadanie 6: Klasyfikacja zdarzenia, embed_document_text(), hamming_distance(), is_near_duplicate_simhash(), normalize(), simhash(), tokenize(), TestNormalizacjaITokeny (+1 more)

### Community 79 - "test_pipeline.py"
Cohesion: 0.40
Nodes (7): Evidence, RuleResult, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.33
Nodes (5): collect_ads_from_dom(), merge_nodes(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.29
Nodes (6): CZĘŚĆ A — Autoskaler, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach)

### Community 82 - "casedb"
Cohesion: 0.13
Nodes (16): build, build, environment, networks, ports, volumes, context, build (+8 more)

### Community 83 - "ingest.py"
Cohesion: 0.46
Nodes (4): export_cases(), find_case_ids(), _plain(), _row()

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.25
Nodes (8): env_file, environment, extra_hosts, networks, API_BASE_URL, OLLAMA_BASE_URL, VALKEY_URL, analyzer

### Community 86 - "LocalBlobStore"
Cohesion: 0.13
Nodes (6): _default_spawn(), download_direct(), download_ytdlp(), probe_duration(), main(), LocalBlobStore

### Community 87 - "test_eval_rules.py"
Cohesion: 0.23
Nodes (6): _row(), test_kolejnosc_regul_numeryczna(), test_metryki_macierz_pomylek(), test_pending_nie_wchodzi_do_macierzy(), test_tabela_zawiera_reguly(), test_walidacja_odrzuca_nieznana_regule()

### Community 88 - "casedb"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 89 - "test_preconditions.py"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.23
Nodes (19): assess_rule_13(), _na(), _result(), rule_13_runner(), _doc(), _node(), test_brak_wynikow_historycznych_to_not_applicable(), test_cytat_to_doslowny_tekst_wezla() (+11 more)

### Community 92 - "_doc"
Cohesion: 0.17
Nodes (6): _load(), main(), _write(), connect(), migrate(), conn()

### Community 93 - "test_api.py"
Cohesion: 0.20
Nodes (18): client(), load(), seeded(), test_calibration_serves_gold_set(), test_document_roundtrip_is_lossless(), test_document_upsert_returns_200_second_time(), test_embedding_survives_roundtrip(), test_finding_for_unknown_document_409() (+10 more)

### Community 95 - "batching.py"
Cohesion: 0.15
Nodes (6): candidates(), metadata(), QuietLogger, run(), worker(), ydl_options()

### Community 96 - "health_payload"
Cohesion: 0.28
Nodes (3): _load_analyzer(), test_fixtures_validate(), test_schema_identical_with_analyzer()

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.40
Nodes (5): web, build, depends_on, networks, ports

### Community 99 - "demo.py"
Cohesion: 0.15
Nodes (13): 6. Do udoskonalenia — uszeregowane po wpływie na demo, evidence(), find_targets(), host(), load_inputs(), main(), normalize(), save() (+5 more)

### Community 100 - "ApiClient"
Cohesion: 0.18
Nodes (4): AdDocument, Finding, Scope, test_contract_copy_matches_analyzer()

### Community 101 - ".test_search_deduplicates_ids_and_respects_candidate_limit"
Cohesion: 0.20
Nodes (7): A — scraper + reguły DET, B — analyzer, C — api + web, Podział roli, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle), Rule

### Community 102 - "casedb_batch.py"
Cohesion: 0.19
Nodes (8): _fake_llm(), test_tryb_plikowy_z_fake_llm(), failing(), main(), make_analyzer(), analyze_case(), run_file(), summarize()

### Community 103 - "test_casedb_bridge.py"
Cohesion: 0.07
Nodes (17): claim(), connect(), fetch_case(), _jsonb(), _plain(), process_cases(), save_ai_result(), set_status() (+9 more)

### Community 105 - "BaseModel"
Cohesion: 0.18
Nodes (9): AGENTS.md - services/casedb, Dla modulu jobow (nastepny krok), Gdzie co jest, Kontrakt (nie zmieniaj bez uzgodnienia), Rola, Stan weryfikacji (2026-11-21, Claude), Zasady repo, add_column() (+1 more)

### Community 107 - "batching.py"
Cohesion: 0.17
Nodes (7): _all_not_applicable(), _build_result(), evaluate_batch(), _normalize_for_match(), _not_applicable(), quote_is_verifiable(), TestQuoteIsVerifiable

### Community 114 - "parse_args"
Cohesion: 0.15
Nodes (6): serve(), main(), parse_args(), _start_health_server(), run(), TestFlagiKolejkiWWorkerze

### Community 115 - "default_config"
Cohesion: 0.12
Nodes (13): default_config(), analyzer — Moduł 2 (analiza AI), Brama zakresu, Konfiguracja, Mapa plików, Quick Start, Uruchomienie, Weryfikacja cytatu (+5 more)

### Community 116 - "change_detect.py"
Cohesion: 0.15
Nodes (11): _basis(), event(), detect_disappeared(), _have_embeddings(), _new_event(), _rule_phrase(), _simhash_int(), _transitions() (+3 more)

### Community 117 - "AnalyzerConfig"
Cohesion: 0.29
Nodes (6): casedb, Instrukcja krok po kroku (dla czlowieka, Windows), Konfiguracja, Quick Start, Testy, Wymagania

### Community 118 - "._api"
Cohesion: 0.40
Nodes (5): 10. Pozyskiwanie danych i bezpieczeństwo demo, Bezpieczeństwo demo (anty-cel: „demo zależne od wifi"), Cybersec (kryterium oceniane wprost), Kolejka i harmonogram, Pluginowalne źródła

### Community 119 - "RuleRunner"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 120 - "make_tts_fixture.ps1"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 121 - "test_idempotency_gate.py"
Cohesion: 0.23
Nodes (12): CZĘŚĆ B — Detektor zmian, Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), simhash_hex(), _doc(), test_brak_simhasha_nie_wywraca_bramy() (+4 more)

### Community 122 - "migrations/__init__.py"
Cohesion: 0.50
Nodes (4): 4. Rozważone podejścia, Podejście A — „wszystko do LLM-a", Podejście B — „wszystko na regułach deterministycznych", Podejście C — hybryda warstwowa **[WYBRANE]**

### Community 123 - "6. Kontrakty danych (ZAMROŻONE o 12:30)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### Community 124 - "gen_facebook_examples.py"
Cohesion: 0.50
Nodes (4): volumes, pgdata, seaweeddata, valkeydata

### Community 130 - "Zbior regresyjny Modulu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Korekty niespojnosci danych (nie dopasowanie do wyniku), Pliki, Uzycie, Zasada etykietowania (wazne dla uczciwosci metryk), Zbior regresyjny Modulu 2 (SYNTETYCZNY)

### Community 131 - "registry.py"
Cohesion: 0.13
Nodes (7): rule_3_runner(), expected_rule_ids(), _merge_meta(), _rule_sort_key(), _with_hybrid(), test_expected_nie_zawiera_regul_spoza_naszych(), test_kolizja_podnosi_blad()

### Community 132 - "gen_facebook_examples.py"
Cohesion: 0.18
Nodes (8): ads_from_html(), test_host_replaced_path_and_params_kept(), test_uppercase_scheme_and_s3_untouched(), test_urls_inside_text_and_nested_structures(), test_ads_from_html_reads_inline_script(), main(), pick_ad(), sanitize()

### Community 133 - "_rule_6"
Cohesion: 0.33
Nodes (9): _evidence(), _na(), _result(), _risk_hits(), _rule_4(), _rule_5(), _rule_6(), _rule_7() (+1 more)

### Community 134 - "cosine"
Cohesion: 0.27
Nodes (3): _cosine(), cosine(), TestCosine

### Community 135 - "best_threshold"
Cohesion: 0.24
Nodes (3): TestBestThreshold, TestPustyZbior, best_threshold()

### Community 136 - "load_gold"
Cohesion: 0.29
Nodes (3): TestLoadGold, load_gold(), _ostrzez()

### Community 141 - "2. Cele, nie-cele, anty-cele"
Cohesion: 0.50
Nodes (4): 2. Cele, nie-cele, anty-cele, Anty-cele (to by oznaczało porażkę, nawet gdyby „działało"), Cele (musi być), Nie-cele (świadomie pomijamy)

### Community 142 - "T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)"
Cohesion: 0.50
Nodes (4): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)

### Community 144 - "Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY), Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości

### Community 145 - "Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)"
Cohesion: 0.29
Nodes (6): Cel, Format i uruchomienie, Liczba etykiet per reguła, Przypadki graniczne w etykietowaniu, Zasady uczciwości, Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)

### Community 146 - "Drabinka cięcia zakresu"
Cohesion: 0.67
Nodes (3): Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, Warstwa nietykalna — tego nie ścinamy nigdy

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 897 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `registry.py`, `gen_facebook_examples.py`, `test_worker.py`, `cosine`, `_rule_6`, `evaluate_batch_1`, `TestInterfejsRule`, `analyzer/contracts.py`, `Verdict`, `re`, `_client`, `RuleResult`, `AdDocument`, `test_casedb_bridge.py`, `casedb_adapter.py`, `meta_json.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_hybrid.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `store.py`, `stt.py`, `test_partial_guard.py`, `eval_rules.py`, `AnalyzerConfig`, `json`, `test_lang_consistency.py`, `test_pipeline.py`, `test_pipeline.py`, `test_rule_13.py`, `TestGranicyKontraktu`, `.test_search_deduplicates_ids_and_respects_candidate_limit`, `batching.py`, `change_detect.py`, `test_idempotency_gate.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 163 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 163 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Why does `Verdict` connect `test_guards.py` to `test_registry.py`, `_rule_6`, `risk_score`, `max_breach_severity`, `TestInterfejsRule`, `evaluate_batch_1`, `analyzer/contracts.py`, `Verdict`, `re`, `_client`, `RuleResult`, `AdDocument`, `test_casedb_bridge.py`, `OllamaClient`, `analyze`, `test_change_detect.py`, `test_rules_det_fallback.py`, `assess_rule_3`, `rules_hybrid.py`, `store.py`, `guards.py`, `test_partial_guard.py`, `eval_rules.py`, `AdDocument`, `json`, `export.py`, `test_lang_consistency.py`, `test_pipeline.py`, `test_pipeline.py`, `test_rule_13.py`, `casedb_batch.py`, `batching.py`, `change_detect.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 68 inferred relationships involving `AdDocument` (e.g. with `ApiClient` and `_cosine()`) actually correct?**
  _`AdDocument` has 68 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_worker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055288461538461536 - nodes in this community are weakly interconnected._