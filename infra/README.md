# infra - stos docker-compose (projekt `investwatch`)

Komendy uruchomienia, adresy i procedura „po git pull”: `README.md` w korzeniu repo.

## Serwisy

| Serwis | Rola | Start |
|---|---|---|
| postgres (`pgvector/pgvector:pg16`) | dokumenty, findingi, casedb | długotrwały |
| valkey | kolejki RQ, stan scrapera | długotrwały |
| seaweedfs | S3 :8333: zrzuty, mp4 | długotrwały |
| nginx | korpus demo offline :8080 | długotrwały |
| casedb | migracje casedb | jednorazowy |
| api | FastAPI :8000 | długotrwały |
| web | dashboard :8090 | długotrwały |
| analyzer | worker kolejki `q:gpu` | długotrwały |
| scraper-ingest | worker `q:ingest` (discover) | długotrwały, repliki |
| scraper-render | worker `q:render` (Playwright) | długotrwały, repliki |
| scheduler | rq-scheduler: CronJob scrapera | długotrwały |
| ollama | opcja bez natywnej Ollamy | tylko `--profile ollama` |

Przepływ: `scheduler` co `FB_REFRESH_MIN` zleca discover do `q:ingest` → `scraper-ingest` zleca
fetch do `q:render` → `scraper-render` buduje `AdDocument`, zapisuje zrzuty w SeaweedFS i zleca
analizę do `q:gpu` → `analyzer` robi `POST /documents`, analizuje (Ollama na hoście) i robi
`POST /findings` → `api` zapisuje i wysyła alert WebSocket → `web` pokazuje.
Praca bez Dockera (SQLite + vite): `services/api/README.md`, `services/web/README.md`.

## Budowanie na kontrakcie bez uruchamiania analizy

`fixtures/contract-examples/finding.json` to gotowy, prawdziwy obiekt `Finding`
(a `facebook_ad_document.json` obok - `AdDocument`). Zasil nimi bazę i front jako
fixture. Analyzer wysyła do Ciebie dokładnie ten kształt przez `POST /findings`
(szczegóły przepływu: `docs/INTEGRACJA.md`). Modele Pydantic:
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

Ollama NIE jest serwisem compose. Działa natywnie na hoście, a kontenery łączą się
przez `host.docker.internal:11434`. Potrzebna tylko osobie uruchamiającej analyzer.

## Do sprawdzenia przy pierwszym starcie (nic z tego nie było uruchomione)

- [x] `docker compose config` przechodzi bez błędów i ostrzeżeń o brakujących zmiennych.
- [x] `init.sql` się wykonał: `\dt` w psql pokazuje `documents`, `findings`, `authorized_entities`;
      `CREATE EXTENSION vector` nie padł. Pamiętaj: init działa tylko na PUSTYM wolumenie
      (po zmianie `docker compose down -v`).
- [x] Indeks ivfflat zbudował się na pustej tabeli; po załadowaniu danych rozważ `REINDEX`.
- [ ] Healthcheck SeaweedFS (`wget` na `:9333/cluster/status`) działa w tym obrazie; jeśli
      brak `wget`, popraw lub usuń healthcheck.
- [ ] Zapis i odczyt przez S3 na `localhost:8333` działa (tryb `server -s3`, bez
      uwierzytelniania - tylko dev).
- [ ] nginx serwuje `http://localhost:8080/` z `autoindex`; montowanie `../fixtures/demo-ads`
      działa na Windows (Docker Desktop, udostępnienie dysku).
- [ ] Obraz `analyzer` się buduje (`requirements.txt`, kontekst `../services/analyzer`).
- [ ] `/health` na 8081 w analyzerze odpowiada. Worker uruchamia ten serwer w wątku-demonie
      przed wejściem w pętlę kolejki, a zgodności portu z `health.HEALTH_PORT` pilnuje test
      `tests/test_spojnosc.py::TestPortHealth` — więc powinno działać od razu. Jeśli nie,
      sprawdź, czy port 8081 nie jest zajęty na hoście.
- [ ] `host.docker.internal:11434` osiągalny z kontenera (Linux: wymaga wpisu `extra_hosts`;
      Ollama musi słuchać na adresie dostępnym z kontenera, np. `OLLAMA_HOST=0.0.0.0`).
- [ ] Analyzer wysyła do `http://api:8000` - `api` jest już w compose; sprawdź `POST /findings` z workera.
- [x] `api` łączy się z Postgresem (`/health` zwraca `"db": true`, `"dialect": "postgresql"`); testy API przechodzą na Postgresie (`TEST_DATABASE_URL`).
- [x] Dashboard na `localhost:8090` łączy się z `/ws/alerts` przez nginx (pill „alerty na żywo”).
- [ ] Wolne porty 5432, 6379, 8333, 8080, 8000, 8090 na hoście (port 3000 bywa zarezerwowany przez Hyper-V — `netsh interface ipv4 show excludedportrange protocol=tcp`).
