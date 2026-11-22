# infra – stos Docker Compose (projekt `investwatch`)

Komendy uruchomienia, adresy i procedura „po git pull”: `README.md` w korzeniu repo.

## Serwisy

| Serwis | Rola | Start |
|---|---|---|
| postgres (`pgvector/pgvector:pg16`) | przypadki, dokumenty, findingi (schemat: migracje casedb) | długotrwały |
| valkey | kolejki RQ, stan scrapera (limiter, breaker) | długotrwały |
| seaweedfs | S3 :8333: HTML, zrzuty, mp4 | długotrwały |
| nginx | korpus demo offline :8080 | długotrwały |
| casedb | migracje casedb + rejestr KNF | jednorazowy (Exited 0) |
| api | FastAPI :8000 | długotrwały |
| web | dashboard :7090 | długotrwały |
| analyzer | worker kolejki `q:gpu` | długotrwały |
| scraper-worker | worker `q:ingest` (discover) + `q:render` (pobranie, Playwright) | długotrwały, repliki `SCRAPER_WORKERS` |
| scheduler | rq-scheduler: harmonogram z `services/scraper/schedule.yaml` | długotrwały |
| ollama | LLM + embeddingi, GPU NVIDIA (port wewnętrzny 11434) | długotrwały |
| ollama-pull | pobiera modele z `OLLAMA_MODELS_PULL` | jednorazowy (Exited 0) |
| scraper-worker-render | pobieranie i render stron (Playwright, 3 rozdzielczości) | długotrwały |
| autoscaler | dokłada kontenery `analyzer` przy kolejce, limity z panelu operatora | długotrwały |
| docker-socket-proxy | ograniczony dostęp autoskalera do Dockera (osobna sieć) | długotrwały |

## Najważniejsze ustawienia (`infra/.env`)

| Serwis | Ustawienia |
|---|---|
| scheduler | `services/scraper/schedule.yaml` (frazy, konta, częstotliwość) |
| scraper-worker, scraper-worker-render | `SCRAPER_*`, `FB_*`, `YT_*`, `TIKTOK_MODE`, `WWW_RENDER`, rotacja: `SCRAPER_USER_AGENTS`, `SCRAPER_PROXIES` |
| analyzer | `OLLAMA_*`, `LLM_*` (kontekst, długość odpowiedzi, równoległość wsadów) |
| autoscaler | `ANALYZER_MAX_REPLICAS`, `ANALYZER_EXTRA_CPUS`, `ANALYZER_EXTRA_MEM_MB`, `AUTOSCALER_*` |
| ollama | `OLLAMA_NUM_PARALLEL`, `OLLAMA_MODELS_PULL`, `OLLAMA_KV_CACHE_TYPE` |
| api, web | `API_PORT`, `WEB_PORT`, `ALERT_*`, `MEDIA_PROXY_HOSTS` |
| postgres, seaweedfs | `POSTGRES_*`, `S3_*` |
| każdy serwis | limity zasobów `*_CPUS`, `*_MEM` |

Przepływ: `scheduler` zleca discover (FB/YT/WWW) do `q:ingest` i `recheck` znanych URL-i →
`scraper-worker` pobiera materiał (`q:render`), rozpoznaje podmioty z rejestru KNF, zapisuje
przypadek w casedb i zleca analizę do `q:gpu` → `analyzer` analizuje (Ollama), zapisuje finding,
dokument i `ChangeEvent` w Postgresie → `api` czyta je i wysyła alert WebSocket → `web` pokazuje.
Uproszczony launcher tylko dla FB (`scraper/scheduler_main.py`, `worker_main.py`) jest w obrazie,
ale compose go nie używa.

## Szybki start: caly stos jedną komendą

```
cd infra
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Startuje: Postgres+pgvector, Valkey, SeaweedFS (S3 z kluczami z `.env`), nginx z korpusem
demo, `casedb` (jednorazowo: migracje + rejestr KNF, kończy się kodem 0), `analyzer`
(worker `q:gpu`), `scraper-worker` (repliki wg `SCRAPER_WORKERS`, kolejki `q:ingest` + `q:render`)
`scheduler` (harmonogram z `services/scraper/schedule.yaml`) oraz `api` (FastAPI, `localhost:8000`)
i `web` (dashboard, `localhost:7090`), które czytają findingi zapisane przez analyzer.

Demo Modułu 1 bez internetu:

```
docker compose exec scheduler python -m scheduler --once     # zleca wszystkie zadania raz
docker compose exec postgres psql -U investwatch -d investwatch \
  -c "select source,url,status,seen_count from cases"
docker compose exec postgres psql -U investwatch -d investwatch -c "select * from module1_report"
docker compose run --rm casedb report module1 --format csv -o /data/modul1.csv   # -> data/casedb/
```

Strony `www` pochodzą z nginx (`http://nginx/www/...`), Facebook przy braku sieci przechodzi na
korpus `fixtures/demo-ads/facebook` (`FB_MODE=auto`, montowany do kontenera), YouTube wymaga
internetu (błędy sieci kończą pojedyncze zadanie, nie worker). Powtórne `--once` daje wynik
`unchanged` i `seen_count` + 1, bez nowego findingu. Harmonogram wraca do normalnego rytmu sam;
zadania wyłączasz zmienną `SCHEDULE_DISABLE`.

Same bazy (praca nad API i frontem):

```
docker compose up -d postgres valkey seaweedfs nginx
```

Dostajesz: Postgres+pgvector (`localhost:5432`), Valkey (`6379`), SeaweedFS S3 (`8333`,
klucze `S3_ACCESS_KEY`/`S3_SECRET_KEY` z `.env`) i korpus demo (`http://localhost:8080/`).
Schemat i rejestr KNF tworzy `casedb` (`docker compose run --rm casedb init`).

`api` i `web` są w compose bez profilu, więc zwykłe `docker compose up` je poda:
API na `localhost:${API_PORT}` (8000), dashboard na `localhost:${WEB_PORT}` (7090).
Tabele `documents` i `findings`, z których korzysta API, tworzy migracja casedb
(`002_modul1.sql`), więc `api` startuje po zakończeniu kontenera `casedb`.
Praca bez Dockera (SQLite + vite): `services/api/README.md`, `services/web/README.md`.

## Budowanie na kontrakcie bez uruchamiania analizy

`fixtures/contract-examples/finding.json` to gotowy, prawdziwy obiekt `Finding`
(a `facebook_ad_document.json` obok - `AdDocument`). Zasil nimi bazę i front jako
fixture. Analyzer zapisuje dokładnie ten kształt w tabeli `findings` (`ANALYZER_STORE=db`)
i przy `risk_level == "high"` wysyła `pg_notify('findings_high', <id>)` – API może tego
słuchać i rozsyłać WebSocket (przepływ: `docs/MODUL1-ARCHITEKTURA.md`). Modele Pydantic:
`services/analyzer/analyzer/contracts.py` - są zamrożone, nie zmieniaj.

## Trzy rzeczy krytyczne dla panelu kalibracji (nie upraszczać)

1. **`rule_results` zapisuj w CAŁOŚCI jako JSONB.** Front przelicza flagi lokalnie
   przy ruchu suwaka, bez requestu do modelu. Okrojenie pola zabija natychmiastowość.
2. **`risk_level == "high"` = sygnał do broadcastu WebSocket.** Progi liczy analyzer;
   API ich nie przelicza.
3. **`routing.reason` to zdanie po polsku POKAZYWANE nadzorcy**, nie pole techniczne.
   Nadzorca musi móc zakwestionować decyzję routingu.

Pokazuj też `coverage` (odsetek reguł, które udało się ocenić) obok score'u;
`not_applicable` to nie naruszenie.

## Metryki do panelu

Macierz pomyłek, precision/recall/F1 i krzywa FP/FN liczone są na zbiorze złotym:
`fixtures/gold/labels.json` (opis w `fixtures/gold/README.md`) przez
`services/analyzer/tools/evaluate.py` (czysto obliczeniowy, nie woła modelu).
Uruchomienie z `services/analyzer`: `./.venv/Scripts/python.exe tools/evaluate.py`.

## Ollama

Domyślnie Ollama działa w kontenerze `ollama` z GPU NVIDIA (Docker Desktop WSL2), modele
pobiera `ollama-pull`, a `analyzer` startuje dopiero po nich (pierwszy `up` pobiera ok. 6 GB).
Parametry serwera (`OLLAMA_NUM_PARALLEL`, `OLLAMA_KEEP_ALIVE` itd.) i lista modeli są w `.env`.
- Bez GPU (CPU, wolno): w `.env` dopisz `COMPOSE_FILE=docker-compose.yml:docker-compose.cpu.yml`.
- Ollama natywna na hoście: `COMPOSE_FILE=docker-compose.yml:docker-compose.native.yml` oraz
  `OLLAMA_BASE_URL=http://host.docker.internal:11434`; modele `ollama pull` na hoście.
- Bez wystawionego portu; do ręcznych komend: `docker compose exec ollama ollama list`.
Potrzebna tylko regułom LLM analyzera.
Limity zasobów kontenerów (`*_CPUS`, `*_MEM`) są w `.env`.

## Autoskaler analyzerów

- `autoscaler` (port 8090, tylko sieć compose) skaluje kontenery `analyzer` wg backlogu `q:gpu`; do Dockera idzie wyłącznie przez `docker-socket-proxy` w wewnętrznej sieci `scaler`.
- Panel operatora woła `GET/PUT /scaling` przez proxy API (autoscaler nie ma portu na hoście). PUT nie ma uwierzytelniania - dostęp tylko z sieci wewnętrznej.
- `docker compose up -d` resetuje `analyzer` do 1 kontenera (autoskaler dodaje klony ponownie wg backlogu).
- Nowe limity (cpus, memory_mb) dostają nowe klony; działające zachowują stare.

## Uwagi eksploatacyjne

- Dockerfile'e `analyzer` i `scraper` mają kontekst `services/` (obok kodu potrzebny pakiet `casedb`).
- Obraz scrapera bazuje na `mcr.microsoft.com/playwright/python:v1.65.2-noble` - tag musi
  odpowiadać wersji `playwright` w `services/scraper/requirements.txt`.
- SeaweedFS ma małe woluminy (128 MB, max 100), bo domyślne 30 GB nie mieszczą się na małym
  dysku (objaw: `no free volumes left`, PutObject -> InternalError).
- `init.sql` (tylko rozszerzenie `vector`) działa tylko na PUSTYM wolumenie Postgresa; schemat
  tworzą migracje casedb (tabela `casedb_migrations`), więc zmiana schematu = nowa migracja.
- Ollama jest potrzebna tylko regułom LLM analyzera; bez niej dostają `not_applicable` z powodem.
  W trybie natywnym na Linuksie Ollama musi słuchać na adresie dostępnym z kontenera
  (`OLLAMA_HOST=0.0.0.0`).
- Analyzer wysyła do `http://api:8000` tylko w trybie `ANALYZER_STORE=api`; compose używa `db`.
- Wolne porty 5432, 6379, 8333, 8080, 8000, 7090 na hoście (port 3000 bywa zarezerwowany przez
  Hyper-V — `netsh interface ipv4 show excludedportrange protocol=tcp`).
- Montowanie `../fixtures/demo-ads` na Windows wymaga udostępnienia dysku w Docker Desktop.
