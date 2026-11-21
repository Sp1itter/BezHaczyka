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

## Przykład: TikTok

`sources/tiktok.py` (około 80 linii) to szkielet na fixture'ach: `discover` filtruje opisy filmów,
`fetch` zwraca opis, linki i napisy jako `transcript`. Tryb live nie jest zaimplementowany,
a zadanie `tiktok-demo` w `schedule.yaml` jest wyłączone.

Włączenie na demo: `enabled: true` w `schedule.yaml` (fixture'y z `TIKTOK_FIXTURES_DIR`,
domyślnie `fixtures/demo-ads/tiktok`).

## Źródła

| nazwa | discover | fetch |
|---|---|---|
| facebook | Meta Ad Library (wyszukiwarka) | render Playwright, 3 viewporty, RenderProbe |
| youtube | wyszukiwarka yt-dlp | metadane, komentarze autora, napisy |
| www | strona startowa + linki z tej samej domeny | widoczny tekst + linki zewnętrzne |
| tiktok | fixture'y (szkielet) | opis, linki, napisy |
