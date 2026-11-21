# analyzer — Moduł 2 (analiza AI)

Serwis Osoby B. Liczy 18 kryteriów UKNF (19 `rule_id` z 12a/12b):
reguły LLM (Bielik, 4 prompty wsadowe), hybrydowe 3 i 13, 10 (spójność języka)
oraz DET 4–8. Dla Facebooka wynik DET ze scrapera ma pierwszeństwo; dla innych
źródeł liczy je `rules_det_fallback.py` z `RenderProbe`, a bez niego
`det_placeholders.py` zwraca `not_applicable` z powodem.

## Quick Start

```bash
cd services/analyzer
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # Linux/macOS: .venv/bin/python
ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
ollama pull bge-m3
.venv/Scripts/python.exe -m pytest tests -q
```

Testy nie wymagają Ollamy; testy E2E Whispera i bazy są pomijane bez modelu/bazy. ffmpeg niepotrzebny (PyAV).

## Wymagania sprzętowe

RTX 3070 Ti Laptop (8 GB VRAM), 15,3 GB RAM. Bielik 4.5B Q8_0 ok. 5 GB VRAM, bge-m3
ok. 1,2 GB, Whisper na CPU. Pełna analiza dokumentu: ok. 15–25 s.

## Konfiguracja

Wzór: `.env.example` (`.env` nie trafia do gita).

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | adres Ollamy |
| `OLLAMA_MODEL` | `SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0` | model reguł |
| `OLLAMA_EMBED_MODEL` | `bge-m3` | embeddingi (1024 wymiary) |
| `OLLAMA_TEMPERATURE` | `0` | dekodowanie zachłanne; przy 0,1 ta sama reklama dawała różne werdykty |
| `OLLAMA_SEED` | `42` | stały seed, razem z temperaturą 0 daje powtarzalne werdykty |
| `WHISPER_MODEL` | `small` | faster-whisper, CPU int8 |
| `STT_ENABLED` | `1` | `0` wyłącza transkrypcję |
| `STT_MEDIA_ROOT`, `STT_MEDIA_CACHE`, `STT_MAX_MEDIA_MB` | -, -, `200` | katalog wideo, cache mediów, limit pliku |
| `SEAWEEDFS_S3_PUBLIC_URL` | puste | brama S3 dla `s3://`; puste = takie media pomijane |
| `DATABASE_URL` | - | Postgres casedb (`--db`); na Windows `127.0.0.1`, nie `localhost` |
| `FINDINGS_OUT_DIR` | puste | zapis `Finding` do JSON, gdy API nie działa |
| `API_BASE_URL`, `VALKEY_URL`, `PROFILE` | `http://api:8000`, `redis://valkey:6379/0`, `gpu8` | serwis api, kolejka RQ, profil sprzętowy |

## Mapa plików

| Plik | Co robi |
|---|---|
| `analyzer/contracts.py`, `pipeline.py` | zamrożone kontrakty; `analyze(doc)` -> `Finding` |
| `analyzer/scope_gate.py`, `router.py`, `scoring.py`, `llm.py`, `embeddings.py` | brama zakresu, R1–R4, `risk_score`, Ollama, bge-m3 |
| `analyzer/rules_llm/batch_1..4.py` + `prompts/batch_*.txt` | reguły 1,2,17,18 / 9,11 / 12a,12b,14 / 15,16 |
| `analyzer/rules_llm/guards.py` | strażnicy w kodzie dla reguł 2, 12a, 12b, 14, 16, 17 |
| `analyzer/rules_llm/preconditions.py`, `lang_consistency.py` | warunki wstępne reguł warunkowych; reguła 10 |
| `analyzer/rules_hybrid.py` | reguły 3 (geometria, czas, tekst, proporcje czcionek) i 13 |
| `analyzer/rules_det_fallback.py`, `det_placeholders.py` | DET 4–8 z `RenderProbe` / `not_applicable` |
| `analyzer/rules_llm/registry.py` | `default_config()`: potok produkcyjny (LLM, embeddingi, Whisper) |
| `analyzer/completeness.py` | wykrywanie materiału częściowego |
| `analyzer/stt.py`, `media_fetch.py` | Whisper; media: ścieżka, http(s), `s3://` |
| `analyzer/worker.py` | worker RQ na `q:gpu`; magazyn `ANALYZER_STORE=db|api` |
| `analyzer/db_store.py`, `change_detect.py` | zapis do casedb (Moduł 1), wykrywanie zmian między przebiegami |
| `analyzer/casedb_adapter.py`, `casedb_bridge.py` | przypadek <-> `AdDocument`/`Finding`, claim i upsert |
| `tools/casedb_batch.py` | analiza przypadków casedb |
| `tools/eval_rules.py` | ewaluacja per reguła (`fixtures/module2-cases/`) |
| `tools/evaluate.py`, `score_corpus.py`, `smoke_*.py` | zbiór złoty `fixtures/gold/` (8 reklam FB), smoke testy |

## Uruchomienie

Wszystkie komendy z `services/analyzer`.

Worker RQ (payload: `{document_id}`, `{document: ...}` albo płaski `AdDocument`, opcjonalnie `det_results`):

```bash
.venv/Scripts/python.exe -m analyzer.worker
```

Most casedb: tryb plikowy zapisuje `<case_id>.json` i `casedb_commands.txt` (komendy
`casedb ai-result`), tryb `--db` czyta i zapisuje wprost w bazie:

```bash
.venv/Scripts/python.exe tools/casedb_batch.py --in export.json --out DIR
.venv/Scripts/python.exe tools/casedb_batch.py --db --limit 10 --source youtube [--retry]
```

Smoke testy:

```bash
.venv/Scripts/python.exe tools/smoke_llm.py
.venv/Scripts/python.exe tools/smoke_stt.py fixtures/stt/ad_pl_risk_late.wav
```

Ewaluacja:

```bash
.venv/Scripts/python.exe tools/eval_rules.py [--rule 12a] [--offline] [--cases PLIK] [--out PLIK]
.venv/Scripts/python.exe tools/evaluate.py
.venv/Scripts/python.exe tools/score_corpus.py
```

## Integracja z bazą (casedb, Moduł 1)

Worker (`analyzer.worker.analyze_document`) bierze dokumenty i zapisuje wyniki
przez magazyn wybierany zmienną `ANALYZER_STORE`: `db` (`analyzer/db_store.py`,
pakiet `casedb`, połączenie z `DATABASE_URL`; domyślny, gdy `DATABASE_URL` jest
ustawione) albo `api` (`api_client.py`, serwis `services/api`).
Kontrakt zadania: `docs/MODUL1-ARCHITEKTURA.md` (payload `document_id`,
`entity_resolution`, `det_results`, `enqueued_at`; payload z całym `AdDocument`
jest nadal przyjmowany). Po analizie worker zapisuje Finding z migawką dokumentu
i wektorami, porównuje z poprzednim Findingiem (`change_detect.detect_change`)
i zapisuje `ChangeEvent`. Wyjątek analizy ustawia status sprawy `error` i jest
rzucany dalej (RQ oznacza job jako failed). W trybie `db` migawka trafia też do
tabeli `documents`, więc dashboard (`services/api` + `services/web`) widzi wyniki.

Obraz buduje się z katalogu `services/` (potrzebny pakiet `casedb`):
`docker build -f analyzer/Dockerfile -t investwatch-analyzer services/`.

## Zasady

- 18 reguł = 4 prompty wsadowe, nie 18 wywołań modelu na dokument (8 GB VRAM).
- `evidence` reguł LLM to dosłowny cytat, nigdy parafraza.
- Brak danych -> `not_applicable`, nigdy `fail`.
- Elementy obiektywne sprawdzają strażnicy w kodzie (`guards.py`): Bielik ignorował część poleceń promptu.
- Materiał częściowy (klipy napisów YouTube, `engine` z `:partial`): `fail` reguł
  „brak” (1, 2, 3, 11, 12a, 12b, 14, 15, 16) -> `not_applicable`.
- Whisper na CPU int8; GPU dla Bielika.
- Prompty w `prompts/*.txt`, nie w kodzie.
- Nie dotykamy `services/scraper/`, `services/api/`, `services/web/`, `services/casedb/`.

## Brama zakresu

Kryterium instrumentowe, nie aktywowe: w zakresie jest materiał z instrumentem finansowym
wg art. 2 ustawy o obrocie, bez względu na aktywo bazowe. CFD na kryptoaktywo zostaje
w zakresie (art. 2 ust. 1 pkt 2 lit. h); poza nim tylko zakup spot (MiCA).

## Weryfikacja cytatu

`batch_1.py` sprawdza, czy cytat modelu występuje w materiale. Dla reguł, gdzie `fail`
oznacza obecność (17, 18), brak cytatu obniża `confidence` do 40% i dodaje adnotację
w `summary`. Dla reguł, gdzie `fail` oznacza brak (`FAIL_MEANS_ABSENCE`), brak cytatu
jest poprawny. Nowa reguła musi zadeklarować, którego rodzaju jest.
