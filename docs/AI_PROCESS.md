# Proces budowy z asystentami AI

Dokument opisuje, jak zespół (3 osoby, każda z agentami Claude Code) zbudował InvestWatch.
Każde twierdzenie wskazuje plik lub commit w repozytorium. Tam, gdzie repozytorium czegoś
nie dokumentuje, napisano to wprost (sekcja 6).

## 1. Narzędzia

| Narzędzie | Rola | Ślad w repo |
|---|---|---|
| Claude Code | asystent kodujący, jeden na osobę zespołu | `.claude/CLAUDE.md`, `.claude/settings.json` |
| Plugin superpowers | proces: brainstorming, spec, plan, TDD, przegląd | struktura `docs/superpowers/{specs,plans}/` |
| graphify | graf wiedzy o kodzie; agent pyta graf przed czytaniem źródeł | `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`), `.claude/skills/graphify/` |
| Ollama + Bielik 4.5B v3.0 (Q8_0), bge-m3 | model produktu, uruchamiany lokalnie na GPU 8 GB | `docs/STAN-PROJEKTU.md` §2, `services/analyzer/analyzer/llm.py` |

Hooki w `.claude/settings.json` (`graphify hook-guard`, PreToolUse na Bash/Grep/Read/Glob)
wymuszają na agencie zapytanie do grafu, zanim przeszuka kod. Graf odświeżano po etapach
(m.in. commity `e37a40f`, `5324276`).

W produkcie nie ma płatnych ani zewnętrznych API modeli. Pilnuje tego automat
`tools/check_compliance.py` (sekcja 5). Narzędzia AI służyły do budowy kodu; model w produkcie
to wyłącznie Bielik i bge-m3 na maszynie lokalnej.

## 2. Proces: standard i pliki

Standard pochodzi z pluginu superpowers. Kolejne kroki mają odpowiedniki w repozytorium:

| Krok | Artefakt |
|---|---|
| Brainstorming i decyzje zakresu | `docs/superpowers/specs/2026-11-21-investwatch-design.md` (m.in. nie-cele i §6.6 brama zakresu) |
| Spec (design doc) | te same specyfikacje oraz `docs/superpowers/specs/2026-11-22-harmonogram-design.md`; wersja 2 po review zespołu: commit `80031fb` |
| Plan z etapami | `docs/superpowers/plans/` (5 planów: harmonogram, infra docker, domknięcie Modułu 1, finalizacja panelu, sprint finałowy z etapami A/B/C) |
| Implementacja z testami | testy obok kodu: `services/analyzer/tests/` (41 plików), `services/api/tests/`, testy scrapera i dashboardu; plany podają polecenia testowe i osobne bazy testowe (`2026-11-22-panel-finalizacja.md`) |
| Przegląd | przegląd zespołu (`80031fb`); przegląd czterech równoległych strumieni, z którego powstał `services/analyzer/tests/test_spojnosc.py` (docstring); przegląd kodu i UI w `docs/superpowers/plans/2026-11-22-sprint-final-3-osoby.md` §1 |
| Weryfikacja na żywym stosie | `docs/STAN-PROJEKTU.md` §2-3 (pomiary na żywym Bieliku), §7 (czego nie uruchomiono) |

Stan testów analizatora na początku sprintu finałowego: 729 przeszło, 6 pominiętych
(wartość z briefu sprintu; odtwarza ją `python -m pytest -q` w `services/analyzer`).

## 3. Praca równoległa zespołu

- **Gałąź i worktree na osobę lub zadanie.** Gałęzie `feat/*` i `worktree-*` w repozytorium
  (np. `feat/dashboard`, `feat/scraper-finalizacja`, `worktree-modul1-domkniecie`).
  Zmiany wchodzą przez pull requesty (w historii `main` 10 commitów merge PR, m.in. #15, #16, #19, #20, #21).
- **Właściciele plików.** Plany i design doc wskazują właściciela (np. nagłówek
  `2026-11-22-harmonogram-design.md`: „Właściciel: Osoba B"); sprint finałowy dzieli pliki
  między osoby A, B, C.
- **Kontrakty danych.** `AdDocument`, `Finding`, `RuleResult`, `RenderProbe`, `Scope` mają
  przykłady w `fixtures/contract-examples/`. Testy `services/analyzer/tests/test_spojnosc.py`
  i `services/api/tests/test_contracts_copy.py` wykrywają rozjazd kopii kontraktu między serwisami.
- **Bazy testowe oddzielone od bazy zespołu** (`iw_test*`), co opisują plany.

## 4. Kontrola jakości wyników AI

Model 4.5B ocenia reklamy, więc jego wyniki mierzymy, a nie zakładamy.

**Zbiory kontrolne zamrożone przed strojeniem** (historia gita to dokumentuje):

| Zbiór | Etykiety w commicie | Wynik przed poprawkami | Wynik końcowy |
|---|---|---|---|
| `fixtures/module2-holdout/` (83 etykiety) | `229f259` (21.11 18:29), przed uruchomieniem modelu | `17c1821` (18:56): 75% (62/83) | 89%, ale po poprawkach na nim zbiór „nie jest już czysty" |
| `fixtures/module2-holdout-2/` (99 etykiet) | `cbe1c6c` (21.11 18:59), przed poprawkami uogólnienia | - | **82%**, zbiór nieużyty do strojenia |
| `fixtures/module1-labels/` (40 etykiet Modułu 1) | `ec2949e` (21.11 21:57), przed zmianami resolvera | `baseline.json` | `after.json` |

Zbiór strojenia (`fixtures/module2-cases/`, 73 etykiety) daje 96%, ale `docs/STAN-PROJEKTU.md` §3
opisuje go jako optymistyczny. Za uczciwą miarę uznajemy 82% z drugiego zbioru kontrolnego.
Zbiór złoty (`fixtures/gold/`, 8 prawdziwych reklam FB): F1 maks. 0,571; niska wartość
wynika z pokrycia, nie z klasyfikatora (§3 tamże). Narzędzie: `services/analyzer/tools/eval_rules.py`
(wskazane w §3 `STAN-PROJEKTU.md`), wyniki w `eval_results*.json` przy zbiorach.

**Strażnicy w kodzie.** Bielik 4.5B ignoruje część poleceń promptu i „widzi" w tekście
zastrzeżenia, których tam nie ma. Elementy obiektywne rozstrzyga kod
(`services/analyzer/analyzer/rules_llm/guards.py`, `preconditions.py`; commity `fb4f2ea`, `13144a6`),
model ocenia tylko to, co wymaga rozumienia języka. Reguła 10 jest hybrydowa z tego samego powodu.

**Powtarzalność.** `temperature 0` + stały `seed` (`analyzer/llm.py`); powód: przy 0,1 ta sama reklama
dawała różne werdykty. Pomiar: 3 identyczne przebiegi i 0 rozbieżności w smoke teście
4 wsadów x 5 materiałów (`docs/STAN-PROJEKTU.md` §2, §4).

Regresje złapane pomiarem są opisane w `docs/STAN-PROJEKTU.md` §3 (np. dwa fałszywe naruszenia
reguły 18 na korpusie złotym).

## 5. Bezpieczeństwo łańcucha dostaw

- `tools/audit.sh`: `pip-audit 2.10.1` (baza PyPA/OSV) dla każdego `services/*/requirements.txt`
  w czystym kontenerze; wyniki i daty w `docs/SECURITY-AUDIT.md`.
- Wersje zależności przypięte `==` (sprawdza `tools/check_compliance.py`).
- Sekrety tylko w `infra/.env` (w `.gitignore`); w repo jest wyłącznie `infra/.env.example`.
- `tools/check_compliance.py` (commit `5bbe9cb`): brak zewnętrznych adresów, brak zewnętrznych API
  modeli, brak licencji AGPL/SSPL/gemma, brak sekretów, przypięte wersje.
- `npm audit` dla panelu: zaplanowany w sprincie finałowym (plan, sekcja o `npm audit`). W chwili
  pisania nie ma go w `docs/SECURITY-AUDIT.md`; wynik zostanie tam dopisany po wykonaniu.

## 6. Czego AI nie robiło i gdzie decydował człowiek

- **Zakres prawny.** Decyzja, że kryptoaktywa spot są poza zakresem, a CFD/ETP na krypto zostają
  w zakresie, jest zapisana w specyfikacji (nie-cele, §6.6) i w `docs/STAN-PROJEKTU.md` §1.
  Zakres wynika z opisu wyzwania i ustawy, nie z wyboru modelu.
- **Zbiór złoty.** `fixtures/gold/labels.json` jest oznaczany ręcznie (README zbioru); w sprincie
  finałowym analityk ma oceniać żywe findingi w UI (plan, B5).
- **Weryfikacja przez człowieka w produkcie.** Powyżej progu finding wymaga potwierdzenia człowieka,
  a panel zapisuje przypisanie AI vs człowiek (commity `ab7b825`, `7d24c87`).
- **Ograniczenia.** Etykiety Modułu 1 (`fixtures/module1-labels/README.md`) nadał subagent AI
  według rubryki, nie człowiek; autor zbioru kontrolnego nie widział kodu reguł. Nie twierdzimy,
  że to ocena ekspercka.
- **Nieudokumentowane w repo.** Briefy i raporty zadań sprintu leżą w `.superpowers/`
  (niezacommitowane), więc nie podajemy z nich liczby przeglądów kodu ani czasu pracy agentów.
