# dashboard

Panel nadzorcy InvestWatch wzorowany na konsolach SOC: React + Vite + Recharts, alerty przez Socket.io.
Na razie działa na serwerze mock (Node), bez bazy.

## Uruchomienie (Docker)

Z katalogu `infra/`:

```
docker compose up -d --build dashboard
```

Panel: http://127.0.0.1:7080 (`DASHBOARD_PORT`). Kontener `dashboard` (nginx) przekazuje `/api` i `/socket.io`
do `API_UPSTREAM`, domyślnie mock `dashboard-mock:4000`. Po podpięciu bazy: `API_UPSTREAM=http://api:8000`.

## Uruchomienie (dev)

```
cd services/dashboard
npm install
npm run dev      # mock API :4000 + panel http://127.0.0.1:5180
npm test         # logika kalibracji
```

Zmienne: `WEB_PORT` (5180), `MOCK_PORT` (4000), `MOCK_ALERT_MS` (co ile nowy rekord, 25000),
`API_URL` (dokąd Vite przekazuje `/api` i `/socket.io`).

## Widoki

- Dashboard: kafelki, trend incydentów w czasie, rozkład ryzyka, źródła, modułu, statusu, top reguł.
- Wyniki: histogram + tabela, filtry daty, źródła, ryzyka, modułu, statusu, wyszukiwarka; szczegóły w panelu bocznym.
- Alerty: kolejka wysokiego ryzyka do obsłużenia + strumień na żywo; zmiana statusu i przypisania.
- Weryfikacja: rekordy z wynikiem ≥ progu z Kalibracji czekają na decyzję człowieka (Potwierdź alert / Fałszywy alarm + notatka).
  Model tylko podpowiada status i osobę (`ai_suggestion`). Statusy „Potwierdzone” i „Odrzucone” ustawia wyłącznie człowiek,
  a przypisanie zrobione przez AI jest oznaczone i wymaga zatwierdzenia.
- Kalibracja: suwak progu, FP/FN, precyzja, pełność, F1, macierz pomyłek, wykres w funkcji progu.

## Punkty połączenia z bazą

Komponenty nie wołają API bezpośrednio: wszystko idzie przez `src/api/client.js` i `src/api/socket.js`.
Znaczniki `[DB-n]` są w `mock-server/server.js` i `src/api/client.js`.

| | Endpoint | Źródło w bazie |
|---|---|---|
| DB-1 | `GET /api/findings` | `findings` JOIN `documents` (jest w services/api) |
| DB-2 | `GET /api/findings/:id` | jw. |
| DB-3 | `PATCH /api/findings/:id` `{status}`, `{assignee, actor}`, `{review: {decision, note}, actor}` | `findings.status` (jest); brak kolumn: `assignee`, `assigned_by`, `ai_suggestion`, `reviewed_by`, `reviewed_at`, `review_note` |
| DB-4 | `GET /api/stats` | agregaty (jest, bez filtrów) |
| DB-5 | `GET /api/stats/trend` | `GROUP BY dzień, risk_level` (brak) |
| DB-6 | `GET /api/calibration` | `fixtures/gold/labels.json` (jest) |
| DB-7 | Socket.io `finding.high` | dziś natywny WS `/ws/alerts` w services/api |

Filtry `from`, `to`, `source` (lista), `module` (lista), `min_score` i `reviewed` trzeba dodać do `GET /findings` w services/api.
