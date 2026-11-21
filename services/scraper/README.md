# scraper: FacebookAdsSource (Meta Ad Library)

Ten katalog zawiera źródło `facebook`, sondę RenderProbe i ich testy oraz niezależne [demo scrapera YouTube](youtube/README.md).
YouTube działa przez CLI lub `scan`/`start_background`, z własnymi zależnościami. Podłączenie do wspólnych kolejek i kontraktów pozostaje kolejnym etapem.
Właścicielem serwisu jest osoba A: `Dockerfile`, compose, `WebPageSource` i `rules_det` są po jej stronie.

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
| `jobs.py` | RQ | `discover_job`, `fetch_job`, `schedule_facebook(scheduler)` (CronJob Modułu 1) |

Decyzje dla reguł DET (konsumuje `rules_det`):
- `platform_rule_override(rule_id, "facebook")`: reguły 4, 5 i 8 zwracają `not_applicable` z powodem „typografia platformy (Meta Ad Library)”.
- `feed_fold_evidence(doc.text)`: dla reguły 7 dowód HYBRID (`risk_offset_chars > 125`), a nie werdykt DET.
- Tekst na grafice ma `background_confidence: "unknown"` (krok 3b w `render/probe.js`).

## `.env`

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `FB_MODE` | `auto` | `live` / `replay` / `auto` (gdy sieć zawiedzie albo breaker jest otwarty, przełącza się na korpus offline) |
| `FB_COUNTRY` | `PL` | kraj wyświetlania reklam |
| `FB_QUERIES` / `FB_REFRESH_MIN` | – / `30` | frazy rozdzielone `;` i interwał CronJoba |
| `FB_MAX_ADS_PER_RUN` / `FB_MAX_SCROLLS` | `25` / `3` | twardy limit ruchu na jeden przebieg |
| `FB_MIN_INTERVAL_S` | `5` | globalny odstęp między zapytaniami do Meta (Valkey, wspólny dla wszystkich workerów) |
| `FB_BREAKER_THRESHOLD` / `FB_BREAKER_COOLDOWN_S` | `2` / `1800` | po 2 blokadach źródło pauzuje 30 min |
| `FB_FIXTURES_DIR` | `fixtures/demo-ads/facebook` | korpus offline |
| `SCRAPER_USER_AGENTS` | – | lista UA rozdzielona `\|\|` |
| `SCRAPER_PROXY` | – | jedno opcjonalne proxy (bez rotacji) |
| `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | – | SeaweedFS; bez tych zmiennych pliki trafiają do `SCRAPER_DATA_DIR` |
| `VALKEY_URL` | `redis://valkey:6379/0` | kolejki i stan |
| `API_BASE_URL` | `http://api:8000` | `fetch_job` zapisuje tu dokument (`POST /documents`), potem wrzuca zadanie `analyzer.worker.analyze_document` do `q:gpu` (`docs/INTEGRACJA.md`) |

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
| `USER_AGENTS` | – | lista UA rozdzielona `\|\|` (rotacja w obu poziomach) |
| `PROXY_URLS` | – | lista proxy (przecinek); blokada źródła pauzuje je niezależnie od proxy |

Schemat dla Postgresa: `collector\sql\url_store.postgres.sql` (do migracji `casedb`).

Na noc: maszyna bez usypiania (`powercfg /change standby-timeout-ac 0`), collector i flota w osobnych oknach.
