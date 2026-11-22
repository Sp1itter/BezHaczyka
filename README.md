# InvestWatch

Monitoring reklam usług inwestycyjnych w sieci dla UKNF. Scrapery (Facebook Ad Library,
YouTube, WWW) zbierają materiały, resolver dopasowuje je do rejestru firm inwestycyjnych KNF,
a analyzer (Bielik przez Ollamę) ocenia informację o ryzyku. Wyniki pokazuje nadzorcy
dashboard (`services/web`) przez API (`services/api`). Wszystko działa on-premise
i na otwartym oprogramowaniu.

## Quick Start

```
cd infra
cp .env.example .env
docker compose up -d --build
```

Po ok. 3–5 min findingi pojawiają się na dashboardzie. Domyślnie `FB_MODE=auto`: Facebook na żywo,
a bez sieci korpus offline `fixtures/demo-ads/facebook` (`FB_MODE=replay` = tylko korpus).

| Usługa | Adres |
|---|---|
| Dashboard | http://localhost:7090 |
| API (FastAPI, `/docs`) | http://localhost:8000/docs |
| Korpus demo | http://localhost:8080 |
| Postgres | `localhost:5432` (dane logowania w `infra/.env`) |
| S3 (SeaweedFS) | http://localhost:8333 |

Status i logi: `docker compose ps`, `docker compose logs -f analyzer`.
Schemat bazy tworzą migracje `casedb` (kontener `casedb` przy każdym starcie stosu, przyrostowo).
`infra/init.sql` włącza tylko rozszerzenie `vector`. Same bazy, bez budowania serwisów:
`docker compose up -d postgres valkey seaweedfs nginx`.

Demo Modułu 1 bez czekania na harmonogram (z katalogu `infra/`):

```
docker compose exec scheduler python -m scheduler --once
docker compose run --rm casedb report module1 --format csv -o /data/modul1.csv   # -> data/casedb/modul1.csv
```

Przykładowe dane dla dashboardu (z `fixtures/contract-examples`):
`docker compose exec api python -m api.seed --dir /data/contract-examples`.

### Ollama (LLM analyzera)

Domyślnie Ollama startuje w kontenerze z GPU NVIDIA, a `ollama-pull` sam pobiera modele
(`SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0`, `bge-m3`, `SpeakLeash/bielik-1.5b-v3.0-instruct:Q8_0`; pierwszy start ok. 6 GB).
Żadnych ręcznych kroków. Alternatywy (w `infra/.env`):
- bez GPU (CPU, wolno): `COMPOSE_FILE=docker-compose.yml:docker-compose.cpu.yml`,
- Ollama natywna na hoście: `COMPOSE_FILE=docker-compose.yml:docker-compose.native.yml` i
  `OLLAMA_BASE_URL=http://host.docker.internal:11434` (modele: `ollama pull` na hoście).

Bez działającej Ollamy analyzer nadal pracuje, a reguły LLM dostają `not_applicable`.

## Po `git pull`

Komendy z katalogu `infra/`.

| Zmieniło się | Komenda |
|---|---|
| `services/<x>/**` | `docker compose up -d --build <x>` (scraper = `scraper-worker scheduler`) |
| `infra/docker-compose.yml` | `docker compose up -d --build --remove-orphans` |
| `infra/.env.example` | porównaj ze swoim `.env`, dopisz nowe zmienne, potem `docker compose up -d`. Ollama: w `.env` ustaw `OLLAMA_BASE_URL=http://ollama:11434` albo dopisz `COMPOSE_FILE=docker-compose.yml:docker-compose.native.yml` (Ollama natywna) / `COMPOSE_FILE=docker-compose.yml:docker-compose.cpu.yml` (bez NVIDIA). Maszyna bez GPU bez nakładki cpu nie uruchomi `ollama` |
| `services/casedb/casedb/migrations/**` | `docker compose up -d --build casedb` (migracje przyrostowe, dane zostają) |
| `infra/init.sql` | dotyczy tylko pustego wolumenu; schemat zmieniają migracje casedb, `down -v` niepotrzebne |
| nie wiesz | `docker compose up -d --build --remove-orphans` (przebuduje tylko zmienione) |

Praca nad UI z hot reload: `cd services/web && npm ci && npm run dev` (Vite :5173, API z Dockera :8000, CORS ustawiony).

## Wymagania

| Zasób | Minimum |
|---|---|
| GPU | NVIDIA, min. 8 GB VRAM (profil `gpu8`), sterownik z obsługą WSL2; bez GPU: nakładka CPU (wolno) |
| RAM | 8 GB bez Ollamy, 16 GB z Ollamą |
| Dysk | ok. 17 GB (modele Ollamy ~6,3 GB + obrazy Dockera, w tym Chromium) |
| Oprogramowanie | Docker Desktop z WSL2 i wsparciem GPU NVIDIA (Compose v2.24+); Ollama działa w kontenerze |

| Narzędzie | Po co | Obowiązkowe |
|---|---|---|
| **Docker Desktop** (z WSL2 na Windows) | cały stos: Postgres, Valkey, SeaweedFS, casedb, scraper, scheduler, analyzer, api, web | **tak** |
| **PostgreSQL 16 + pgvector** | baza przypadków, dokumentów i ustaleń (schemat: migracje `services/casedb`) — działa **w Dockerze**, obraz `pgvector/pgvector:pg16`, nie instaluj go osobno | **tak** (przez Docker) |
| Ollama | modele dla analyzera (Bielik, bge-m3); domyślnie kontener z GPU, alternatywnie natywna | tylko do analizy |
| Python 3.12, Node.js 20 | praca nad kodem serwisów poza kontenerami | tylko dla deweloperów |

Modele pobiera kontener `ollama-pull` (ręcznie, tylko w trybie natywnym: `ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0`, `ollama pull bge-m3`).

### Instalacja Dockera na Windows

Uruchom w PowerShell **jako administrator**:

```
dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
winget install --id Docker.DockerDesktop -e --source winget
```

Potem **restart komputera**, a po restarcie, znowu jako administrator:

```
wsl --update
```

Uruchom Docker Desktop (pierwszy start trwa ok. minuty) i sprawdź:

```
docker version
docker compose version
```

Znane problemy:
- `wsl --install` może zwrócić **403 (Zabroniony)** przy pobieraniu pakietu — dlatego funkcje
  włączamy przez `dism`, a WSL aktualizujemy po restarcie (`wsl --update`) albo instalujemy
  `winget install --id Microsoft.WSL -e`.
- Instalator WSL zwraca `Access is denied`, dopóki nie zrobisz restartu po `dism`.
- Docker Desktop wymaga członkostwa w grupie `docker-users` (instalator dodaje bieżącego
  użytkownika; po instalacji wyloguj się i zaloguj ponownie).
- `ports are not available ... forbidden by its access permissions` — Windows (Hyper-V/WSL)
  rezerwuje zakresy portów i blokuje bind. Sprawdź: `netsh interface ipv4 show excludedportrange protocol=tcp`
  i zmień port w `infra/.env` na spoza zakresów. Dlatego dashboard jest na 7090 (8090 i 3000 bywają zarezerwowane).
- Wirtualizacja musi być włączona w BIOS/UEFI (Menedżer zadań → Wydajność → CPU → „Wirtualizacja: Włączone”).

## Serwisy

| serwis | rola | konfiguracja |
|---|---|---|
| `postgres` | Postgres 16 + pgvector | `POSTGRES_*` |
| `valkey` | kolejki RQ (`q:ingest`, `q:render`, `q:gpu`) | – |
| `seaweedfs` | magazyn obiektów S3 (HTML, zrzuty, wideo) | `S3_*` |
| `casedb` | migracje i rejestr KNF, start jednorazowy; CLI raportów | [services/casedb](services/casedb/README.md) |
| `scheduler` | harmonogram źródeł i ponownych sprawdzeń | [schedule.yaml](services/scraper/schedule.yaml), `SCHEDULE_*` |
| `scraper-worker` | pobieranie, resolver KNF, zapis, zlecenie analizy | [services/scraper](services/scraper/README.md), `FB_*`, `SCRAPER_*` |
| `analyzer` | zakres, routing modułów, reguły, scoring, detekcja zmian | [services/analyzer](services/analyzer/README.md), `OLLAMA_*` |
| `api` | FastAPI: dokumenty, ustalenia, alerty WebSocket | [services/api](services/api/README.md), `API_PORT` |
| `web` | dashboard: ustalenia, przegląd, panel kalibracji | [services/web](services/web/README.md), `WEB_PORT` |
| `nginx` | korpus demo offline | `DEMO_CORPUS_PORT` |
| `ollama`, `ollama-pull` | Ollama z GPU NVIDIA + jednorazowe pobranie modeli | `infra/README.md` |

Wszystkie zmienne z opisami są w [infra/.env.example](infra/.env.example), a przepływ danych
w [docs/MODUL1-ARCHITEKTURA.md](docs/MODUL1-ARCHITEKTURA.md). Szczegóły stosu: [infra/README.md](infra/README.md).

## Struktura

| Katalog | Co | Dokumentacja |
|---|---|---|
| `services/scraper` | Moduł 1: źródła Facebook/YouTube/WWW, resolver KNF, harmonogram, RenderProbe, reguły DET | `services/scraper/README.md` |
| `services/analyzer` | brama zakresu, router modułów, reguły LLM i hybrydowe, scoring | `services/analyzer/README.md` |
| `services/casedb` | wspólna baza przypadków YT/FB/WWW, migracje schematu, rejestr KNF | `services/casedb/README.md` |
| `services/api` | FastAPI: dokumenty, ustalenia, alerty WebSocket | `services/api/README.md` |
| `services/web` | dashboard: ustalenia, przegląd, panel kalibracji | `services/web/README.md` |
| `infra` | docker-compose | `infra/README.md` |
| `docs` | integracja serwisów, stan projektu, design | `docs/INTEGRACJA.md`, `docs/MODUL1-ARCHITEKTURA.md`, `docs/STAN-PROJEKTU.md` |

Zgodność z wymogami technicznymi konkursu (on-premise, licencje, sekrety, wersje):

```
python tools/check_compliance.py
```

## Bezpieczeństwo łańcucha dostaw

Zależności są przypięte, a skan robi `sh tools/audit.sh` (pip-audit; wyniki w
[docs/SECURITY-AUDIT.md](docs/SECURITY-AUDIT.md)). Zgodność z wymogami (brak sekretów,
płatnych API i licencji AGPL/SSPL) sprawdza `python tools/check_compliance.py`.
Sekrety trzymamy wyłącznie w `infra/.env`.
