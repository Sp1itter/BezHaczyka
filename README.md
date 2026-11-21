# InvestWatch

Monitoring reklam inwestycyjnych pod kątem wymogów nadzorczych (zadanie UKNF, HackNation 2026).
Scraper zbiera materiały, analyzer (Bielik przez Ollamę) ocenia je regułami, API zapisuje
wyniki w Postgresie, a dashboard pokazuje je nadzorcy.

## Wymagania — bez tego projekt nie wystartuje

| Narzędzie | Po co | Obowiązkowe |
|---|---|---|
| **Docker Desktop** (z WSL2 na Windows) | cały stos: Postgres, Valkey, SeaweedFS, api, web, analyzer | **tak** |
| **PostgreSQL 16 + pgvector** | baza dokumentów i ustaleń (`infra/init.sql`) — działa **w Dockerze**, obraz `pgvector/pgvector:pg16`, nie instaluj go osobno | **tak** (przez Docker) |
| Ollama | modele dla analyzera (Bielik, bge-m3); działa natywnie na hoście, nie w Dockerze | tylko do analizy |
| Python 3.12, Node.js 20 | praca nad kodem serwisów poza kontenerami | tylko dla deweloperów |

Postgres jest wymagany: API zapisuje w nim dokumenty i ustalenia, a analyzer i casedb na nim
pracują. SQLite w `services/api` służy wyłącznie do testów i szybkiej pracy nad frontem.

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
- Wirtualizacja musi być włączona w BIOS/UEFI (Menedżer zadań → Wydajność → CPU → „Wirtualizacja: Włączone”).

## Uruchomienie

```
cd infra
cp .env.example .env
docker compose up --build
```

| Usługa | Adres |
|---|---|
| Dashboard | http://localhost:3000 |
| API (FastAPI, `/docs`) | http://localhost:8000 |
| Postgres | `localhost:5432` (dane logowania w `infra/.env`) |
| Korpus demo | http://localhost:8080 |

Schemat bazy tworzy `infra/init.sql` przy **pierwszym** starcie na pustym wolumenie.
Po zmianie schematu: `docker compose down -v` i ponowne `up`.

Same bazy, bez budowania serwisów: `docker compose up postgres valkey seaweedfs nginx`.

Przykładowe dane w bazie (z `fixtures/contract-examples`):

```
docker compose exec api python -m api.seed --dir /data/contract-examples
```

Analyzer potrzebuje Ollamy na hoście z pobranymi modelami — patrz `KOMENDY.txt`.

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
