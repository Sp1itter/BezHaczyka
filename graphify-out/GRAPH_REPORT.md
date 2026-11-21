# Graph Report - investwatch-plan  (2026-11-21)

## Corpus Check
- 58 files · ~47,046 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .log 1)

## Summary
- 884 nodes · 2206 edges · 28 communities (24 shown, 4 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 262 edges (avg confidence: 0.93)
- Token cost: 22,122 input · 2,098 output

## Graph Freshness
- Built from commit: `bacaaa5b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InvestWatch Platform Architecture
- Development Documentation and Skills
- AdDocument
- InvestWatch Challenge Description
- test_stt.py
- test_worker.py
- module3.py
- test_evaluate.py
- test_pipeline.py
- test_scoring.py
- InvestWatch — dokument projektowy (design doc)
- evaluate_batch_1
- classify_scope
- _file
- test_config.py
- contracts.py
- Verdict
- Rule
- analyze
- _client
- InvestWatch — plan wykonawczy 23 h
- rules
- test_contracts.py
- RuleResult
- EvidenceKind
- quote_is_verifiable
- TestInterfejsRule

## God Nodes (most connected - your core abstractions)
1. `AdDocument` - 51 edges
2. `RuleResult` - 50 edges
3. `Verdict` - 49 edges
4. `OllamaClient` - 45 edges
5. `analyze()` - 30 edges
6. `classify_scope()` - 28 edges
7. `ScopeStatus` - 25 edges
8. `EvidenceKind` - 24 edges
9. `evaluate_batch_1()` - 23 edges
10. `evaluate_batch()` - 23 edges

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

## Communities (28 total, 4 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.22
Nodes (9): InvestWatch Competition Regulations, Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System (+1 more)

### Community 2 - "AdDocument"
Cohesion: 0.06
Nodes (33): AdDocument, LlmError, load_prompt(), OllamaClient, evaluate_batch_2(), evaluate_batch_3(), evaluate_batch_4(), _all_not_applicable() (+25 more)

### Community 4 - "test_stt.py"
Cohesion: 0.06
Nodes (43): Transcript, TranscriptSegment, _default_transcriber(), run(), _first_match_start(), normalize_text(), rate_anomaly(), risk_timing() (+35 more)

### Community 5 - "test_worker.py"
Cohesion: 0.06
Nodes (35): Co A wrzuca do kolejki, Co analyzer zwraca do API, Dlaczego kolejka, a nie endpoint HTTP u analyzera, Dodatkowo u analyzera: `/health`, Integracja serwisów — kto wywołuje kogo, Kształt przepływu, Zasada wspólna: brak danych nie jest naruszeniem, ApiClient (+27 more)

### Community 6 - "module3.py"
Cohesion: 0.06
Nodes (30): normalize(), mentions_financial_instrument(), _has_any(), has_investment_recommendation(), has_profit_claims(), looks_like_advisory_business(), _normalize(), route() (+22 more)

### Community 7 - "test_evaluate.py"
Cohesion: 0.06
Nodes (22): TestBestThreshold, TestDzieleniePrzezZero, TestIdealnyKlasyfikator, TestKlasyfikatorLosowy, TestLoadGold, TestMacierzPomylek, TestNicNieNaruszaNic, TestPrzemiatanieProgow (+14 more)

### Community 8 - "test_pipeline.py"
Cohesion: 0.06
Nodes (16): classify_similarity(), cosine(), embed_document_text(), hamming_distance(), is_near_duplicate_simhash(), knn_score(), simhash(), simhash_hex() (+8 more)

### Community 9 - "test_scoring.py"
Cohesion: 0.08
Nodes (19): Co znaczy `is_violation`, Jak dodac pozycje, `rule_labels` (opcjonalne), Skad etykiety demo, Zbior zloty (gold set), RiskLevel, coverage(), failed_rules() (+11 more)

### Community 10 - "InvestWatch — dokument projektowy (design doc)"
Cohesion: 0.05
Nodes (41): 10. Pozyskiwanie danych i bezpieczeństwo demo, 11. Co zostaje do decyzji budującemu, 12. Definicja sukcesu, 1. Intencja i uzasadnienie, 2. Cele, nie-cele, anty-cele, 3.1 Licencje — twarde kryterium wdrożeniowe, 3. Ograniczenia narzucone z zewnątrz, 4. Rozważone podejścia (+33 more)

### Community 11 - "evaluate_batch_1"
Cohesion: 0.12
Nodes (7): evaluate_batch_1(), _client(), _doc(), _generate_handler(), handler(), TestEvaluateBatch1, TestOllamaClient

### Community 12 - "classify_scope"
Cohesion: 0.09
Nodes (9): ScopeStatus, classify_scope(), _find_any(), TestCfdNaKryptoZostajeWZakresie, TestFalszywePozytywy, TestNiepewneIdaDoTriage, TestPolskaOdmiana, TestPozaZakresemTylkoBezOpakowania (+1 more)

### Community 13 - "_file"
Cohesion: 0.13
Nodes (5): _file(), TestCalegoRepozytorium, TestMechanizmuWyjatkow, TestNieZglaszaFalszywychAlarmow, TestWylapujeNaruszenia

### Community 14 - "test_config.py"
Cohesion: 0.12
Nodes (17): _deep_merge(), get_threshold(), load_thresholds(), test_brakujace_klucze_uzupelniane_domyslnymi(), test_brakujacy_plik_zwraca_wartosci_domyslne(), test_domyslny_plik_jest_zgodny_z_fallbackiem(), _lisc(), test_get_threshold_domyslnie_none() (+9 more)

### Community 15 - "contracts.py"
Cohesion: 0.20
Nodes (13): AdvertiserRef, BBox, Embedding, Entities, InvestmentFirmRef, MediaItem, Publisher, RegistryMatch (+5 more)

### Community 16 - "Verdict"
Cohesion: 0.24
Nodes (20): Verdict, advisory_signals(), assess_shadow_advisory(), _na(), _result(), _boom(), _client(), wrapped() (+12 more)

### Community 17 - "Rule"
Cohesion: 0.11
Nodes (18): 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET, Układ repozytorium, A — scraper + reguły DET, B — analyzer, C — api + web, Co zmieniło się po review zespołu (wersja 2), Podział roli, T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min) (+10 more)

### Community 18 - "analyze"
Cohesion: 0.18
Nodes (6): analyze(), AnalyzerConfig, _doc(), _rule(), _runner(), TestAnalyze

### Community 19 - "_client"
Cohesion: 0.22
Nodes (9): _by_id(), _client(), _doc(), _ok(), handler(), test_evaluate_batch_generyczny_respektuje_fail_means_absence(), test_zmyslony_cytat_obniza_confidence(), TestBatch3BrakCytatuNieKaraDlaAbsencji (+1 more)

### Community 20 - "InvestWatch — plan wykonawczy 23 h"
Cohesion: 0.09
Nodes (21): A — scraper + reguły DET, A — scraper + warstwa podmiotowa Modułu 1, B — analyzer, B — analyzer, C — api + web, C — api + web, Drabinka cięcia zakresu, Drabinka — ścinamy od dołu (+13 more)

### Community 21 - "rules"
Cohesion: 0.09
Nodes (21): dedup, near_duplicate_cosine, same_campaign_cosine, simhash_max_distance, legal_basis, min_ratio, legal_basis, min_contrast (+13 more)

### Community 22 - "test_contracts.py"
Cohesion: 0.17
Nodes (7): test_analyzable_text_zawiera_transkrypcje(), test_cfd_na_krypto_jest_w_zakresie_w_przykladzie(), test_finding_moze_nalezec_do_wielu_modulow(), test_przyklad_waliduje_sie_przeciw_modelowi(), test_rule_result_ma_dowod_dla_kazdego_werdyktu(), test_tempo_segmentu_transkryptu_jest_liczone(), main()

### Community 23 - "RuleResult"
Cohesion: 0.32
Nodes (3): Evidence, RuleResult, RuleBase

### Community 24 - "EvidenceKind"
Cohesion: 0.24
Nodes (4): Engine, EvidenceKind, Relation, _crashed_rule_result()

### Community 25 - "quote_is_verifiable"
Cohesion: 0.27
Nodes (3): _normalize_for_match(), quote_is_verifiable(), TestQuoteIsVerifiable

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 278 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdDocument` connect `AdDocument` to `test_worker.py`, `module3.py`, `test_pipeline.py`, `InvestWatch — dokument projektowy (design doc)`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `Rule`, `analyze`, `_client`, `test_contracts.py`, `RuleResult`, `TestInterfejsRule`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `AdDocument` (e.g. with `6.1 `AdDocument` — to, co produkuje scraper` and `6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"`) actually correct?**
  _`AdDocument` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AdDocument` be split into smaller, more focused modules?**
  _Cohesion score 0.05828953655040611 - nodes in this community are weakly interconnected._
- **Why does `RuleResult` connect `RuleResult` to `AdDocument`, `module3.py`, `test_pipeline.py`, `test_scoring.py`, `InvestWatch — dokument projektowy (design doc)`, `evaluate_batch_1`, `contracts.py`, `Verdict`, `Rule`, `analyze`, `InvestWatch — plan wykonawczy 23 h`, `test_contracts.py`, `EvidenceKind`, `TestInterfejsRule`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `RuleResult` (e.g. with `6.3 `RuleResult` — wynik jednej reguły` and `Układ repozytorium`) actually correct?**
  _`RuleResult` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_stt.py` be split into smaller, more focused modules?**
  _Cohesion score 0.058596491228070174 - nodes in this community are weakly interconnected._