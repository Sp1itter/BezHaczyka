# InvestWatch

Monitoring reklam inwestycyjnych pod kątem wymogów nadzorczych (zadanie UKNF, HackNation 2026).
Scraper zbiera materiały, analyzer (Bielik przez Ollamę) ocenia je regułami, API zapisuje
wyniki w Postgresie, a dashboard pokazuje je nadzorcy.

## Wymagania sprzętowe

| Zasób | Minimum |
|---|---|
| GPU | min. 8 GB VRAM (zalecane); bez GPU działa na CPU, wolno |
| RAM | 16 GB |
| Dysk | ok. 15 GB (modele Ollamy ~6,3 GB + obrazy Dockera ~3 GB) |
| Oprogramowanie | Docker Desktop z WSL2; Ollama natywnie na hoście (analiza) |

Postgres + pgvector działa w Dockerze (`pgvector/pgvector:pg16`), nie instaluj go osobno.
Python 3.12 i Node.js 20 potrzebne tylko do pracy nad kodem poza kontenerami.

Modele (na hoście, raz):

```
ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
ollama pull bge-m3
```

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
  i zmień port w `infra/.env` na spoza zakresów. Dlatego dashboard jest na 8090, nie na 3000.
- Wirtualizacja musi być włączona w BIOS/UEFI (Menedżer zadań → Wydajność → CPU → „Wirtualizacja: Włączone”).

## Uruchomienie

```
cd infra
cp .env.example .env
docker compose up -d --build
```

Po ok. 3–5 min findingi pojawiają się na http://localhost:8090. Domyślnie `FB_MODE=replay`:
scheduler odtwarza offline korpus FB (bez internetu). `FB_MODE=auto` włącza żywe Ad Library.

| Usługa | Adres |
|---|---|
| Dashboard | http://localhost:8090 |
| API (FastAPI, `/docs`) | http://localhost:8000/docs |
| Korpus demo | http://localhost:8080 |
| Postgres | `localhost:5432` (dane w `infra/.env`) |
| S3 (SeaweedFS) | http://localhost:8333 |

Status i logi: `docker compose ps`, `docker compose logs -f analyzer`.
Schemat bazy tworzy `infra/init.sql` tylko na pustym wolumenie. Opcjonalnie dane przykładowe:
`docker compose exec api python -m api.seed --dir /data/contract-examples`.
Bez Ollamy na hoście:
1. w `infra/.env` ustaw `OLLAMA_BASE_URL=http://ollama:11434`,
2. `docker compose --profile ollama up -d --build`,
3. `docker compose exec ollama ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0` oraz `docker compose exec ollama ollama pull bge-m3`.
Opis serwisów: `infra/README.md`.

## Po `git pull`

Komendy z katalogu `infra/`.

| Zmieniło się | Komenda |
|---|---|
| `services/<x>/**` | `docker compose up -d --build <x>` (scraper = `scraper-ingest scraper-render scheduler`) |
| `infra/docker-compose.yml` | `docker compose up -d --build --remove-orphans` |
| `infra/.env.example` | porównaj ze swoim `.env`, dopisz nowe zmienne, potem `docker compose up -d` |
| `infra/init.sql` | `docker compose down -v`, potem `docker compose up -d --build` (**UWAGA: kasuje dane**) |
| `services/casedb/casedb/migrations/**` | `docker compose up -d --build casedb` (migracje przyrostowe, dane zostają) |
| nie wiesz | `docker compose up -d --build` (przebuduje tylko zmienione) |

Praca nad UI z hot reload: `cd services/web && npm ci && npm run dev` (Vite :5173, API z Dockera :8000, CORS ustawiony).

## Struktura

| Katalog | Co | Dokumentacja |
|---|---|---|
| `services/scraper` | zbieranie reklam (Facebook, YouTube), RenderProbe, reguły DET | `services/scraper/README.md` |
| `services/analyzer` | brama zakresu, router modułów, reguły LLM i hybrydowe, scoring | `services/analyzer/README.md` |
| `services/casedb` | wspólna baza przypadków YT/FB/WWW | `services/casedb/README.md` |
| `services/api` | FastAPI: dokumenty, ustalenia, alerty WebSocket | `services/api/README.md` |
| `services/web` | dashboard: ustalenia, przegląd, panel kalibracji | `services/web/README.md` |
| `infra` | docker-compose, schemat bazy | `infra/README.md` |
| `docs` | integracja serwisów, stan projektu, design | `docs/INTEGRACJA.md`, `docs/STAN-PROJEKTU.md` |

Zgodność z wymogami technicznymi konkursu (on-premise, licencje, sekrety, wersje):

```
python tools/check_compliance.py
```
