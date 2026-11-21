# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 127 files · ~1,107,649 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: .gz 8, (none) 5, .example 2)

## Summary
- 2086 nodes · 5294 edges · 140 communities (103 shown, 37 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 515 edges (avg confidence: 0.92)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `e8c7c296`
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
- test_scaling_runtime.py
- test_scaling_runtime.py
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- test_contracts.py
- AdDocument
- facebook.py
- Integracja serwisów — kto wywołuje kogo
- LocalBlobStore
- meta_json.py
- stt.py
- test_facebook_contract.py
- OllamaClient
- analyze
- jobs.py
- re
- Verdict
- AdDocument
- assess_rule_3
- test_rules_hybrid.py
- assess_rule_10
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
- ScalingConfig
- feed_fold_evidence
- InvestWatch — stan projektu
- max_breach_severity
- test_pool.py
- pytest
- TestPowtarzalnosciModelu
- QueueState
- test_scoring.py
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
- worker.py
- facebook_rules.py
- collect_ads_from_dom
- Harmonogram Modułu 1 — plan implementacji
- api
- change_detect.py
- Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)
- environment
- _default_spawn
- knn_score
- test_gen_examples.py
- Zbior zloty (gold set)
- seaweedfs
- test_rule_13.py
- re
- test_det_placeholders.py
- TestGranicyKontraktu
- QuietLogger
- nginx
- valkey
- web
- json
- ApiClient
- analyze
- TranscriptSegment
- FeedFoldEvidence
- _fake_transcriber
- ._api
- sys
- TestWywolaniaTranskrypcji
- classify_similarity
- main
- detect_language
- conftest.py
- analyzer — Moduły Analityczne / AI
- 10. Pozyskiwanie danych i bezpieczeństwo demo
- 8. Logika modułów
- 9. Scoring, threshold i metryki
- pytest
- 2. Cele, nie-cele, anty-cele
- 4. Rozważone podejścia
- T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)
- T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)
- TestZaleznosci
- test_worker_imports_without_rq

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 100 edges
2. `Verdict` - 99 edges
3. `RuleResult` - 79 edges
4. `analyze()` - 57 edges
5. `OllamaClient` - 54 edges
6. `FacebookAdsSource` - 48 edges
7. `AnalyzerConfig` - 43 edges
8. `EntityResolution` - 41 edges
9. `Evidence` - 38 edges
10. `Engine` - 36 edges

## Surprising Connections (you probably didn't know these)
- `6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `6.2 `RenderProbe` — geometria renderu, podstawa reguł DET` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Jak wagi jury przekładają się na decyzje projektowe` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `Podejście C — hybryda warstwowa **[WYBRANE]**` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-design.md → services/analyzer/analyzer/contracts.py
- `A — scraper + reguły DET` --references--> `RenderProbe`  [INFERRED]
  docs/superpowers/specs/2026-11-21-investwatch-plan-24h.md → services/analyzer/analyzer/contracts.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (140 total, 37 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "test_registry.py"
Cohesion: 0.11
Nodes (18): rule_3_runner(), build_config(), coverage_report(), expected_rule_ids(), module2_runners(), _rule_sort_key(), _with_hybrid(), _all_pass_handler() (+10 more)

### Community 4 - "test_stt.py"
Cohesion: 0.20
Nodes (20): Transcript, rate_anomaly(), risk_timing(), RiskTiming, test_rate_anomaly_fast_disclaimer(), test_rate_anomaly_single_segment(), test_rate_anomaly_too_few_segments(), test_rate_anomaly_zero_median() (+12 more)

### Community 5 - "test_worker.py"
Cohesion: 0.22
Nodes (16): handle_job(), _api(), _api_no_get(), test_api_error_on_get_returns_none(), test_api_error_on_post_returns_none(), test_findings_out_dir_zapisuje_json_nawet_gdy_api_pada(), test_flat_payload_z_det_results(), test_get_document_raises_api_error() (+8 more)

### Community 6 - "Relation"
Cohesion: 0.13
Nodes (10): Relation, Routing, route(), RoutingDecision, RoutingInput, _inp(), TestR1WlasnyMaterialFirmy, TestR2PodmiotTrzeci (+2 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.05
Nodes (24): is_flagged(), TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic (+16 more)

### Community 8 - "embeddings.py"
Cohesion: 0.14
Nodes (8): Zadanie 6: Klasyfikacja zdarzenia, hamming_distance(), is_near_duplicate_simhash(), normalize(), simhash(), tokenize(), TestNormalizacjaITokeny, TestSimhash

### Community 9 - "risk_score"
Cohesion: 0.14
Nodes (7): risk_level(), risk_score(), Weryfikacja cytatu — zabezpieczenie przed halucynacją, _rule(), TestEskalacjiPoNajciezszymNaruszeniu, TestNotApplicableNieWchodziDoMianownika, TestRiskScore

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.20
Nodes (9): 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 5. Architektura, 7. Mapowanie 18 reguł na silniki, InvestWatch — dokument projektowy (design doc) (+1 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.13
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

### Community 15 - "contracts.py"
Cohesion: 0.13
Nodes (11): AdvertiserRef, Embedding, Engine, Entities, EvidenceKind, InvestmentFirmRef, Publisher, RegistryMatch (+3 more)

### Community 16 - "Verdict"
Cohesion: 0.11
Nodes (22): advisory_signals(), assess_shadow_advisory(), mentions_financial_instrument(), _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable, _boom(), _client() (+14 more)

### Community 18 - "test_scaling_runtime.py"
Cohesion: 0.11
Nodes (9): _connection(), read_queue_states(), _rq_backlog_reader(), _read(), _rq_worker_counter(), _count(), TestDostawcyStanu, TestOdczytuStanuKolejek (+1 more)

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.11
Nodes (17): B — analyzer, C — api + web, Co zmieniło się po review zespołu (wersja 2), Drabinka cięcia zakresu, Drabinka — ścinamy od dołu, InvestWatch — plan wykonawczy 23 h, Jedna rzecz na każdy gate, Rejestr ryzyk (+9 more)

### Community 21 - "rules"
Cohesion: 0.07
Nodes (29): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, dominance_ratio, legal_basis, legal_basis, max_distance_px (+21 more)

### Community 22 - "test_contracts.py"
Cohesion: 0.09
Nodes (13): Układ repozytorium, A — scraper + reguły DET, Podział roli, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min), Evidence, RenderProbe, Rule, RuleBase (+5 more)

### Community 23 - "AdDocument"
Cohesion: 0.18
Nodes (4): _doc(), _rule(), _runner(), TestAnalyze

### Community 25 - "facebook.py"
Cohesion: 0.10
Nodes (4): AdDocument, download_direct(), Source, BlobStore

### Community 26 - "Integracja serwisów — kto wywołuje kogo"
Cohesion: 0.29
Nodes (6): Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem

### Community 28 - "LocalBlobStore"
Cohesion: 0.15
Nodes (9): main(), FacebookConfig, ads_from_html(), LocalBlobStore, source(), doc(), test_ads_from_html_reads_inline_script(), main() (+1 more)

### Community 29 - "meta_json.py"
Cohesion: 0.10
Nodes (31): doc_from_node(), ad_text(), ad_title(), ads_from_graphql(), _cards(), clean_text(), find_ad_nodes(), _first() (+23 more)

### Community 30 - "stt.py"
Cohesion: 0.15
Nodes (12): _default_transcriber(), run(), SttError, transcribe(), test_stt_error_is_runtime_error(), test_transcribe_empty_result(), test_transcribe_passes_through_stt_error(), boom() (+4 more)

### Community 31 - "test_facebook_contract.py"
Cohesion: 0.11
Nodes (11): ad_id_from_url(), canonical_ad_url(), doc(), test_deterministic_document_id(), test_identity_and_url(), test_login_redirect_blocked_and_overlays_removed_without_clicks(), test_non_dco_ad_without_testid_is_scoped_from_sponsored_label(), test_replay_without_fixture_is_a_source_error() (+3 more)

### Community 32 - "OllamaClient"
Cohesion: 0.06
Nodes (17): embed_document_text(), LlmError, OllamaClient, evaluate_batch_4(), TestEmbedDocumentText, handler(), _client_returning_fail(), _client_that_must_not_be_called() (+9 more)

### Community 33 - "analyze"
Cohesion: 0.16
Nodes (8): AnalyzerConfig, EntityResolution, _det(), _doc(), TestBramyZakresuNaRealnejReklamie, TestPrzeplywuDetResults, TestRegulyR4, TestWarstwyWektorowej

### Community 34 - "jobs.py"
Cohesion: 0.19
Nodes (8): build_facebook_source(), discover_job(), fetch_job(), _redis(), schedule_facebook(), Jak to działa, blob_store_from_env(), S3BlobStore

### Community 35 - "re"
Cohesion: 0.27
Nodes (12): check_external_hosts(), check_forbidden_deps(), check_forbidden_patterns(), check_pinned_versions(), check_secrets(), _host_allowed(), is_allowlisted_file(), _lines() (+4 more)

### Community 36 - "Verdict"
Cohesion: 0.34
Nodes (23): detect_change(), ChangeKind, RiskLevel, Verdict, _doc(), _finding(), _r(), test_brak_embeddingu_degraduje_do_simhasha_bez_wyjatku() (+15 more)

### Community 37 - "AdDocument"
Cohesion: 0.12
Nodes (14): AdDocument, RuleResult, load_prompt(), _na(), _result(), evaluate_batch_2(), evaluate_batch_3(), _all_not_applicable() (+6 more)

### Community 38 - "assess_rule_3"
Cohesion: 0.11
Nodes (9): assess_rule_3(), _result(), _doc(), _node(), TestOsiCzasu, TestOsiGeometrii, TestOsiTekstu, TestProporcjonalnosciCzcionki (+1 more)

### Community 39 - "test_rules_hybrid.py"
Cohesion: 0.14
Nodes (8): _center_y(), measure_geometry(), measure_proximity(), measure_text(), measure_timeline(), _pick_viewport(), Proximity, TestWyboruOsi

### Community 40 - "assess_rule_10"
Cohesion: 0.24
Nodes (4): assess_rule_10(), _result(), split_sentences(), TestAssessRule10

### Community 41 - "FacebookAdsSource"
Cohesion: 0.13
Nodes (5): MediaItem, SourceBlocked, SourceError, FacebookAdsSource, test_discover_replay_yields_canonical_urls()

### Community 42 - "test_stt_pipeline.py"
Cohesion: 0.14
Nodes (7): ad_archive_id(), make_local_transcriber(), _transcribe(), resolve_media_path(), _doc(), TestKorpusuNaTejMaszynie, TestResolveraPlikow

### Community 43 - "test_render_probe.py"
Cohesion: 0.14
Nodes (15): NavigationGuard, neutralize_overlays(), run_probe(), _node(), page(), test_background_alpha_composition_and_assumed_canvas(), test_clipped_by_ellipsis(), test_collapsed_signals() (+7 more)

### Community 44 - "scraper/contracts.py"
Cohesion: 0.14
Nodes (15): AdvertiserRef, Embedding, Entities, Finding, InvestmentFirmRef, MediaItem, Publisher, RegistryMatch (+7 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.09
Nodes (11): CircuitBreaker, NodeCache, RateLimiter, SeenSet, test_auto_mode_falls_back_to_fixture_when_breaker_open(), FakeClock, test_breaker_opens_after_threshold_and_closes_after_cooldown(), test_breaker_window_forgets_old_failures() (+3 more)

### Community 46 - "DemoTests"
Cohesion: 0.14
Nodes (6): analyze(), is_language(), language_factory(), make_clips(), DemoTests, segments()

### Community 47 - "test_facebook_rules.py"
Cohesion: 0.18
Nodes (16): BBox, TextNode, ViewportProbe, facebook_det_results(), _doc(), _node(), score(), test_not_applicable_rules_stay_out_of_score_denominator() (+8 more)

### Community 48 - "demo.py"
Cohesion: 0.16
Nodes (11): candidates(), evidence(), find_targets(), host(), metadata(), normalize(), run(), signals_in() (+3 more)

### Community 49 - "gpu"
Cohesion: 0.10
Nodes (20): max, min, scale_down_idle_s, scale_up_backlog, max, min, scale_down_idle_s, scale_up_backlog (+12 more)

### Community 50 - "test_scaling_endpoint.py"
Cohesion: 0.15
Nodes (13): scaling_payload(), _get(), _przywroc_provider(), test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(), test_domyslny_provider_daje_pusta_liste(), test_endpoint_scaling_zwraca_200_i_json(), test_health_dalej_dziala(), test_niepoprawna_konfiguracja_nie_wywala_handlera() (+5 more)

### Community 51 - "parametrize"
Cohesion: 0.12
Nodes (6): _first_match_start(), normalize_text(), TestFleksjiWRouterze, TestWzorcowOsiCzasu, TestZgodnosciKolejkiMiedzySerwisami, test_normalize_strips_diacritics()

### Community 52 - "ScalingConfig"
Cohesion: 0.24
Nodes (8): CZĘŚĆ A — Autoskaler, Zadanie 1: Konfiguracja skalowania i jej walidacja, Zadanie 2: Funkcja decyzyjna autoskalera, Zadanie 3: Endpoint `/scaling`, Zadanie 4: Executor `pool`, make_valkey_state_provider(), _provider(), ScalingConfig

### Community 53 - "feed_fold_evidence"
Cohesion: 0.18
Nodes (13): feed_fold_evidence(), platform_rule_override(), test_feed_fold_hybrid_evidence_from_document_text(), test_bez_ryzyka_is_a_promise_not_a_warning(), test_cfd_retail_loss_disclosure_detected(), test_english_and_cfd_style_warnings(), test_no_warning_returns_none(), test_other_rules_and_sources_untouched() (+5 more)

### Community 54 - "InvestWatch — stan projektu"
Cohesion: 0.12
Nodes (16): 1. Co działa i jest zweryfikowane, 2. Pomiary na żywym modelu, 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego, 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu, 5. Do zrobienia, 6. Do udoskonalenia — uszeregowane po wpływie na demo, 7. Znane ograniczenia — mówimy je wprost, 8. Mapa odpowiedzialności za reguły (+8 more)

### Community 56 - "test_pool.py"
Cohesion: 0.12
Nodes (14): DryRunExecutor, PoolExecutor, ScalingDecision, _d(), FakeSpawn, FakeWorker, test_apply_jest_idempotentne(), test_apply_startuje_brakujace_workery() (+6 more)

### Community 57 - "pytest"
Cohesion: 0.15
Nodes (16): _int(), load_scaling_config(), _parse(), QueuePolicy, ScalingConfigError, _ShapeError, validate_scaling_config(), test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku() (+8 more)

### Community 59 - "QueueState"
Cohesion: 0.30
Nodes (12): decide(), QueueState, test_backlog_powyzej_progu_zwieksza_o_jeden(), test_brak_backlogu_nie_zmienia_liczby_workerow(), test_gpu_nie_przekracza_liczby_endpointow(), test_limit_globalny_przycina_deterministycznie(), test_limit_globalny_zdejmuje_z_kolejki_o_najmniejszym_backlogu(), test_nie_schodzi_ponizej_min_ani_nie_rosnie_powyzej_max() (+4 more)

### Community 60 - "test_scoring.py"
Cohesion: 0.18
Nodes (6): coverage(), failed_rules(), Co już jest (gotowe i przetestowane), TestCoverage, TestFailedRules, TestRiskLevel

### Community 61 - "test_idempotency_gate.py"
Cohesion: 0.31
Nodes (10): Zadanie 7: Brama idempotencji przed kolejką GPU, GateDecision, should_analyze(), simhash_hex(), _doc(), test_brak_simhasha_nie_wywraca_bramy(), test_identyczny_material_nie_idzie_na_gpu(), test_pierwsze_zetkniecie_zawsze_analizujemy() (+2 more)

### Community 62 - "infra - punkt startowy dla Osoby C (API + dashboard)"
Cohesion: 0.15
Nodes (8): Budowanie na kontrakcie bez uruchamiania analizy, Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione), infra - punkt startowy dla Osoby C (API + dashboard), Metryki do panelu, Ollama, Szybki start: same bazy, Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać), TestPortHealth

### Community 63 - "router.py"
Cohesion: 0.21
Nodes (6): _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _matches_any(), TestHasProfitClaims

### Community 64 - "health.py"
Cohesion: 0.13
Nodes (8): _Handler, health_payload(), _no_states(), _scaling_response(), handler(), _llm(), test_health_ollama_down_is_degraded_not_fatal(), test_health_ollama_up()

### Community 65 - "cosine"
Cohesion: 0.27
Nodes (3): _cosine(), cosine(), TestCosine

### Community 66 - "TranscriptSegment"
Cohesion: 0.36
Nodes (4): TranscriptSegment, speech_rate(), test_speech_rate_basic(), test_speech_rate_zero_duration_no_crash()

### Community 67 - "Harmonogram i orkiestracja — dokument projektowy"
Cohesion: 0.14
Nodes (14): 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia), 11. Kolejność wdrożenia, 12. Ryzyka, 1. Co wymaga specyfikacja, 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian, 3. Architektura, 4. Deklaratywny harmonogram, 5. Typy zdarzeń (+6 more)

### Community 68 - "json"
Cohesion: 0.33
Nodes (5): load_case(), main(), print_table(), score_one(), update_gold()

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
Nodes (9): 6.1 `AdDocument` — to, co produkuje scraper, 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść, 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, 6.3 `RuleResult` — wynik jednej reguły, 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów, 6.5 Potok przetwarzania i ROUTER modułów, 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin", 6. Kontrakty danych (ZAMROŻONE o 12:30) (+1 more)

### Community 74 - "healthcheck"
Cohesion: 0.47
Nodes (9): healthcheck, interval, retries, start_period, test, timeout, healthcheck, healthcheck (+1 more)

### Community 75 - "postgres"
Cohesion: 0.22
Nodes (9): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, environment, image, networks, ports, volumes (+1 more)

### Community 77 - "_client"
Cohesion: 0.39
Nodes (3): _client(), _doc(), TestOverrideWBatch2

### Community 78 - "worker.py"
Cohesion: 0.12
Nodes (5): Co A wrzuca do kolejki, analyze_document(), _build_det_results(), _build_resolution(), _save_finding()

### Community 79 - "facebook_rules.py"
Cohesion: 0.44
Nodes (6): Evidence, _platform(), _result(), _risk_nodes(), _rule6(), _rule7()

### Community 80 - "collect_ads_from_dom"
Cohesion: 0.33
Nodes (5): collect_ads_from_dom(), merge_nodes(), _serve(), test_gives_up_after_timeout_without_results(), test_waits_through_navigation_until_results_arrive()

### Community 81 - "Harmonogram Modułu 1 — plan implementacji"
Cohesion: 0.16
Nodes (11): CZĘŚĆ B — Detektor zmian, Global Constraints, Harmonogram Modułu 1 — plan implementacji, Poza zakresem tego planu — świadomie, z powodem, Review Focus, Weryfikacja końcowa (po obu częściach), Zadanie 5: Kontrakt `ChangeEvent` i diff reguł, diff_rule_results() (+3 more)

### Community 82 - "api"
Cohesion: 0.25
Nodes (8): build, build, networks, ports, profiles, context, api, build

### Community 83 - "change_detect.py"
Cohesion: 0.18
Nodes (9): _basis(), event(), detect_disappeared(), _have_embeddings(), _new_event(), _rule_phrase(), _simhash_int(), ChangeSimilarity (+1 more)

### Community 84 - "Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)"
Cohesion: 0.29
Nodes (6): Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI), Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne), Osoba B (analyzer), Osoba C (API/UI), Otwarte, Pliki

### Community 85 - "environment"
Cohesion: 0.29
Nodes (7): environment, environment, API_BASE_URL, DATABASE_URL, OLLAMA_BASE_URL, S3_ENDPOINT, VALKEY_URL

### Community 87 - "knn_score"
Cohesion: 0.36
Nodes (3): 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba, knn_score(), TestKnnScore

### Community 88 - "test_gen_examples.py"
Cohesion: 0.27
Nodes (5): test_committed_examples_have_no_external_hosts(), test_host_replaced_path_and_params_kept(), test_uppercase_scheme_and_s3_untouched(), test_urls_inside_text_and_nested_structures(), sanitize()

### Community 89 - "Zbior zloty (gold set)"
Cohesion: 0.33
Nodes (5): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set)

### Community 90 - "seaweedfs"
Cohesion: 0.33
Nodes (6): command, image, networks, ports, volumes, seaweedfs

### Community 91 - "test_rule_13.py"
Cohesion: 0.16
Nodes (22): BBox, TextNode, ViewportProbe, assess_rule_13(), _na(), _result(), rule_13_runner(), _doc() (+14 more)

### Community 92 - "re"
Cohesion: 0.13
Nodes (11): normalize(), _first_match_offset(), _matches(), risk_sentences(), _words(), _matches_any(), mentions_forecast(), mentions_forecast_or_tax() (+3 more)

### Community 93 - "test_det_placeholders.py"
Cohesion: 0.23
Nodes (7): missing_det_placeholders(), _doc(), _res(), test_nie_dubluje_regul_ze_scrapera(), test_placeholdery_nie_zmieniaja_ryzyka_a_obnizaja_coverage(), test_powod_gdy_probe_jest_ale_brak_wyniku(), test_wszystkie_pieciu_gdy_brak_wynikow_i_probe()

### Community 96 - "nginx"
Cohesion: 0.40
Nodes (5): image, networks, ports, volumes, nginx

### Community 97 - "valkey"
Cohesion: 0.40
Nodes (5): valkey, image, networks, ports, volumes

### Community 98 - "web"
Cohesion: 0.40
Nodes (5): web, depends_on, networks, ports, profiles

### Community 99 - "json"
Cohesion: 0.20
Nodes (9): test_finding_moze_nalezec_do_wielu_modulow(), test_przyklad_waliduje_sie_przeciw_modelowi(), main(), test_document_matches_frozen_contract(), load_inputs(), main(), save(), scan() (+1 more)

### Community 100 - "ApiClient"
Cohesion: 0.21
Nodes (5): ApiClient, ApiError, _check_local(), _resolve_document(), test_external_base_url_rejected()

### Community 102 - "analyze"
Cohesion: 0.18
Nodes (4): analyze(), _crashed_rule_result(), _ensure_transcript(), _ensure_vector_representation()

### Community 117 - "_fake_transcriber"
Cohesion: 0.20
Nodes (3): _fake_transcriber(), TestKolejnosciEtapow, licznik()

### Community 122 - "main"
Cohesion: 0.33
Nodes (4): serve(), main(), _start_health_server(), run()

### Community 124 - "conftest.py"
Cohesion: 0.43
Nodes (3): browser(), chromium_available(), _launch()

### Community 125 - "analyzer — Moduły Analityczne / AI"
Cohesion: 0.33
Nodes (5): analyzer — Moduły Analityczne / AI, Brama zakresu — najważniejsza decyzja domenowa, Quick start, Regeneracja przykładów kontraktów, Zasady, których trzymamy się w tym serwisie

### Community 126 - "10. Pozyskiwanie danych i bezpieczeństwo demo"
Cohesion: 0.40
Nodes (5): 10. Pozyskiwanie danych i bezpieczeństwo demo, Bezpieczeństwo demo (anty-cel: „demo zależne od wifi"), Cybersec (kryterium oceniane wprost), Kolejka i harmonogram, Pluginowalne źródła

### Community 127 - "8. Logika modułów"
Cohesion: 0.40
Nodes (5): 8. Logika modułów, Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy), Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo, Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory), Speech-to-text (w MVP)

### Community 128 - "9. Scoring, threshold i metryki"
Cohesion: 0.40
Nodes (5): 9.1 Budżet VRAM i serializacja etapów GPU, 9. Scoring, threshold i metryki, Panel kalibracji — decyzja, która ratuje demo, Wzór, Zbiór złoty (gold set)

### Community 129 - "pytest"
Cohesion: 0.40
Nodes (3): _merge_meta(), test_kolizja_podnosi_blad(), test_transcribe_without_library_raises_stt_error()

### Community 130 - "2. Cele, nie-cele, anty-cele"
Cohesion: 0.50
Nodes (4): 2. Cele, nie-cele, anty-cele, Anty-cele (to by oznaczało porażkę, nawet gdyby „działało"), Cele (musi być), Nie-cele (świadomie pomijamy)

### Community 131 - "4. Rozważone podejścia"
Cohesion: 0.50
Nodes (4): 4. Rozważone podejścia, Podejście A — „wszystko do LLM-a", Podejście B — „wszystko na regułach deterministycznych", Podejście C — hybryda warstwowa **[WYBRANE]**

### Community 132 - "T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)"
Cohesion: 0.50
Nodes (4): A — scraper + reguły DET, B — analyzer, C — api + web, T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### Community 133 - "T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)"
Cohesion: 0.50
Nodes (4): A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, C — api + web, T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 708 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_registry.py`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `_client`, `test_contracts.py`, `AdDocument`, `facebook.py`, `LocalBlobStore`, `meta_json.py`, `stt.py`, `test_facebook_contract.py`, `OllamaClient`, `analyze`, `Verdict`, `assess_rule_3`, `test_rules_hybrid.py`, `FacebookAdsSource`, `test_stt_pipeline.py`, `test_facebook_rules.py`, `test_idempotency_gate.py`, `cosine`, `json`, `6. Kontrakty danych (ZAMROŻONE o 12:30)`, `_client`, `worker.py`, `facebook_rules.py`, `change_detect.py`, `test_rule_13.py`, `re`, `test_det_placeholders.py`, `json`, `ApiClient`, `analyze`, `_fake_transcriber`, `TestWywolaniaTranskrypcji`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AdDocument` (e.g. with `6.1 `AdDocument` — to, co produkuje scraper` and `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"`) actually correct?**
  _`AdDocument` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_registry.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Why does `RuleResult` connect `AdDocument` to `test_registry.py`, `T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)`, `test_evaluate.py`, `risk_score`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `test_contracts.py`, `AdDocument`, `OllamaClient`, `analyze`, `Verdict`, `assess_rule_3`, `assess_rule_10`, `test_facebook_rules.py`, `max_breach_severity`, `test_scoring.py`, `json`, `6. Kontrakty danych (ZAMROŻONE o 12:30)`, `worker.py`, `facebook_rules.py`, `Harmonogram Modułu 1 — plan implementacji`, `change_detect.py`, `test_rule_13.py`, `re`, `test_det_placeholders.py`, `analyze`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `Verdict` (e.g. with `detect_change()` and `_transitions()`) actually correct?**
  _`Verdict` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Should `Relation` be split into smaller, more focused modules?**
  _Cohesion score 0.12903225806451613 - nodes in this community are weakly interconnected._