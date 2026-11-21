# casedb

Wspolna baza przypadkow ze scraperow YouTube, Facebook i WWW oraz wynikow AI.
Postgres (metadane i tresc) + SeaweedFS/linki (pliki).

## Quick Start

```
cd infra
cp .env.example .env
docker compose up -d postgres
docker compose run --rm --build casedb migrate
```

Pliki do wczytania wrzuc do `data/casedb/` w katalogu glownym repo (w kontenerze: `/data`).

```
docker compose run --rm casedb ingest youtube /data/wynik.json
docker compose run --rm casedb ingest facebook /data/fb.json
docker compose run --rm casedb export --status new -o /data/export.json
docker compose run --rm casedb export --claim router --limit 10
docker compose run --rm casedb add-column cases risk_score "double precision"
docker compose run --rm casedb ai-result <case_id> --task scam --model bielik-4.5b /data/wynik_ai.json
```

## Konfiguracja

| Zmienna | Opis |
|---|---|
| `DATABASE_URL` | ustawiana w `infra/docker-compose.yml` z `POSTGRES_*` w `infra/.env` |

## Testy

```
python -m pip install -r requirements-dev.txt
TEST_DATABASE_URL=postgresql://investwatch:<haslo>@127.0.0.1:5432/investwatch python -m pytest
```
Na Windows uzyj `127.0.0.1`, nie `localhost` (proba IPv6 `::1` spowalnia kazde polaczenie; testy 6,5 min zamiast 1 s).
Uwaga: testy czyszcza tabele casedb w podanej bazie.

## Wymagania
Docker z Compose v2. Bez GPU. Postgres ok. 100 MB RAM.
