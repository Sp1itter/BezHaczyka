# scraper: Moduł 1 (facebook, youtube, www_live, tiktok)

Serwis zbiera reklamy i materiały firm inwestycyjnych z czterech źródeł na żywo (`sources/facebook.py`,
`sources/youtube.py`, `sources/www_live.py`, `sources/tiktok.py`; `sources/www.py` = korpus offline), rozpoznaje podmioty względem rejestru KNF (`resolver.py`), zapisuje dokumenty
w bazie (pakiet `casedb`) i zleca analizę kolejką `q:gpu`. Przepływ i kontrakty: `docs/MODUL1-ARCHITEKTURA.md`.

| Plik | Rola |
|---|---|
| `jobs.py` | `discover_job(source, query)` (`q:ingest`), `fetch_job(source, url)`, `recheck_job(limit, older_than_minutes)` (`q:render`/`q:ingest`), fabryka `build_source` |
| `resolver.py` | `Registry` (z `casedb.store.registry_entries`, cache 10 min) i `resolve(doc, registry)` -> pola `EntityResolution` |
| `scheduler.py`, `schedule.yaml` | harmonogram (rq-scheduler): `python -m scheduler`, `--once` = jednorazowy przebieg |
| `worker.py` | pula procesów `SimpleWorker`: `q:ingest`(+`q:ingest:fb`) i kolejki per źródło `q:render:fb/yt/tt`, `q:fetch:www` (szczegóły: `SOURCES.md`) |
| `tools/measure_ingest.py` | pomiar: nowe materiały/min per źródło po `--once` |

## Wydajność (pomiar 22.11.2026, `tools/measure_ingest.py`, 12 min, świeże frazy)

| źródło | nowe | /min | uwagi |
|---|---|---|---|
| www_live | 192 | 16,0 | ddgs → curl_cffi → trafilatura; oferty z RenderProbe ×3 |
| youtube | 58 | 4,8 | limiter `YT_MIN_INTERVAL_S=8`; napisy blokowane (429) → audio dla Whispera |
| tiktok | 48 | 4,0 | ddgs `site:tiktok.com` + yt-dlp; wideo tylko dla filmów o finansach |
| facebook | 45 | 3,7 | limiter `FB_MIN_INTERVAL_S=5` (≤ 12/min); w szczycie 9,1/min |
| **razem** | **343** | **28,5** | przed sprintem: ~2/min |

**Metodyka pomiaru.** Wynik powyżej i pomiar do prezentacji to `scheduler --once` na **czystym stosie**
(pusta baza i puste zbiory `<źródło>:seen`, np. `docker compose -p iwverify` po świeżym starcie).
Wtedy każda znaleziona reklama/strona/film jest „nowa”, więc mierzymy przepustowość silnika zbierania,
a nie liczbę materiałów, które jeszcze nie były w bazie. Na długo działającym stosie, gdy frazy są już
zebrane, tempo nowych materiałów spada (22.11, 01:27–01:37: 8,2/min, głównie FB), bo ograniczają je
pula wyników wyszukiwarek i celowe limity zapytań do platform (`FB_MIN_INTERVAL_S`, `YT_MIN_INTERVAL_S`,
`SEARCH_MIN_INTERVAL_S`), a nie wydajność kodu. Pomiar pokazuje, że architektura (kolejki per źródło,
pula procesów, jedna przeglądarka na proces) przetwarza ≥ 20 materiałów/min.

Błędy pobrań: FB 0/57, WWW ~12% (403/timeout serwisów). Reklamy TikTok Ad Library nie są
pobierane (API odpowiada 421 również przeglądarce — ochrona przed automatami, nie obchodzimy).

Resolver: wzmianka firmy to domena z URL-a > dokładna nazwa/alias > fuzzy (rapidfuzz, próg 90, nazwy
od 8 znaków); aliasy krótsze niż 3 znaki są ignorowane. Relacja: `official` (domena/handle/nazwa
publikującego należy do firmy), `third_party` (firma wymieniona, publikujący to kto inny), `unknown`
(brak wzmianki). `disclosure_found` i `affiliate_link` liczone z tekstu, transkryptu i linków w treści.
Ograniczenie: strona zbiorcza z linkiem „…w XTB” w treści też liczy się jako wzmianka.

Rejestr: `python tools/knf_registry.py --dry-run` (w katalogu głównym repo) uzupełnia
`knf_registry.csv` o nowe podmioty z wykazów KNF (adresy w kolumnie `source_url`), nie nadpisując
ręcznych aliasów/domen. Po zmianie CSV: `docker compose run --rm casedb load-registry`.

Po zmianie resolvera lub rejestru KNF: `docker compose exec scraper-worker python tools/reresolve.py` (domyślnie `DATABASE_URL`; `--dry-run`, `--source`) przelicza `cases.entity_resolution` z `cases.raw`.

## Quick start

```bash
cd services/scraper
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # Windows
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe -m pytest                                # offline, bez sieci
```

## Jak to działa

| Krok | Gdzie | Co robi |
|---|---|---|
| `discover(query)` | `q:ingest` | Otwiera wyszukiwanie Ad Library (PL, aktywne). Bierze węzły reklam z inline JSON i z `/api/graphql/`, zwraca `…/ads/library/?id=<ad_archive_id>` |
| `fetch(url)` | `q:render` | Ładuje widok `?id=` na 3 viewportach, usuwa nakładki bez klikania, blokuje nawigację, uruchamia RenderProbe, robi zrzuty desktop/mobile, pobiera mp4. Tekst pochodzi z JSON-a Meta |
| `jobs.py` | RQ | `discover_job(source, query)`, `fetch_job(source, url)` - patrz wyżej; harmonogram w `scheduler.py` |

Decyzje dla reguł DET (konsumuje `rules_det`):
- `platform_rule_override(rule_id, "facebook")`: reguły 4, 5 i 8 zwracają `not_applicable` z powodem „typografia platformy (Meta Ad Library)”.
- `feed_fold_evidence(doc.text)`: dla reguły 7 dowód HYBRID (`risk_offset_chars > 125`), a nie werdykt DET.
- Tekst na grafice ma `background_confidence: "unknown"` (krok 3b w `render/probe.js`).

## `.env`

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `FB_MODE` | `auto` | `live` / `replay` / `auto` (gdy sieć zawiedzie albo breaker jest otwarty, przełącza się na korpus offline) |
| `FB_COUNTRY` | `PL` | kraj wyświetlania reklam |
| `FB_MAX_ADS_PER_RUN` / `FB_MAX_SCROLLS` | `25` / `3` | twardy limit ruchu na jeden przebieg (każda fraza zwraca ≤ 25 reklam) |
| `SCRAPER_INGEST_PROCS`, `SCRAPER_POOL_FB/YT/WWW/TT` | `3`, `1/1/2/1` | procesy w kontenerze (worker.py) |
| `TIKTOK_MODE` | `live` | `live` / `replay` (fixture'y) |
| `WWW_RENDER`, `WWW_QUERY_SUFFIXES`, `WWW_DOMAIN_INTERVAL_S` | `1`, warianty, `1` | www_live: RenderProbe ofert, warianty frazy, limiter per domena |
| `YT_AUDIO_MAX_S`, `YT_RESULTS_PER_QUERY` | `1200`, `20` | audio dla Whispera do 20 min; wyniki wyszukiwania YT |
| `ANALYSIS_JOB_TIMEOUT_S` | `900` | `job_timeout` zadań `q:gpu` |
| `FB_MIN_INTERVAL_S` | `5` | globalny odstęp między zapytaniami do Meta (Valkey, wspólny dla wszystkich workerów) |
| `FB_BREAKER_THRESHOLD` / `FB_BREAKER_COOLDOWN_S` | `2` / `1800` | po 2 blokadach źródło pauzuje 30 min |
| `FB_FIXTURES_DIR` | `fixtures/demo-ads/facebook` | korpus offline |
| `SCRAPER_USER_AGENTS` / `SCRAPER_PROXIES` | – | listy UA / proxy rozdzielone `\|\|` (`SCRAPER_PROXY`: pojedyncze proxy) |
| `YT_MIN_INTERVAL_S` | `8` | odstęp między zapytaniami do YouTube (Valkey `yt:ratelimit`); 3 s dawało IpBlocked przy napisach |
| `DATABASE_URL` | – | baza `casedb` (w compose składana z `POSTGRES_*`) |
| `SCHEDULE_FILE` / `SCHEDULE_DISABLE` / `SCHEDULE_INTERVAL_<NAZWA>` | `schedule.yaml` / – / – | nadpisania harmonogramu |
| `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | – | SeaweedFS; bez tych zmiennych pliki trafiają do `SCRAPER_DATA_DIR` |
| `VALKEY_URL` | `redis://valkey:6379/0` | kolejki i stan |
| `SCRAPER_OUTPUT_QUEUE` / `SCRAPER_OUTPUT_FUNC` | `q:gpu` / `analyzer.worker.analyze_document` | zlecenie analizy przez nazwę funkcji, bez importu |

## Korpus demo (nagrać wieczorem przed demo)

```bash
.venv/Scripts/python.exe record_fb_fixtures.py --query "inwestycje" --max 6
```

Nagranie zapisuje zamrożony snapshot `page.html` (ok. 3 MB na reklamę). Replay daje identyczną sondę jak przebieg na żywo. HAR nie działa: aplikacja Meta nie renderuje się z nagrania, szczegóły w `render/freeze.js`.

## Collector i flota (praca ciągła)

Dwa niezależne procesy pracują na wspólnej tabeli `url_store`:

| Proces | Komenda (PowerShell, z `services\scraper`) | Co robi |
|---|---|---|
| Poziom 1: collector | `.venv\Scripts\python.exe -m collector run` | zapytania z `config\queries.yaml` do Meta Ad Library; zapisuje kandydatów z priorytetem, bez renderu i bez LLM |
| Poziom 2: flota | `.venv\Scripts\python.exe -m collector fleet` | bierze kandydatów od najwyższego priorytetu (lease, bez dublowania), pobiera, liczy DET; do analyzera wysyła tylko od `analyzer_min_priority` |

Komendy operatora:

```powershell
.venv\Scripts\python.exe -m collector ctl stats         # liczniki: kandydaci, kolejka, kwarantanna, scalone, gotowe
.venv\Scripts\python.exe -m collector ctl pause         # wstrzymuje collector; flota dalej przerabia kolejkę
.venv\Scripts\python.exe -m collector ctl resume
.venv\Scripts\python.exe -m collector ctl reprioritize  # po zmianie słowników
.venv\Scripts\python.exe -m collector ctl errors        # odrzucone pliki konfiguracji
.venv\Scripts\python.exe -m collector seed-synthetic    # plan B: strony z fixtures\demo-ads jako kandydaci
```

Słowniki, wagi i progi są w `config\lexicons.yaml`, zapytania w `config\queries.yaml`, osoby publiczne w `config\personas.json`. Zmiana działa bez restartu. Plik z błędem jest odrzucany w całości i zostaje poprzednia wersja.

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `COLLECTOR_DATABASE_URL` | – | Postgres dla `url_store`; bez niej plik SQLite |
| `COLLECTOR_DB_PATH` | `data/collector/url_store.sqlite` | plik SQLite |
| `COLLECTOR_STATE_DIR` | `data/collector` | flaga pauzy, `stats.json`, pobrane dokumenty |
| `COLLECTOR_CONFIG_DIR` | `services/scraper/config` | słowniki i zapytania |
| `COLLECTOR_INTERVAL_S` / `COLLECTOR_JITTER_S` | `50` / `15` | przerwa między zapytaniami |
| `COLLECTOR_MAX_QUERIES_PER_HOUR` | `60` | limit zapytań do Meta |
| `COLLECTOR_ANALYZE` | `1` | `0` wyłącza wysyłkę do analyzera (sam fetch) |
| `SCRAPER_USER_AGENTS` / `SCRAPER_PROXIES` | – | wspólny `net.Rotator` (UA i proxy losowane na kontekst); blokada źródła pauzuje je niezależnie od proxy |

Schemat dla Postgresa: `collector\sql\url_store.postgres.sql` (do migracji `casedb`).

Na noc: maszyna bez usypiania (`powercfg /change standby-timeout-ac 0`), collector i flota w osobnych oknach.
