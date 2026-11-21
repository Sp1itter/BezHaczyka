# Moduł 1 — profesjonalne domknięcie

## Spec (wiążący)

Specyfikacja UKNF, Moduł 1: wyszukiwanie reklam zarejestrowanych w Polsce firm inwestycyjnych
(i ich instrumentów/usług) zamieszczanych przez **podmioty trzecie lub osoby prywatne
(finfluencerów)**, także **polskojęzycznych reklam zagranicznych firm działających
transgranicznie**. Rezultat: automatyczny raport/baza: **dane firmy, dane podmiotu
reklamującego, treść reklamy, dokładna lokalizacja (URL)** + mechanizm okresowej aktualizacji.
Załącznik 1: rejestr KNF — domy maklerskie, banki maklerskie, oddziały zagranicznych firm,
zagraniczne firmy bez oddziału.

Stan wyjściowy (zmierzony 2026-11-21 na żywych danych, 63 wiersze raportu):
- oficjalna strona „XTB Online Investing” klasyfikowana jako `third_party`
  (`services/scraper/resolver.py` `match_publisher` porównuje nazwę wyświetlaną tylko dokładnie),
- `disclosure_found` = false w 63/63 (lista `DISCLOSURE_PHRASES` ma 10 fraz),
- resolver zna 41 firm (`authorized_entities` z CSV); snapshot KNF (1088 wpisów, 712 zagranicznych
  firm notyfikowanych, agenci, cofnięte zezwolenia) w `knf_entities` ładowany tylko ręcznie
  (`casedb load-knf`) i nieużywany,
- raport tylko z CLI (`casedb report module1`), brak w API i panelu, brak flag naruszeń,
  duplikaty kreacji, brak linku do zrzutu.

Cel: raport Modułu 1, który nadzorca może otworzyć w panelu i pobrać jako CSV, z poprawną
relacją oficjalny/podmiot trzeci, wykrywaniem ujawnień i flagami naruszeń, pokrywający pełny
rejestr KNF, z ZMIERZONĄ trafnością na zbiorze z etykietami nadanymi przed zmianami.

## Global Constraints

- Repo: worktree `C:/Users/pawel/Desktop/HackNation2026/INWESTWATCH/.claude/worktrees/modul1-domkniecie`.
  Tylko proste komendy git z tego katalogu; `git add` wyłącznie własnych plików, jawnie.
- Nie zmieniać: `services/dashboard/**` (nowy panel — inna osoba), `services/scraper/sources/facebook.py`,
  `services/scraper/render/**`, `services/scraper/collector/**`, `infra/docker-compose.yml`.
- Migracje casedb: NOWE pliki z kolejnym numerem (`011_…`, `012_…`), nigdy edycja istniejących.
  Muszą działać na bazie, na której już są 001/002/010 (idempotentne `IF NOT EXISTS`, widok przez
  `DROP VIEW IF EXISTS … ; CREATE VIEW …`).
- Wersje `==` z komentarzem licencji; `python tools/check_compliance.py` → 5× `[OK  ]`.
- Komentarze krótkie, po polsku. Bez ścian tekstu.
- Testy (venvy istnieją; python: `<venv>/Scripts/python.exe`):
  - casedb: `C:/Users/pawel/.claude/jobs/f7866bc7/tmp/venv-casedb`, z `services/casedb`,
    `TEST_DATABASE_URL=postgresql://investwatch:zmien-mnie-lokalnie@127.0.0.1:5432/iw_test`
    (baza testowa — testy ją czyszczą; NIGDY nie wskazuj bazy `investwatch`).
  - scraper: `C:/Users/pawel/.claude/jobs/f7866bc7/tmp/venv-scraper`, z `services/scraper`,
    `-o addopts=""`. PRZED testami: `<venv> -m pip install -q -e <worktree>/services/casedb`
    (venv ma casedb z innego katalogu).
  - api: `C:/Users/pawel/.claude/jobs/f7866bc7/tmp/venv-api`, z `services/api`.
  - web: `node --test src/lib/*.test.js` z `services/web`.
- Baza demo (tylko ODCZYT, chyba że zadanie mówi inaczej): Postgres w Dockerze,
  `docker exec investwatch-postgres-1 psql -U investwatch -d investwatch -c "<SQL>"`.
  Dokument: `cases.raw` (pełny AdDocument JSON), wynik resolvera: `cases.entity_resolution`.
- Commit na zadanie, styl repo (`feat(modul1): …`), ostatnia linia:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Nie uruchamiać graphify.

---

### Task 1: Zbiór z etykietami Modułu 1 i ewaluacja (PRZED zmianami resolvera)

**Pliki:** `fixtures/module1-labels/cases.jsonl`, `fixtures/module1-labels/README.md`,
`services/scraper/tools/eval_module1.py`, `services/scraper/tests/test_eval_module1.py`,
`fixtures/module1-labels/baseline.json`.

1. Z bazy demo wybierz **40 przypadków** (`cases.raw IS NOT NULL`), zróżnicowanych: ≥12 facebook,
   ≥12 youtube, wszystkie www; preferuj te, gdzie `entity_resolution->>'registry_knf_id'` jest ustawione,
   ale dołóż ≥6 bez dopasowania. Zapisz do `cases.jsonl` po jednym obiekcie:
   `{"case_id", "source", "url", "publisher_display_name", "publisher_handle", "publisher_profile_url",
     "title", "text" (pierwsze 1500 znaków), "doc": <pełny cases.raw>, "labels": {...}}`.
2. Etykiety nadajesz WYŁĄCZNIE z treści (nie patrz w kod resolvera ani w `entity_resolution`), wg rubryki:
   - `firm`: oficjalna nazwa firmy inwestycyjnej, którą materiał reklamuje/promuje (albo `null`),
   - `relation`: `official` gdy publikujący to sama firma (jej strona/kanał — nazwa strony, handle lub
     domena profilu należy do firmy, np. „XTB Online Investing”), `third_party` gdy publikuje kto inny
     o firmie, `unknown` gdy materiał nie dotyczy żadnej firmy inwestycyjnej,
   - `disclosure`: `true` gdy tekst jawnie ujawnia współpracę/reklamę (np. #reklama, „materiał sponsorowany”,
     „link afiliacyjny/partnerski”, „kod polecający”, „współpraca z”, „partnerem odcinka jest”,
     „płatna współpraca”), inaczej `false`,
   - `affiliate`: `true` gdy w tekście jest link z kodem/parametrem polecającym do firmy,
   - `note`: jedno zdanie uzasadnienia.
   `README.md`: rubryka + oświadczenie, że etykiety nadano przed zmianami resolvera (data, commit bazowy).
3. `eval_module1.py`: wczytuje `cases.jsonl`, dla każdego `doc` liczy `resolver.resolve(AdDocument(**doc), registry)`
   z rejestrem z bazy (`--db URL`, domyślnie env `DATABASE_URL`) i porównuje z etykietami.
   Raport (stdout + `--out plik.json`): accuracy `relation`, precision/recall `disclosure`
   (klasa true), accuracy `firm` (porównanie po `registry_official_name` vs `firm`, case-insensitive,
   tylko gdy etykieta `firm` nie jest null), lista pomyłek (case_id, pole, oczekiwane, otrzymane).
   Logika porównania w czystych funkcjach testowalnych bez bazy.
4. Testy jednostkowe porównania (bez bazy).
5. Uruchom na bazie demo (`--db postgresql://investwatch:zmien-mnie-lokalnie@127.0.0.1:5432/investwatch`)
   i zapisz wynik do `baseline.json` (to jest punkt „przed”).

---

### Task 2: Pełny rejestr KNF w dopasowaniu (zagraniczne firmy, agenci, cofnięte zezwolenia)

**Pliki:** `services/casedb/casedb/migrations/011_registry_source.sql`, `services/casedb/casedb/cli.py`,
`services/casedb/casedb/store.py`, `services/casedb/casedb/knf.py`, testy casedb,
`services/scraper/resolver.py`, `services/scraper/jobs.py` (tylko wywołanie YouTube), testy scrapera.

1. Migracja 011: `authorized_entities` + kolumna `source TEXT NOT NULL DEFAULT 'curated'`
   (`'curated'` = CSV z aliasami/domenami, `'knf'` = wyprowadzone ze snapshotu) oraz `active BOOLEAN NOT NULL DEFAULT true`.
2. `casedb init` (cli): po migracji i CSV dodatkowo ładuje snapshot (`knf.load_snapshot` domyślnego pliku)
   i wywołuje nową `store.sync_registry_from_knf(conn) -> int`, która upsertuje do `authorized_entities`
   wpisy snapshotu z kategorią `firma_inwestycyjna` lub `zagraniczna_firma_inwestycyjna`
   (aktywne i nieaktywne), których `name_key` nie pokrywa się z firmą curated:
   `knf_id = 'KNF-' || register || '-' || first 10 hex of sha1(name_key)`, `name`, `normalized_name`
   (casedb `normalize_name`), `type` = register, `country` = z pól karty (`Państwo macierzyste` /
   `Nazwa kraju, w którym działalność domu maklerskiego została notyfikowana`) albo `PL` dla
   domów i banków, `register`, `aliases` = `former_names`, `source='knf'`, `active` = REGISTERS[register][1].
   Wpisy curated nie są nadpisywane. Funkcja idempotentna.
3. `registry_entries` zwraca też `source` i `active`.
4. Agenci (`category='agent'`, aktywni) NIE trafiają do `authorized_entities`. Nowa
   `store.knf_agent_keys(conn) -> set[str]` (klucze `name_key` aktywnych agentów).
5. Resolver:
   - `Registry.from_rows`: firmy `source='knf'` dopasowywane tylko DOKŁADNIE (bez fuzzy);
     nazwa snapshotu musi mieć ≥ 6 znaków po normalizacji ALBO ≥ 2 słowa, inaczej pomijana;
   - nowe pole wyniku `firm_license_active` (bool|None): `active` dopasowanej firmy;
     `firm_is_authorized` = dopasowanie do firmy AKTYWNEJ (dla nieaktywnej `false`),
   - `Registry` ładuje też klucze agentów (z bazy w `from_db`; w `from_rows` opcjonalny parametr
     `agent_keys`); `publisher_is_authorized` = true także gdy `knf.name_key(display_name)` ∈ agentów.
6. YouTube: słownik (`dictionary_from_registry`) budowany tylko z wierszy `source='curated'`
   (bez zmiany pliku `sources/youtube.py` — filtr w `jobs.py` przed wywołaniem).
7. Testy: casedb (sync idempotentny, curated nienadpisane, kraj, active), scraper (exact-only dla knf,
   krótka nazwa pominięta, nieaktywna firma → `firm_is_authorized=false`, agent → `publisher_is_authorized`).
   Pełne zestawy casedb i scrapera zielone.

---

### Task 3: Relacja oficjalny/podmiot trzeci, ujawnienia, ponowne rozwiązanie bazy

**Pliki:** `services/scraper/resolver.py`, `services/casedb/casedb/data/knf_registry.csv`,
`services/scraper/tools/reresolve.py`, `services/casedb/casedb/store.py` (jeśli potrzebna funkcja zapisu),
testy scrapera.

1. `match_publisher` — kolejność: domena profilu → handle → nazwa wyświetlana dokładna (jak dziś) →
   NOWE: znormalizowana nazwa wyświetlana ZACZYNA SIĘ od aliasu/nazwy firmy jako całego słowa/słów
   (np. „xtb online investing” zaczyna się od „xtb”), tylko dla firm `source='curated'` i aliasów ≥ 3 znaki.
   Gdy pasuje kilka firm — najdłuższy alias.
2. `knf_registry.csv`: uzupełnij kolumnę `handles` dla firm, które w bazie demo mają oficjalne strony/kanały —
   sprawdź `SELECT DISTINCT raw->'publisher'->>'display_name', raw->'publisher'->>'handle', source FROM cases`
   i dodaj handle stron/kanałów, które ewidentnie należą do firmy (np. strona FB „XTB Online Investing”).
   Nie zgaduj — tylko to, co widać w danych.
3. `DISCLOSURE_PHRASES` rozszerz o (formy po `_fold`, bez diakrytyków): `link afiliacyjny`, `linki afiliacyjne`,
   `link partnerski`, `linki partnerskie`, `link polecajacy`, `kod polecajacy`, `kod rabatowy`, `kod promocyjny`,
   `wspolpraca platna`, `platna wspolpraca`, `platne partnerstwo`, `we wspolpracy z`, `odcinek powstal we wspolpracy`,
   `sponsorem odcinka`, `sponsor odcinka`, `partnerem materialu`, `material reklamowy`, `reklama`
   (tylko jako samodzielne słowo w pierwszej linii lub jako `[reklama]`/`(reklama)`), `paid partnership`,
   `#wspolpracareklamowa`, `#partner`, `#sponsorowane`, `#reklamaxtb`-style: każdy hashtag zaczynający się od `#reklama`.
   Zachowaj granice słów; dopisz testy pozytywne i negatywne (np. „reklamacja” nie jest ujawnieniem).
4. Nowe pole wyniku `affiliate_without_disclosure` = `affiliate_link is not None and not disclosure_found`.
5. `tools/reresolve.py`: `python tools/reresolve.py --db URL [--source S] [--dry-run]` — dla każdego
   `cases` z `raw` liczy `resolve()` i zapisuje `cases.entity_resolution` (UPDATE), wypisuje podsumowanie
   zmian relacji/ujawnień (ile przeszło z third_party na official itd.).
6. Testy: XTB Online Investing → official; „Inwestuj z XTB” (finfluencer) → third_party; nowe frazy;
   `affiliate_without_disclosure`. Pełny zestaw scrapera zielony.

---

### Task 4: Raport Modułu 1 — flagi naruszeń, kampanie, zrzut

**Pliki:** `services/casedb/casedb/migrations/012_module1_report_v2.sql`, testy casedb.

Widok `module1_report` od nowa (`DROP VIEW IF EXISTS module1_report; CREATE VIEW …`) z WSZYSTKIMI
dotychczasowymi kolumnami (te same nazwy i znaczenie) plus na końcu:
- `firm_license_active` (z `entity_resolution`),
- `affiliate_without_disclosure` (z `entity_resolution`, boolean),
- `screenshot_uri`: pierwszy `case_assets.uri` z `kind='screenshot'` dla przypadku (NULL gdy brak),
- `campaign_key`: `md5(lower(regexp_replace(left(tresc,300),'\s+',' ','g')))` (NULL gdy brak treści),
- `campaign_size`: liczba wierszy z tym samym `campaign_key` (okno),
- `m1_flags TEXT[]` (bez NULL-i, kolejność stała):
  `'podmiot_trzeci_bez_ujawnienia'` gdy relation='third_party' AND NOT disclosure_found;
  `'link_afiliacyjny_bez_ujawnienia'` gdy affiliate_without_disclosure;
  `'cofniete_zezwolenie'` gdy firm_license_active = false;
  `'firma_zagraniczna'` gdy firm_country IS NOT NULL AND firm_country <> 'PL'.
Warunek WHERE bez zmian. Test na bazie testowej: przypadek z third_party bez ujawnienia ma flagę,
official nie ma; `campaign_size` = 2 dla dwóch identycznych treści; `screenshot_uri` z case_assets.
`casedb report module1 --format csv` działa z nowymi kolumnami (tablice w CSV jako `a;b`).

---

### Task 5: API — raport Modułu 1 (JSON + CSV)

**Pliki:** `services/api/api/main.py`, `services/api/api/store.py`, testy api, `services/api/README.md`.

1. `GET /reports/module1` — query: `source`, `relation`, `flag` (element `m1_flags`), `since` (ISO data,
   po `last_seen_at`), `limit` (domyślnie 200, max 1000), `offset`. Zwraca `{"items": [...], "total": N}`
   z kolumnami widoku (daty ISO).
2. `GET /reports/module1.csv` — te same filtry, `text/csv; charset=utf-8` z BOM (Excel), nagłówek
   `Content-Disposition: attachment; filename="modul1-raport-YYYYMMDD.csv"`, tablice jako `a;b`.
3. Na SQLite (tryb testów/dev) widoku nie ma: endpointy zwracają 503 z czytelnym komunikatem.
4. Testy: na Postgresie (`TEST_DATABASE_URL` jak dla casedb; jeśli testy api korzystają z innej zmiennej —
   użyj tej, której już używają) — stworzenie schematu przez migracje casedb
   (`casedb.db.migrate`), wstawienie przypadku, sprawdzenie filtrów i CSV; na SQLite — 503.

---

### Task 6: Zakładka „Moduł 1” w działającym panelu (`services/web`)

**Pliki:** `services/web/src/components/Module1.jsx`, `services/web/src/App.jsx`, `services/web/src/lib/api.js`,
ewentualnie `services/web/src/styles.css`, test logiki w `services/web/src/lib/*.test.js`.

1. Nowa zakładka „Moduł 1 — raport” obok istniejących. Tabela: firma (oficjalna nazwa + kraj),
   reklamujący (nazwa, link do profilu), relacja, flagi (czytelne etykiety PL jako „pigułki”),
   treść (skrót 140 znaków, pełna w `title`), URL (link), zrzut (link gdy `screenshot_uri`),
   pierwsze/ostatnie wystąpienie, liczba w kampanii.
2. Filtry: źródło, relacja, flaga; przycisk „Pobierz CSV” (link do `/api/reports/module1.csv` z tymi filtrami).
3. Kafelki nad tabelą: liczba pozycji, podmioty trzecie, bez ujawnienia, firmy zagraniczne.
4. Mapowanie flag na etykiety i budowa query stringu jako czyste funkcje w `src/lib/` z testem `node --test`.
5. `npm run build` przechodzi (z `services/web`, `npm ci` jeśli brak node_modules).
