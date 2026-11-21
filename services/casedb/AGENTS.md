# AGENTS.md - services/casedb

<!-- casedb-handoff v1 | autor: Claude (sesja Hacknation, 2026-11-21) | stan: dzialajacy, przetestowany -->

Notatka dla kolejnego modelu/agenta. Czytaj przed zmianami w tym katalogu.

## Rola
Wspolna baza przypadkow (case) dla scraperow YouTube, Facebook i WWW. Zrodlo danych
dla przyszlego modulu jobow, ktory rozdziela przypadki na endpointy modeli AI
i zapisuje wyniki z powrotem (`ai_results`).

## Kontrakt (nie zmieniaj bez uzgodnienia)
- `case_id` = `uuid5(NAMESPACE_URL, kanoniczny_url)`. Dla FB to samo co `AdDocument.id`,
  wiec `case_id == documents.id` (tabela osoby C w `infra/init.sql`, NIE ruszamy jej).
- Tabele: `cases` (metadane + `status` + `extra`/`raw` JSONB), `case_content`
  (kind: title|description|text|transcript|clip|comment|evidence), `case_assets`
  (kind: link|html|screenshot|video|audio|image, `uri` = `s3://...` lub `https://...`),
  `ai_results` (unikalne po case_id, task, model, version).
- Statusy: new -> queued -> processing -> done | error | skipped.
- Ksztalt eksportu: `{case_id, source, url, status, metadata, content{kind:[...]}, assets[], ai_results{task:[...]}}`.
  `metadata` zawiera WSZYSTKIE kolumny `cases` (takze dodane przez `add_column`) + `extra`.

## Gdzie co jest
- `casedb/migrations/NNN_*.sql` - schemat. Nowa zmiana = nowy plik z kolejnym numerem; nie edytuj starych.
- `casedb/store.py` - caly SQL (save_case, save_ai_result, add_column, set_columns, set_status, claim).
- `casedb/ingest.py` - mapowanie wynikow scraperow na `Case` (bez bazy).
- `casedb/export.py` - JSON dla modulu jobow.
- `casedb/cli.py` - `python -m casedb ...`.

## Dla modulu jobow (nastepny krok)
- Pobieranie pracy: `store.claim(conn, worker, limit, source=None)` - `FOR UPDATE SKIP LOCKED`,
  bezpieczne przy wielu workerach. Potem `export.export_cases(conn, ids)`.
- Wynik: `store.save_ai_result(...)` + `store.set_status(conn, case_id, "done"|"error", error)`.
- Pole wyniku jako prawdziwa kolumna: `store.add_column(conn, "cases", nazwa, typ)` + `store.set_columns(...)`.

## Zasady repo
- `tools/check_compliance.py` musi przechodzic (brak zewnetrznych hostow w kodzie, wersje `==`).
- Sekrety tylko w `.env`. Tylko open source / on-premise.
- Testy: `TEST_DATABASE_URL=... python -m pytest` (czysci tabele casedb w tej bazie!).
