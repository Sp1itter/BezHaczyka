# casedb

Jedyna warstwa danych stosu: przypadki ze scraperow YouTube, Facebook i WWW, rejestr KNF,
findings, change_events i widok `module1_report`. Postgres (z `pgvector`) + SeaweedFS/linki (pliki).
Instalacja jako pakiet: `pip install ./services/casedb`.

## Quick Start

```
cd infra
cp .env.example .env
docker compose up -d postgres
docker compose run --rm --build casedb init      # migracje + rejestr KNF (idempotentnie)
```

Pliki do wczytania wrzuc do `data/casedb/` w katalogu glownym repo (w kontenerze: `/data`).

```
docker compose run --rm casedb ingest youtube /data/wynik.json
docker compose run --rm casedb ingest facebook /data/fb.json
docker compose run --rm casedb export --status new -o /data/export.json
docker compose run --rm casedb export --claim router --limit 10
docker compose run --rm casedb load-registry /data/rejestr.csv   # domyslnie plik pakietowy
docker compose run --rm casedb report module1 --format csv -o /data/modul1.csv
docker compose run --rm casedb recheck-list --limit 20
docker compose run --rm casedb add-column cases risk_score "double precision"
docker compose run --rm casedb ai-result <case_id> --task scam --model bielik-4.5b /data/wynik_ai.json
```

Rejestr KNF: CSV UTF-8 `knf_id,name,type,country,register,aliases,domains,handles,source_url`
(listy rozdzielone `;`); pakietowy `casedb/data/knf_registry.csv` zawiera tylko przyklady.

## Rejestr KNF (snapshot)

`casedb/data/knf_snapshot.jsonl` to snapshot 10 wykazow KNF "Firmy inwestycyjne i Agenci firm
inwestycyjnych" (domy i banki maklerskie, notyfikacje ZFI, agenci, cofniete zezwolenia, dane
historyczne). Ladowanie do tabeli `knf_entities` i sprawdzenie nazwy:

```
docker compose run --rm --build casedb migrate
docker compose run --rm casedb load-knf
docker compose run --rm casedb knf-lookup "XTB S.A."
```

Odswiezenie snapshotu (z katalogu glownego repo, sama biblioteka standardowa):
`python tools/knf_snapshot.py`

## Konfiguracja

| Zmienna | Opis |
|---|---|
| `DATABASE_URL` | ustawiana w `infra/docker-compose.yml` z `POSTGRES_*` w `infra/.env` |

## Testy

```
python -m pip install ./ -r requirements-dev.txt
TEST_DATABASE_URL=postgresql://investwatch:<haslo>@127.0.0.1:5432/investwatch python -m pytest
```
Na Windows uzyj `127.0.0.1`, nie `localhost` (proba IPv6 `::1` spowalnia kazde polaczenie; testy 6,5 min zamiast 1 s).
Baza testowa musi miec `pgvector` (np. obraz `pgvector/pgvector:pg16`); testy bez `TEST_DATABASE_URL` pomijaja czesc bazodanowa.
Uwaga: testy czyszcza tabele casedb w podanej bazie.

## Wymagania
Docker z Compose v2. Bez GPU. Postgres ok. 100 MB RAM.

## Instrukcja krok po kroku (dla czlowieka, Windows)

1. Uruchom Docker Desktop i poczekaj, az bedzie gotowy.
2. Baza (PowerShell, z katalogu repo):
   ```
   cd infra
   copy .env.example .env
   docker compose up -d postgres
   docker compose run --rm --build casedb init
   ```
   Gdy port 5432 jest zajety, zmien `POSTGRES_PORT` w `infra/.env` (np. 5433).
3. Dane ze scrapera YouTube (prawdziwe pobieranie, ok. 2-5 min):
   ```
   cd services\scraper\youtube
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\python demo.py --limit 3 --output ..\..\..\data\casedb\yt.json
   ```
4. Dane Facebook: skopiuj przyklad kontraktu jako liste JSON (replay korpusu FB wymaga Chromium):
   ```
   python -c "import json;d=json.load(open('fixtures/contract-examples/facebook_ad_document.json',encoding='utf-8'));json.dump([d],open('data/casedb/fb.json','w',encoding='utf-8'),ensure_ascii=False)"
   ```
5. Wczytanie i eksport (z `infra/`):
   ```
   docker compose run --rm casedb ingest youtube /data/yt.json
   docker compose run --rm casedb ingest facebook /data/fb.json
   docker compose run --rm casedb export --status new -o /data/export.json
   ```
   Wynik: `data/casedb/export.json`. Ponowny ingest nie tworzy duplikatow.
6. Podglad bazy:
   ```
   docker compose exec postgres psql -U investwatch -d investwatch -c "select source, status, count(*) from cases group by 1,2"
   ```

W Git Bash dodaj `MSYS_NO_PATHCONV=1` przed komendami z `/data/...`, inaczej sciezka
zostanie zamieniona na windowsowa. Notatka dla modeli/agentow: `AGENTS.md`.
