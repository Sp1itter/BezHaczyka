# api (stub GATE 1)

Minimalne API z `docs/INTEGRACJA.md`: scraper zapisuje dokument, worker analyzera go pobiera i odsyła Finding. Dane leżą w plikach JSON, Postgres przychodzi po GATE 1b.

## Start (PowerShell)

```powershell
cd services\api
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` wystawia stub w sieci lokalnej. Pozostałe serwisy ustawiają wtedy `API_BASE_URL=http://<IP-tej-maszyny>:8000`. Swoje IP sprawdzisz poleceniem `ipconfig` (pole „Adres IPv4”).

## Endpointy

| Metoda | Ścieżka | Wynik |
|---|---|---|
| POST | `/documents` | 201 `{"id": ...}`; wymaga pól `id`, `source`, `url` |
| GET | `/documents/{id}` | 200 z `AdDocument` albo 404 |
| POST | `/findings` | 201 `{"id": ...}`; wymaga `id` i `document_id` |
| GET | `/findings` | lista Findingów, najnowsze pierwsze |
| GET | `/health` | liczba zapisanych dokumentów i Findingów |

## Konfiguracja

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `API_DATA_DIR` | `services/api/data/` | katalog plików JSON (w `.gitignore`) |

## Testy

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
```
