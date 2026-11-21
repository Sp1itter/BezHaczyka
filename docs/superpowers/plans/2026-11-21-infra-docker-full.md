# Pełna infrastruktura w Dockerze — projekt i plan

**Cel:** `cd infra && cp .env.example .env && docker compose up -d --build` stawia CAŁY system
(zbieranie → analiza → API → dashboard) i po kilku minutach na dashboardzie są prawdziwe
findingi z korpusu FB. Zespół pracuje dalej na tym stosie (UI i scraper rozwijane równolegle).

## Spec (wiążący)

Wymagania z `DocsTaskINWESTWATCH/Opis Wyzwania` par. 3 i 5:
- kolejka zadań open source (RQ na Valkey), CronJob/orchestrator dla scraperów,
- baza metadanych SQL (Postgres) + magazyn obiektów (SeaweedFS S3),
- uruchomienie całego stosu on-premise jedną komendą, Docker + Compose,
- wyłącznie darmowe modele (Ollama), bez płatnych API, sekrety tylko w `.env`.

### Docelowa topologia (`infra/docker-compose.yml`, projekt `investwatch`)

| Serwis | Obraz | Rola | Start |
|---|---|---|---|
| postgres | pgvector/pgvector:pg16 | dokumenty, findingi, casedb | długotrwały |
| valkey | valkey/valkey:8-alpine | kolejki RQ, stan scrapera | długotrwały |
| seaweedfs | chrislusf/seaweedfs:3.68 | S3: zrzuty, mp4 | długotrwały |
| nginx | nginx:1.27-alpine | korpus demo offline :8080 | długotrwały |
| casedb | build services/casedb | migracje casedb | jednorazowy |
| api | build services/api | FastAPI :8000 | długotrwały |
| web | build services/web | dashboard :8090 | długotrwały |
| analyzer | build services/analyzer | worker `q:gpu` | długotrwały |
| scraper-ingest | build services/scraper | worker `q:ingest` (discover) | długotrwały, repliki |
| scraper-render | ten sam obraz | worker `q:render` (Playwright fetch) | długotrwały, repliki |
| scheduler | ten sam obraz | rq-scheduler: CronJob Modułu 1 | długotrwały |
| ollama | ollama/ollama (profil `ollama`) | opcja dla maszyn bez natywnej Ollamy | tylko z `--profile ollama` |

Przepływ: `scheduler` co `FB_REFRESH_MIN` wrzuca `jobs.discover_job(query)` do `q:ingest` →
`scraper-ingest` wrzuca `jobs.fetch_job(url)` do `q:render` → `scraper-render` buduje `AdDocument`,
zapisuje zrzuty/mp4 w SeaweedFS i wrzuca `analyzer.worker.analyze_document(payload)` do `q:gpu` →
`analyzer` robi `POST /documents` (upsert), analizuje (Ollama na hoście), robi `POST /findings` →
`api` zapisuje i wysyła alert WebSocket → `web` pokazuje.

Domyślnie `FB_MODE=replay` (korpus z `fixtures/demo-ads/facebook`, zero ruchu do Meta) — demo
nie zależy od Wi-Fi. `FB_MODE=auto` włącza żywe Ad Library z fallbackiem na korpus.

### Decyzje

- Ollama zostaje natywnie na hoście (GPU bez NVIDIA Container Toolkit); profil `ollama` jako opcja.
- Jeden obraz scrapera, trzy serwisy (różne `command`), kotwica YAML `x-scraper`.
- Brak skryptów `.sh` jako entrypointów: checkout na Windows zamienia LF na CRLF i psuje shebang.
  Launchery w Pythonie, CMD w formie exec.
- Sieć compose bez stałego `name:` (izolacja przy `-p`, np. do weryfikacji obok działającego stosu).

## Global Constraints

- Wersje przypięte: `==` w requirements, konkretny tag obrazu (nigdy `latest`).
  `python tools/check_compliance.py` musi kończyć się 5× `[OK  ]`.
- Licencje wyłącznie permisywne (MIT/BSD/Apache/PostgreSQL); każda nowa linia requirements
  z komentarzem licencji, jak istniejące.
- Obrazy własne: użytkownik nie-root, `python:3.12.7-slim-bookworm` jako baza Pythona.
- Porty publikowane wyłącznie na `127.0.0.1`.
- Sekrety tylko w `infra/.env` (gitignored); `infra/.env.example` ma wartości zastępcze.
- Nie zmieniać: `services/web/src/**`, `services/api/api/**`, `services/scraper/sources/**`,
  `services/scraper/render/**`, `services/scraper/jobs.py` (równolegle pracują nad nimi inne osoby).
- Komentarze krótkie, po polsku, bez ścian tekstu (wymóg „bez AI slop”).
- Venvy z zależnościami do testów już istnieją:
  `C:\Users\pawel\.claude\jobs\f7866bc7\tmp\venv-analyzer`, `...\venv-scraper`, `...\venv-api`
  (python: `<venv>\Scripts\python.exe`). Testy uruchamiać z katalogu serwisu: `python -m pytest -q`.
- Commit na zadanie, wiadomość w stylu repo (`feat(infra): ...`), zakończona linią
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

---

### Task 1: Analyzer zapisuje dokument w API przed findingiem

**Problem:** scraper przekazuje do `q:gpu` płaski `AdDocument`. `handle_job` robi tylko
`POST /findings`, a API odrzuca finding do nieznanego dokumentu kodem 409
(`services/api/api/main.py`, `post_finding`). Żaden finding ze scrapera nie trafia do bazy.

**Pliki:** `services/analyzer/analyzer/api_client.py`, `services/analyzer/analyzer/worker.py`,
testy w `services/analyzer/tests/` (rozszerz istniejące `test_api_client.py` / `test_worker.py`,
zachowując ich styl atrap).

**Wymagania:**
1. `ApiClient.post_document(doc: AdDocument) -> None`: `POST /documents`, body
   `doc.model_dump(mode="json")`. 200 i 201 = sukces. Inny status lub błąd sieci → `ApiError`
   (ten sam wzorzec co `post_finding`).
2. `handle_job`: gdy dokument przyszedł w payloadzie (kształt `"flat"` lub `"document"`),
   PRZED analizą wywołaj `api.post_document(doc)`. Przy `ApiError`: `log.error(...)` i `return None`
   (zadanie do ponowienia). Dla kształtu `"document_id"` nie wołaj (dokument już jest w API).
3. Testy: (a) flat → post_document wywołane przed post_finding; (b) document_id → post_document
   niewywołane; (c) ApiError z post_document → `None`, post_finding niewywołane;
   (d) `post_document` mapuje 201/200 na sukces, 500 na `ApiError`.
4. Cały zestaw testów analyzera przechodzi (obecnie 669 passed, 2 skipped).

---

### Task 2: Obraz scrapera, launchery workera i harmonogramu

**Pliki (nowe):** `services/scraper/Dockerfile`, `services/scraper/.dockerignore`,
`services/scraper/worker_main.py`, `services/scraper/scheduler_main.py`,
`services/scraper/tests/test_launchers.py`.
**Pliki (zmiana):** `services/scraper/requirements.txt`, `services/scraper/contracts.py`.

**Wymagania:**
1. `requirements.txt`: dopisz `rq-scheduler==0.14         # MIT — CronJob Modulu 1 (scheduler_main.py)`.
   Sprawdź w venv scrapera, że instaluje się z `rq==2.9.1` i `import rq_scheduler` działa.
2. `worker_main.py`: `python worker_main.py <kolejka> [<kolejka> ...]` uruchamia
   `rq.Worker` na podanych kolejkach, połączenie `Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))`,
   logging INFO. Bez argumentów → błąd argparse. Logika w funkcji `main(argv)`; importy rq/redis leniwe w `main`.
3. `scheduler_main.py`: `main()`:
   - `Scheduler(queue_name="q:ingest", connection=conn, interval=int(os.getenv("SCHEDULER_POLL_S", "10")))`,
   - anuluje wcześniej zarejestrowane zadania z `job.id` zaczynającym się od `"fb-discover-"`
     (`scheduler.get_jobs()` + `scheduler.cancel(job)`), żeby restart nie dublował CronJobów,
   - `n = jobs.schedule_facebook(scheduler)`; log liczby fraz; przy `n == 0` ostrzeżenie
     „FB_QUERIES puste — harmonogram nic nie uruchomi”,
   - `scheduler.run()`.
   Wydziel `register(scheduler) -> int` (anulowanie + rejestracja), żeby dało się testować bez Redisa.
4. Testy `test_launchers.py` (bez Redisa, atrapa schedulera): `register` anuluje tylko zadania
   `fb-discover-*`, rejestruje po jednym zadaniu na frazę z `FB_QUERIES` (monkeypatch env),
   zwraca liczbę fraz; `worker_main` bez argumentów kończy się `SystemExit`.
5. `contracts.py`: kopia kontraktów musi być identyczna z `services/analyzer/analyzer/contracts.py`
   — obecnie pada `tests/test_contracts.py::test_contract_copy_matches_analyzer`
   (brakuje m.in. `ChangeEvent`). Zsynchronizuj tak, by test przeszedł; nie zmieniaj pliku analyzera.
6. `Dockerfile`:
   - `FROM python:3.12.7-slim-bookworm`, `ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`,
   - `pip install -r requirements.txt`, potem `python -m playwright install --with-deps chromium`,
   - użytkownik `scraper` uid/gid 10003, bez shella; `/app/data` zapisywalny przez niego,
   - `COPY` tylko kodu runtime: `*.py` z katalogu głównego serwisu (bez `record_fb_fixtures.py` może zostać — nie szkodzi), `sources/`, `render/`; bez `tests/`, `youtube/`, `.venv`,
   - `WORKDIR /app`, `USER scraper`, `CMD ["python", "worker_main.py", "q:ingest"]`.
   `.dockerignore`: `.venv`, `__pycache__`, `tests`, `youtube`, `data`, `*.pyc`, `.pytest_cache`.
7. Weryfikacja: `docker build -t iw-scraper-test services/scraper` przechodzi, a
   `docker run --rm iw-scraper-test python -c "import jobs, worker_main, scheduler_main, rq_scheduler; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); print('chromium ok'); b.close(); p.stop()"`
   wypisuje `chromium ok`. Usuń obraz testowy po weryfikacji. Testy scrapera: 0 failed.

---

### Task 3: Compose — wszystkie serwisy, `.env.example`

**Pliki:** `infra/docker-compose.yml`, `infra/.env.example`.

**Wymagania:**
1. Nagłówek compose: usuń „UWAGA: ten plik jest NIEPRZETESTOWANY” i nieaktualne warianty
   uruchomienia; zostaw krótko: `cp .env.example .env` → `docker compose up -d --build`;
   profil `ollama` opcjonalny. Usuń `--profile full` (nie istnieje).
2. Sieć: `networks: investwatch: {}` bez klucza `name:`.
3. Kotwica `x-scraper` (build `../services/scraper`, `env_file: .env`, `restart: unless-stopped`,
   `depends_on` valkey i seaweedfs `service_healthy`, sieć `investwatch`, wolumen
   `../fixtures/demo-ads:/app/fixtures/demo-ads:ro`, `shm_size: "1gb"`) i environment:
   ```
   VALKEY_URL: redis://valkey:6379/0
   S3_ENDPOINT: http://seaweedfs:8333
   S3_ACCESS_KEY: ${S3_ACCESS_KEY}
   S3_SECRET_KEY: ${S3_SECRET_KEY}
   FB_FIXTURES_DIR: /app/fixtures/demo-ads/facebook
   SCRAPER_OUTPUT_QUEUE: q:gpu
   SCRAPER_OUTPUT_FUNC: analyzer.worker.analyze_document
   ```
   Serwisy na kotwicy:
   - `scraper-ingest`: `command: ["python", "worker_main.py", "q:ingest"]`, `deploy.replicas: ${SCRAPER_INGEST_WORKERS:-2}`,
   - `scraper-render`: `command: ["python", "worker_main.py", "q:render"]`, `deploy.replicas: ${SCRAPER_RENDER_WORKERS:-1}`,
   - `scheduler`: `command: ["python", "scheduler_main.py"]` (bez replik).
   Obraz budowany raz: nadaj kotwicy `image: investwatch-scraper:local` i `build` tylko w kotwicy
   (compose zbuduje jeden obraz; sprawdź `docker compose config`, że trzy serwisy mają ten sam obraz).
4. `analyzer`: `restart: unless-stopped`, `depends_on` dodatkowo `api: condition: service_healthy`.
5. `api`, `web`: `restart: unless-stopped`; `web.depends_on.api.condition: service_healthy`.
6. Profil `ollama`: serwis `ollama`, `image: ollama/ollama:0.5.4`, `profiles: ["ollama"]`,
   wolumen `ollamadata:/root/.ollama`, bez publikowania portu, sieć `investwatch`. W `.env.example`
   komentarz: przy tym profilu ustaw `OLLAMA_BASE_URL=http://ollama:11434` i pobierz modele
   `docker compose exec ollama ollama pull <model>`.
7. `.env.example` — dopisz (z krótkimi komentarzami):
   ```
   S3_ACCESS_KEY=zmien-mnie
   S3_SECRET_KEY=zmien-mnie-tez
   FB_MODE=replay
   FB_QUERIES=inwestycje;zarabiaj na gieldzie
   FB_REFRESH_MIN=30
   FB_MAX_ADS_PER_RUN=25
   SCRAPER_USER_AGENTS=
   SCRAPER_PROXY=
   SCRAPER_INGEST_WORKERS=2
   SCRAPER_RENDER_WORKERS=1
   SCHEDULER_POLL_S=10
   ```
   i zmień `WHISPER_MODEL=medium` na `WHISPER_MODEL=small` (CPU int8; tak mierzono w docs/STAN-PROJEKTU.md).
8. Weryfikacja: `docker compose --env-file .env.example config -q` bez błędów (z katalogu `infra/`,
   tymczasowo skopiuj `.env.example` do `.env` jeśli compose tego wymaga i USUŃ go po sprawdzeniu),
   `python tools/check_compliance.py` 5× OK. Nie uruchamiaj `up` (zrobi to kontroler).

---

### Task 4: Dokumentacja uruchomienia i instrukcja „po git pull” dla czatów

**Pliki:** `README.md`, `infra/README.md`, `CLAUDE.md`.

**Wymagania:**
1. `README.md` sekcja „Uruchomienie”: jedna komenda (`cd infra`, `cp .env.example .env`,
   `docker compose up -d --build`), co zobaczyć po ok. 3–5 min (findingi na http://localhost:8090),
   tabela usług z adresami (dashboard 8090, API 8000/docs, korpus 8080, Postgres 5432, S3 8333),
   `docker compose ps` / `docker compose logs -f analyzer`. Usuń akapit o „Przykładowe dane w bazie”
   jako kroku obowiązkowym (zostaw jako opcję jednym zdaniem).
2. `README.md` nowa krótka sekcja „Wymagania sprzętowe”: tabela — GPU min. 8 GB VRAM (zalecane;
   bez GPU działa na CPU, wolno), RAM 16 GB, dysk ok. 15 GB (modele Ollamy ~6,3 GB + obrazy ~3 GB),
   Docker Desktop z WSL2. Modele: `ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0` i `ollama pull bge-m3`.
3. `README.md` sekcja „Po `git pull`”: tabela „zmieniło się → komenda”:
   - `services/<x>/**` → `docker compose up -d --build <serwisy x>` (scraper = `scraper-ingest scraper-render scheduler`),
   - `infra/docker-compose.yml` → `docker compose up -d --build --remove-orphans`,
   - `infra/.env.example` → porównaj ze swoim `.env` i dopisz nowe zmienne, potem `up -d`,
   - `infra/init.sql` lub migracje → `docker compose down -v && docker compose up -d --build` (UWAGA: kasuje dane),
   - nie wiesz → `docker compose up -d --build` (przebuduje tylko zmienione).
   Plus: praca nad UI z hot reload — `cd services/web && npm ci && npm run dev` (Vite :5173, API z Dockera :8000, CORS już ustawiony).
4. `infra/README.md`: usuń informacje, że serwisy „czekają na pierwsze uruchomienie”; opisz krótko
   serwisy z tabeli topologii (sekcja Spec w planie poniżej skopiowana w skrócie) i przepływ danych
   jednym akapitem; odeślij do README po komendy.
5. `CLAUDE.md`: nowa sekcja `## Docker (instrukcja dla czatów)` — zasady dla agentów:
   po `git pull` lub po własnej zmianie w `services/<x>` uruchom odpowiednią komendę z tabeli z README
   (powtórz tabelę zwięźle), sprawdź `docker compose ps` (wszystkie długotrwałe `running`/`healthy`),
   przy błędzie `docker compose logs --tail 100 <serwis>`; NIGDY `down -v` bez zgody człowieka (kasuje bazę);
   komendy z katalogu `infra/`; w Git Bash `MSYS_NO_PATHCONV=1` przed komendami z ścieżkami `/data/...`.
6. Zwięźle, bez lania wody. README ma pozostać krótki (wymóg „README ograniczony do niezbędnego minimum”).
