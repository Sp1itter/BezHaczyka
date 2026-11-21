# infra - punkt startowy dla Osoby C (API + dashboard)

> **UWAGA: ten stos jest NIEPRZETESTOWANY.** Autor nie miał Dockera na swojej
> maszynie, więc `docker-compose.yml`, `init.sql` i `nginx.conf` nigdy nie zostały
> uruchomione. Sprawdzono tylko składnię YAML i zgodność licencyjną
> (`tools/check_compliance.py`). Lista rzeczy do sprawdzenia jest na końcu.

## Szybki start: same bazy

```
cd infra
cp .env.example .env
docker compose up postgres valkey seaweedfs nginx
```

To **wystarczy do zbudowania całego API i frontu**. Nie potrzebujesz analyzera,
Bielika, Ollamy ani pobierania 6,3 GB modeli. Dostajesz: Postgres+pgvector
(`localhost:5432`, schemat z `init.sql`), Valkey (`6379`), SeaweedFS S3 (`8333`)
i korpus demo jako statyczne pliki (`http://localhost:8080/`).

Gdy napiszesz `services/api` i `services/web` (każdy z `Dockerfile`), usuń linie
`profiles: ["full"]` w `docker-compose.yml` - wtedy zwykłe `docker compose up` je poda.
Przyjęte założenia: `api` słucha na 8000, `web` na 80, Dockerfile w `services/api` i `services/web`.

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

- [ ] `docker compose config` przechodzi bez błędów i ostrzeżeń o brakujących zmiennych.
- [ ] `init.sql` się wykonał: `\dt` w psql pokazuje `documents`, `findings`, `authorized_entities`;
      `CREATE EXTENSION vector` nie padł. Pamiętaj: init działa tylko na PUSTYM wolumenie
      (po zmianie `docker compose down -v`).
- [ ] Indeks ivfflat zbudował się na pustej tabeli; po załadowaniu danych rozważ `REINDEX`.
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
- [ ] Analyzer wysyła do `http://api:8000` - dopóki `api` jest w profilu `full`, to adres nieosiągalny.
- [ ] Wolne porty 5432, 6379, 8333, 8080, 8000, 3000 na hoście.
