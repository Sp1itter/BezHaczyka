# Panel nadzorcy — finalizacja (osoba B)

## Spec (wiążący)

Specyfikacja UKNF, aplikacja webowa: wyświetlanie wyników z filtrowaniem (data, źródło, poziom
ryzyka, moduł), wykresy trendów, zmiana statusu rekordu, **WebSocket — powiadomienia o wykryciu
wysokiego ryzyka w czasie rzeczywistym**, panel kalibracji. Jury ocenia trafność, stabilność
interfejsu i powiadomienia na żywo.

Wymagania zespołu:
1. Panel (`services/dashboard`, port 7080) na prawdziwej bazie: **sortowanie** listy.
2. Po kliknięciu pozycji **dokładny raport**: które reguły złapały, **jakim silnikiem**
   (LLM Bielik / DET pomiar renderu / hybryda), na jakiej podstawie prawnej, z jakim **dowodem**
   (cytat, wartości pomiaru, znacznik czasu, viewport, zrzut).
3. Na górze szczegółów **krótkie podsumowanie AI**: dlaczego pozycja została tak oceniona.
4. Alerty WebSocket o wysokim ryzyku **muszą działać**. Dziś nie działają: analyzer zapisuje
   findingi bezpośrednio do Postgresa (`ANALYZER_STORE=db`), a API wysyła alert tylko przy
   `POST /findings` (`services/api/api/main.py`).
5. Raport Modułu 1 (`/api/reports/module1` + `.csv`, już istnieje w API) dostępny w nowym panelu.

Decyzje:
- Podsumowanie w kolumnach `findings.summary` + `findings.summary_engine` (migracja
  `services/casedb/casedb/migrations/015_finding_summary.sql` — JUŻ ISTNIEJE w repo, nie twórz jej),
  NIE w kontrakcie `Finding` (kopia kontraktu w scraperze należy do innej osoby).
- Sortowanie po stronie panelu (panel i tak filtruje lokalnie do 500 pozycji).
- Alerty: API co `ALERT_POLL_S` sekund (domyślnie 3) pyta bazę o nowe findingi `high`.

## Global Constraints

- Worktree: `C:/Users/pawel/Desktop/HackNation2026/INWESTWATCH/.claude/worktrees/panel-finalizacja`.
  Proste komendy git z tego katalogu; `git add` TYLKO własnych plików, jawnie (równolegle pracują
  inne agenty w tym samym worktree).
- NIE zmieniać: `services/scraper/**`, `services/casedb/**` (poza tym, co zadanie mówi wprost),
  `infra/docker-compose.yml` (poza tym, co zadanie mówi wprost), `services/web/**`.
- Kontrakty (`contracts.py` w analyzer/api/scraper) — BEZ zmian.
- Wersje `==` z komentarzem licencji; `python tools/check_compliance.py` → 5× `[OK  ]`
  (adresy w testach tylko `*.example.invalid`).
- Komentarze krótkie, po polsku. Teksty UI po polsku.
- Venvy: `C:/Users/pawel/.claude/jobs/f7866bc7/tmp/venv-{analyzer,api,casedb}` (`<venv>/Scripts/python.exe`);
  przed testami `<venv> -m pip install -q -e <worktree>/services/casedb`. Analyzer/scraper: `-o addopts=""`.
- Bazy testowe (czyszczone przez testy — NIGDY baza `investwatch`):
  Task 1 → `postgresql://investwatch:zmien-mnie-lokalnie@127.0.0.1:5432/iw_test_a`,
  Task 2 → `postgresql://investwatch:zmien-mnie-lokalnie@127.0.0.1:5432/iw_test_b`.
- Baza demo (tylko odczyt, chyba że zadanie mówi inaczej):
  `postgresql://investwatch:zmien-mnie-lokalnie@127.0.0.1:5432/investwatch`.
- Panel: z `services/dashboard`: `npm ci` (jeśli brak node_modules), `npm run build`,
  `node --test src/lib/*.test.js` (podawaj pliki jawnie, jeśli glob nie działa).
- Commit na zadanie, styl repo, ostatnia linia: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Nie uruchamiać graphify.

---

### Task 1: Podsumowanie AI findingu (analyzer)

**Pliki:** `services/analyzer/analyzer/summary.py`, `services/analyzer/analyzer/prompts/summary.txt`,
`services/analyzer/analyzer/worker.py`, `services/analyzer/analyzer/db_store.py`,
`services/analyzer/tools/backfill_summaries.py`, testy w `services/analyzer/tests/`.

1. `summary.py`: `build_summary(finding: Finding, doc: AdDocument | None, client=None, use_llm=True) -> tuple[str, str]`
   zwraca `(tekst, engine)` gdzie engine ∈ `{"llm", "template"}`.
   - Brak reguł z werdyktem `fail` → zawsze szablon, np. „Nie stwierdzono naruszeń (ryzyko niskie, wynik 12).
     Oceniono N reguł; …” (bez LLM — oszczędność czasu GPU).
   - Są naruszenia i `use_llm` → prompt z `prompts/summary.txt` (wypełniany: poziom i wynik ryzyka,
     moduły, routing.reason, firma/KNF/autoryzacja, reklamujący/relacja/ujawnienie, lista naruszonych
     reguł: id, nazwa, podstawa prawna, `evidence.quote` lub `evidence.summary`). Model ma zwrócić JSON
     `{"summary": "..."}`: 2–3 zdania po polsku, bez faktów spoza danych, z odwołaniem do numerów reguł.
     `OllamaClient().generate_json` (jak w `module3.py`).
   - Strażnik: odpowiedź pusta, > 700 znaków, bez żadnego `rule_id` naruszonej reguły, albo `LlmError`
     → szablon. Szablon: „Ryzyko {wysokie|średnie|niskie} (wynik X). Naruszenia: reguła 3 (Informacja
     o ryzyku) — „cytat…”; … Podmiot: … Publikujący: … ({relacja}).” (cytaty skrócone do 120 znaków).
2. `worker.py`: po `analyze()` policz podsumowanie (env `SUMMARY_ENABLED` domyślnie `1`; `SUMMARY_LLM`
   domyślnie `1`; `0` = tylko szablon) i przekaż do zapisu. `DbStore.post_finding(finding, document=None, summary=None, summary_engine=None)`
   zapisuje kolumny `summary`, `summary_engine`. `ApiClient.post_finding` — zachowaj zgodność wywołań
   (przyjmij i zignoruj nowe kwargs). Błąd podsumowania NIGDY nie przerywa zapisu findingu.
3. `tools/backfill_summaries.py --db URL [--llm] [--limit N]`: dla findingów z `summary IS NULL`
   odbuduj `Finding` z wiersza (kolumny JSON) i dokument z `document_snapshot` (jeśli jest), policz
   podsumowanie, UPDATE. Per-rekord try/except, podsumowanie liczb na stdout.
4. Testy: szablon dla braku naruszeń; szablon przy `LlmError`; odrzucenie odpowiedzi bez rule_id;
   akceptacja poprawnej odpowiedzi LLM (atrapa klienta); worker zapisuje summary (atrapa store);
   backfill na `iw_test_a` (migracje casedb przez `casedb.db.migrate`). Pełny zestaw analyzera zielony.
5. Uruchom backfill na bazie demo z `--llm` (Ollama na hoście działa: `http://127.0.0.1:11434`,
   ustaw `OLLAMA_BASE_URL`) — to jedyny dozwolony zapis do bazy demo; najpierw zastosuj migracje
   (`casedb.db.migrate`). Pokaż w raporcie 3 przykładowe podsumowania (LLM i szablon).

---

### Task 2: API — podsumowanie w odpowiedzi i alerty WebSocket z bazy

**Pliki:** `services/api/api/main.py`, `services/api/api/store.py`, testy w `services/api/tests/`,
`services/api/README.md`.

1. `GET /findings` i `GET /findings/{id}` zwracają też `summary` i `summary_engine` (NULL gdy brak;
   SQLite: kolumny może nie być — zwróć `None`, nie wywracaj się).
2. Alerty z bazy: zadanie w tle uruchamiane na starcie aplikacji (lifespan/startup) tylko dla
   Postgresa: co `ALERT_POLL_S` (env, domyślnie 3) s wybiera findingi `risk_level='high'` z
   `created_at > znacznik` (znacznik startowy = chwila startu; potem max widziany `created_at`),
   i wysyła `alert_payload(...)` przez istniejący hub WebSocket. Deduplikacja po `id` z alertami
   wysyłanymi z `POST /findings` (wspólny zbiór ostatnio wysłanych id, ograniczony np. do 1000).
   Wydziel `poll_alerts_once(app) -> int` (zwraca liczbę wysłanych) — testowalne bez czekania.
   Błąd bazy w pętli: log + dalsza praca (pętla nie może umrzeć).
3. Testy na `iw_test_b`: finding `high` wstawiony bezpośrednio do tabeli → `poll_alerts_once` wysyła
   1 alert do podłączonego klienta WS; drugi poll nie wysyła ponownie; finding `low` nie alarmuje;
   `POST /findings` + poll nie dublują. `summary` obecne w odpowiedziach. SQLite: brak pętli, brak błędów.
   Pełny zestaw api zielony (z TEST_DATABASE_URL i bez).

---

### Task 3: Panel — sortowanie i szczegółowy raport pozycji

**Pliki:** `services/dashboard/src/lib/sort.js` (+ `sort.test.js`), `services/dashboard/src/lib/evidence.js`
(+ `evidence.test.js`), `services/dashboard/src/components/findings/FindingsTable.jsx`,
`services/dashboard/src/components/findings/FindingDetail.jsx`, ewentualnie `services/dashboard/src/lib/labels.js`
i `services/dashboard/src/styles.css`. NIE dotykaj `App.jsx`, `Sidebar.jsx`, `api/client.js` (Task 4).

1. `sort.js`: `sortFindings(items, key, dir)`; klucze: `risk` (high>medium>low, potem `risk_score`),
   `score`, `date` (`created_at`), `source`, `module` (`primary_module`), `status`, `publisher`; stabilne,
   `null` na końcu. Testy.
2. `FindingsTable`: klikane nagłówki kolumn sortują (▲/▼, `aria-sort`), domyślnie `risk` malejąco.
   Stan sortowania wewnątrz komponentu.
3. `FindingDetail` — kolejność sekcji:
   a) **Podsumowanie** na górze: `f.summary` z etykietą źródła („AI · Bielik” gdy `summary_engine='llm'`,
      „szablon” gdy `template`; brak → „Podsumowanie niedostępne”).
   b) **Dlaczego**: lista TYLKO naruszonych reguł (verdict `fail`) — numer i nazwa, silnik słownie
      (LLM → „model językowy (Bielik)”, DET → „pomiar renderu”, HYBRID → „hybryda: pomiar + tekst”),
      podstawa prawna, pewność %, waga, dowód.
   c) **Podmioty**: firma w reklamie, oficjalna nazwa i ID KNF, autoryzacja; reklamujący, relacja
      (oficjalny / podmiot trzeci / nieznana), ujawnienie współpracy, link afiliacyjny (tylko http(s) jako link).
   d) **Wszystkie reguły** (rozwijane `<details>`): pogrupowane: „Moduł 2 — informacja o ryzyku”
      (numeryczne id), „Moduł 3 — doradztwo bez zezwolenia” (`M3`), inne; kolumny jak w b).
   e) Istniejące: decyzja człowieka, status, przypisanie, routing, oś zdarzeń — zachowaj.
4. `evidence.js`: `formatEvidence(evidence)` → struktura do wyświetlenia: cytat (w cudzysłowie),
   opis, wartości `measured` (np. `font_px: 9.5`, ratio z 2 miejscami), `transcript_ts` jako `mm:ss`,
   viewport po polsku, `screenshot_crop` jako link tylko gdy http(s). Testy.
5. `npm run build` przechodzi; testy `node --test` zielone.

---

### Task 4: Panel — widok „Moduł 1 — raport”

**Pliki:** `services/dashboard/src/views/Module1Report.jsx`, `services/dashboard/src/lib/module1.js`
(+ `module1.test.js`), `services/dashboard/src/App.jsx`, `services/dashboard/src/components/layout/Sidebar.jsx`,
`services/dashboard/src/api/client.js`. NIE dotykaj plików z Task 3.

1. Pozycja w menu „Moduł 1 — raport” i widok: tabela z `GET /api/reports/module1` (filtry `source`,
   `relation`, `flag`, `since`; `limit=500`): firma (oficjalna nazwa + kraj), reklamujący (link do profilu
   przez safeHref), relacja, flagi jako pigułki z etykietami PL (`podmiot_trzeci_bez_ujawnienia`,
   `link_afiliacyjny_bez_ujawnienia`, `cofniete_zezwolenie`, `zakonczona_dzialalnosc`, `firma_zagraniczna`),
   treść (140 znaków), URL (safeHref), pierwsze/ostatnie wystąpienie, liczba w kampanii.
2. Kafelki: pozycji (`total`), podmioty trzecie, bez ujawnienia, firmy zagraniczne; przycisk
   „Pobierz CSV” → `/api/reports/module1.csv?<te same filtry>`.
3. Obsługa 503/błędu (komunikat PL), ignorowanie spóźnionych odpowiedzi (flaga w cleanupie efektu).
4. `module1.js`: `safeHref`, etykiety flag, budowa query — czyste funkcje z testami.
5. `client.js`: `api.module1Report(filters)` i `api.module1CsvUrl(filters)`.
6. `npm run build` przechodzi; testy zielone.
