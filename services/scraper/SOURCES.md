# Jak dodać źródło

Źródło to klasa z dwiema metodami (`sources/base.py`, protokół `Source`):

```python
class MojeZrodlo:
    name = "moje"
    def discover(self, query: str) -> Iterable[str]: ...  # fraza/seed -> URL-e
    def fetch(self, url: str) -> AdDocument: ...           # URL -> AdDocument (contracts.py)
```

Kolejki, deduplikacja, limiter, resolver KNF, zapis do bazy i analiza są wspólne.
Źródło zgłasza błędy przez `SourceError`, `SourceBlocked` (otwiera breaker) i `SourceGone` (`gone_at`).

## Kroki

1. `sources/<nazwa>.py` z klasą jak wyżej.
2. `jobs.py`: nazwa w `SOURCES` i gałąź w `build_source`.
3. `schedule.yaml`: zadanie `kind: discover` z `source: <nazwa>`; na start `enabled: false`.
4. Baza: migracja w `services/casedb/casedb/migrations/` rozszerzająca `cases_source_check`
   (wzór: `016_source_tiktok.sql`).
5. Fixture w `fixtures/demo-ads/<nazwa>/` i wpis w `ADAPTERS` w `tests/test_source_contract.py`.
   Bez wpisu `test_every_source_has_adapter` nie przejdzie.
6. Testy jednostkowe źródła (`tests/test_<nazwa>.py`).

## TikTok

`sources/tiktok.py`: `TIKTOK_MODE=live` (domyślnie) odkrywa filmy wyszukiwarką
(`site:tiktok.com <fraza>`, ddgs — ekstraktor tagów yt-dlp jest oznaczony jako zepsuty),
metadane i napisy pobiera yt-dlp, a filmy o finansach (filtr słów kluczowych) zapisuje do S3,
żeby analyzer zrobił transkrypcję Whisperem. `TIKTOK_MODE=replay` = fixture'y (`tiktok-demo`).

**TikTok Ad Library (reklamy płatne) nie jest pobierana.** Publiczne API wyszukiwania
`library.tiktok.com/api/v1/search` zwraca `421 system busy` także prawdziwej przeglądarce
(ochrona przed automatami); obchodzenie jej jest poza zasadami projektu. Legalna droga:
oficjalne [Commercial Content API](https://developers.tiktok.com/products/commercial-content-api)
(rejestracja aplikacji, klucz) — wtedy nowe źródło `tiktok_ads` (migracja 017 już je dopuszcza).

## Kolejki i wydajność (sprint finałowy, A1)

| kolejka | procesy w kontenerze `scraper-worker-render` | co |
|---|---|---|
| `q:ingest` | `SCRAPER_INGEST_PROCS` (3) w `scraper-worker` | discover FB/WWW/TikTok, recheck |
| `q:render:fb` | `SCRAPER_POOL_FB` (1) | reklamy Meta (Chromium, limiter `FB_MIN_INTERVAL_S`) |
| `q:render:yt` | `SCRAPER_POOL_YT` (1) | discover i pobrania YouTube (limiter `YT_MIN_INTERVAL_S`) |
| `q:fetch:www` | `SCRAPER_POOL_WWW` (2) | `www`, `www_live` (curl_cffi, render tylko ofert) |
| `q:render:tt` | `SCRAPER_POOL_TT` (1) | TikTok |

Każdy proces to `SimpleWorker` (bez forka na zadanie): jedna przeglądarka Chromium i rejestr KNF
na proces. URL trafia do `<źródło>:seen` dopiero po udanym pobraniu (nieudane wracają przy
następnym discover). Pomiar: `python tools/measure_ingest.py --minutes 10` (zleca `--once`).

## Źródła

| nazwa | discover | fetch |
|---|---|---|
| facebook | Meta Ad Library (wyszukiwarka) | render Playwright, 3 viewporty, RenderProbe |
| youtube | wyszukiwarka yt-dlp | metadane, komentarze autora, napisy json3 z yt-dlp; przy blokadzie (429) audio m4a dla Whispera |
| www | strona startowa + linki z tej samej domeny (korpus offline nginx) | widoczny tekst + linki zewnętrzne |
| www_live | ddgs (pl-pl), filtr szumu i domen z rejestru KNF | curl_cffi + trafilatura; oferty: RenderProbe ×3, zrzuty |
| tiktok | live: ddgs `site:tiktok.com`; replay: fixture'y | yt-dlp: opis, napisy, wideo dla Whispera |
