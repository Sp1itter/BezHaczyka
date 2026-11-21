# Moduł 1 – przepływ danych i kontrakty

Moduł 1 (spec. UKNF): reklamy firm inwestycyjnych z rejestru KNF publikowane przez podmioty
trzecie (finfluencerów). Wynik: baza/raport *firma – reklamujący – treść – URL* z okresową
aktualizacją.

## Przepływ

```
scheduler (rq-scheduler, schedule.yaml)
   │  co N min: discover(fb|youtube|www, fraza/seed)   co M min: recheck (najdawniej widziane)
   ▼
q:ingest ── discover_job ──> q:render ── fetch_job(source, url)
                                           │ Source.fetch -> AdDocument
                                           │ resolver (rejestr KNF) -> entity_resolution
                                           │ casedb.record_document(...)  -> new | changed | unchanged
                                           ▼ (tylko new/changed i zakwalifikowane)
                                         q:gpu ── analyzer.worker.analyze_document(payload)
                                                    │ casedb.get_document  (cases.raw -> AdDocument)
                                                    │ analyze() -> Finding (+ ChangeEvent vs poprzedni)
                                                    ▼ casedb.save_finding / save_change_event
Postgres: cases, case_content, case_assets, ai_results, authorized_entities, findings,
          change_events, widok module1_report
```

## Jedno źródło prawdy: casedb

`services/casedb` to warstwa danych całego stosu (migracje + biblioteka + CLI). Scraper
i analyzer instalują ją jako pakiet (`pip install ./casedb` w obrazie, kontekst budowania
`services/`). `infra/init.sql` tworzy tylko rozszerzenie `vector`; cały schemat jest
w `casedb/migrations/`. Tabela `documents` nie istnieje osobno: dokument to `cases.raw`
(pełny `AdDocument` bez wektora), `cases.case_id == AdDocument.id`.

## Kontrakt zadania analizy (kolejka `q:gpu`)

Funkcja RQ: `analyzer.worker.analyze_document`, argument: jeden słownik

```json
{
  "document_id": "uuid (== cases.case_id)",
  "enqueued_at": "ISO-8601",
  "entity_resolution": { "...": "pola EntityResolution, patrz niżej" },
  "det_results": []
}
```

`entity_resolution` (liczy scraper, `services/scraper/resolver.py`):

| pole | typ | znaczenie |
|---|---|---|
| publisher_relation | official / third_party / unknown | relacja publikującego do firmy |
| publisher_is_authorized | bool | publikujący sam jest w rejestrze KNF |
| firm_is_authorized | bool | wymieniona firma jest w rejestrze KNF |
| mentions_authorized_firm | bool | reklama wymienia firmę z rejestru |
| publisher_name | str | nazwa/handle publikującego |
| firm_name_in_ad | str | nazwa firmy w treści |
| registry_knf_id, registry_official_name, registry_score | str, str, float | dopasowanie do rejestru |
| disclosure_found | bool | oznaczenie współpracy (#reklama, współpraca, partner…) |
| affiliate_link | str | link z ref/aff/utm/kodem do domeny firmy |

## Okresowa aktualizacja

`casedb.record_document` porównuje `content_hash` (sha256 znormalizowanego tekstu
+ transkryptu). Wynik `unchanged` podbija `last_seen_at`/`seen_count` i nie tworzy zadania
analizy. `changed` ustawia status `new` i wysyła analizę; analyzer porównuje nowy Finding
z poprzednim (`change_detect.detect_change`) i zapisuje `ChangeEvent`. Zadanie `recheck`
pobiera ponownie najdawniej widziane URL-e; brak materiału ustawia `gone_at`.

## Źródła

| źródło | plik | discover | fetch |
|---|---|---|---|
| facebook | `sources/facebook.py` | Meta Ad Library, fraza | widok `?id=`, RenderProbe |
| youtube | `sources/youtube.py` | yt-dlp `ytsearch`, fraza | metadane + napisy, kwalifikacja promocji |
| www | `sources/www.py` | strona startowa + linki w domenie | httpx, tekst z HTML |

Rotacja User-Agent i proxy: `services/scraper/net.py` (`SCRAPER_USER_AGENTS`,
`SCRAPER_PROXIES`, separator `||`), wspólna dla wszystkich źródeł.

## Uruchomienie i harmonogram

`infra/docker-compose.yml` stawia całość jedną komendą (`docker compose up -d --build`):
`casedb` (migracje + rejestr, jednorazowo), `scraper-worker` (repliki wg `SCRAPER_WORKERS`),
`scheduler` (`python -m scheduler`, zadania w `services/scraper/schedule.yaml`) i `analyzer`.
`python -m scheduler --once` zleca wszystkie zadania jednorazowo (recheck bez progu wieku), co daje
powtarzalne demo: pierwszy przebieg zapisuje przypadki (`new`) i findingi, drugi kończy się
`unchanged` (`seen_count` + 1) bez nowego findingu. Rejestr KNF uzupełnia `tools/knf_registry.py`.
