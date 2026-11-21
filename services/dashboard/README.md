# dashboard

Panel nadzorcy InvestWatch wzorowany na konsolach SOC: React + Vite + Recharts, alerty na żywo przez WebSocket.
Czyta z `services/api` (Postgres). Serwer mock (Node) służy do pracy bez bazy.

## Uruchomienie (Docker)

Z katalogu `infra/`:

```
docker compose up -d --build dashboard
```

Panel: http://127.0.0.1:7080 (`DASHBOARD_PORT`). Kontener `dashboard` (nginx) przekazuje `/api` i `/ws`
do `DASHBOARD_API_UPSTREAM`, domyślnie `http://api:8000`. Na mocku: `docker compose --profile mock up -d dashboard-mock`
i `DASHBOARD_API_UPSTREAM=http://dashboard-mock:4000`. `DASHBOARD_BIND=0.0.0.0` udostępnia panel w sieci lokalnej.

## Uruchomienie (dev)

```
cd services/dashboard
npm install
npm run dev      # mock API :4000 + panel http://127.0.0.1:5180
npm test         # logika kalibracji
```

Zmienne: `WEB_PORT` (5180), `MOCK_PORT` (4000), `MOCK_ALERT_MS` (co ile nowy rekord, 25000),
`API_URL` (dokąd Vite przekazuje `/api` i `/ws`; np. `http://127.0.0.1:8000` dla API z Dockera).

## Widoki

- Dashboard: kafelki, trend incydentów w czasie, rozkład ryzyka, źródła, modułu, statusu, top reguł.
- Wyniki: histogram + tabela, filtry daty, źródła, ryzyka, modułu, statusu, wyszukiwarka; szczegóły w panelu bocznym.
- Alerty: kolejka wysokiego ryzyka do obsłużenia + strumień na żywo; zmiana statusu i przypisania.
- Weryfikacja: rekordy z wynikiem ≥ progu z Kalibracji czekają na ocenę człowieka (lista etykiet TP/FP/błędy + notatka),
  „Zajmuję się” / „Przejmij” / „Zwolnij” zapisuje, kto pracuje nad alertem; panel feedbacku zlicza etykiety.
  Model tylko podpowiada status i osobę (`ai_suggestion`). Statusy „Potwierdzone” i „Odrzucone” ustawia wyłącznie człowiek,
  a przypisanie zrobione przez AI jest oznaczone i wymaga zatwierdzenia.
- Kalibracja: suwak progu, FP/FN, precyzja, pełność, F1, macierz pomyłek, wykres w funkcji progu.

## Punkty połączenia z bazą

Komponenty nie wołają API bezpośrednio: wszystko idzie przez `src/api/client.js` i `src/api/socket.js`.
Panel korzysta tylko z endpointów, które ma `services/api`; filtry, statystyki i trend liczy w przeglądarce
(`src/lib/query.js`) z `GET /findings?limit=500`.
Znaczniki `[DB-n]` są w `mock-server/server.js` i `src/api/client.js`.

| | Endpoint | Źródło w bazie |
|---|---|---|
| DB-1 | `GET /api/findings` | `findings` JOIN `documents` (jest w services/api) |
| DB-2 | `GET /api/findings/:id` | jw. |
| DB-3 | `PATCH /api/findings/:id` `{status}`, `{assignee, actor}`, `{review: {label, note}, actor}` | `findings.assignee/assigned_by/assigned_at`, `review_verdict/label/note`, `reviewed_by/at` (migracja casedb `011_review.sql`) |
| DB-4 | statystyki | liczone lokalnie z DB-1 |
| DB-5 | trend w czasie | liczony lokalnie z DB-1 (przy dużej skali: `GROUP BY dzień, risk_level`) |
| DB-6 | `GET /api/calibration` | `fixtures/gold/labels.json` (jest) |
| DB-7 | WS `/ws/alerts` `finding.high` | AlertHub w services/api |
| DB-8 | `GET /api/findings/:id/events` | `finding_events` (historia przypisań i ocen) |
| DB-9 | `GET /api/review-labels` | słownik etykiet ocen, `services/api/api/review.py` |

Ocena człowieka to etykieta (TP, FP, błędny podmiot, błędna reguła, zły poziom ryzyka, FN, poza zakresem, duplikat,
błąd danych, inny). Status `confirmed`/`dismissed` wynika z etykiety, a etykiety służą jako feedback do kalibracji.
