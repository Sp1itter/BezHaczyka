# web (osoba C)

Jedyny panel analityka UKNF: React 18 + Vite + Recharts, ciemny motyw „BezHaczyka”.
Wszystkie dane z `services/api` (filtrowanie, stronicowanie i agregaty liczy serwer).

| Strona | Co robi | API |
|---|---|---|
| Przegląd | liczniki, kolejka weryfikacji (zrzut, decyzja), najczęściej łamane reguły, źródła, trend | `/stats`, `/stats/trend`, `/findings?fields=list` |
| Alerty | na żywo przez WebSocket + otwarte sprawy wysokiego ryzyka | `/ws/alerts`, `/findings` |
| Wyniki | filtry: daty, źródło, ryzyko, moduł, status, szukaj; 50 na stronę; trend | `/findings?fields=list&limit=50&offset=`, `/stats/trend` |
| Szczegóły | podsumowanie, naruszenia (cytat, art. 44), podmiot vs rejestr KNF, zrzut, decyzja, przypisanie, status, historia | `/findings/{id}`, `/findings/{id}/events`, `PATCH /findings/{id}` |
| Raport Modułu 1 / 3 | tabele z eksportem CSV | `/reports/module1(.csv)`, `/reports/module3(.csv)` |
| Kalibracja | suwak progu, macierz TP/FP/FN/TN, P/R/F1, wykres FP/FN, zapis progu | `/calibration`, `/settings/threshold` |
| Operator | kolejki, limity kontenerów analizy, workery (co 10 s) | `/ops/scaling` |

Bez odpytywania częściej niż co 10 s; alerty tylko przez WebSocket (ponowne łączenie co 3 s).

## Uruchomienie (dev)

```
cd services/web
npm install
npm run dev        # http://127.0.0.1:5173, /api i /ws przez proxy do API_URL (domyślnie :8000)
npm test           # testy logiki (node --test)
npm run build      # dist/ dla obrazu nginx
```

W compose obraz `web` serwuje build przez nginx (nie-root, port 8080) i proxuje `/api` oraz `/ws` do `api`.
