# api (osoba C)

FastAPI: zapis dokumentów i ustaleń, odczyt dla dashboardu, alerty na żywo.
Przepływ między serwisami: [`docs/INTEGRACJA.md`](../../docs/INTEGRACJA.md).

## Quick start bez Dockera (SQLite)

```
cd services/api
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
./.venv/Scripts/python.exe -m api.seed            # przykłady z fixtures/contract-examples
./.venv/Scripts/python.exe -m uvicorn api.main:app --port 8000
```

Bez `DATABASE_URL` baza to `services/api/data/api-dev.sqlite`. W compose
`DATABASE_URL=postgresql://...` i tabele z `infra/init.sql`.

## Endpointy

| Metoda | Ścieżka | Kto woła | Uwagi |
|---|---|---|---|
| `POST` | `/documents` | scraper (A) | `AdDocument`; upsert: 201 nowy, 200 aktualizacja |
| `GET` | `/documents/{id}` | analyzer (B) | pełny `AdDocument` |
| `POST` | `/findings` | analyzer (B) | `Finding`; 409 gdy brak dokumentu; nowe `high` → broadcast WS |
| `GET` | `/findings` | web | filtry: `risk_level` (wielokrotny), `status`, `module`, `source`, `min_score`, `max_score`, `q`, `limit`, `offset` |
| `GET` | `/findings/{id}` | web | z podglądem dokumentu i `coverage` |
| `PATCH` | `/findings/{id}` | web | `{"status": "in_review" \| "confirmed" \| "dismissed" \| ...}` |
| `GET` | `/stats` | web | agregaty do wykresów |
| `GET` | `/calibration` | web | zbiór złoty (`fixtures/gold/labels.json`); progi liczy front |
| `WS` | `/ws/alerts` | web | `{"type": "finding.high", ...}` przy nowym lub eskalowanym `high` |
| `GET` | `/health` | compose | stan bazy |

Zasady z kontraktu, których API pilnuje:
- `rule_results` zapisywane w całości (panel kalibracji przelicza flagi lokalnie),
- API nie przelicza progów — `risk_level` liczy analyzer,
- `coverage` = odsetek reguł ocenionych; `not_applicable` to brak danych, nie naruszenie.

## Testy

```
./.venv/Scripts/python.exe -m pytest
```

Testy działają na SQLite w pamięci. `tests/test_contracts_copy.py` pilnuje, że
`api/contracts.py` jest identyczna z kopią analyzera.

**Niezweryfikowane:** `PostgresStore` (Postgres + pgvector) nie był uruchomiony —
w zespole nie było Dockera. SQL jest wspólny z SQLite poza filtrem modułu
(`= ANY(modules)`), JSONB i rzutowaniem `embedding` na `vector`.
