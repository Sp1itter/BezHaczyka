# web (osoba C)

Jedyny panel analityka UKNF: React 18 + Vite + Recharts, ciemny motyw „BezHaczyka”.
Wszystkie dane z `services/api` (filtrowanie, stronicowanie i agregaty liczy serwer).

| Strona | Co robi | API |
|---|---|---|
| Przegląd | liczniki (przeanalizowane, wysokie ryzyko, czeka na decyzję), trend wykryć, podział wg źródła i poziomu ryzyka (kliknięcie otwiera Wyniki z filtrem), najczęściej łamane reguły | `/stats`, `/stats/trend?bucket=auto` |
| Alerty | na żywo przez WebSocket + otwarte sprawy wysokiego ryzyka; filtry: daty, moduł, status, źródło, szukaj | `/ws/alerts`, `/findings` |
| Wyniki | filtry (domyślnie rozwinięte): daty, źródło, ryzyko, moduł, status, szukaj; kolumna z numerami złamanych reguł; 50 na stronę; trend | `/findings?fields=list&limit=50&offset=`, `/stats/trend?bucket=auto` |
| Szczegóły | podgląd materiału (zrzut lub kadr) obok naruszeń (cytat, pomiar, art. 44), podmiot vs rejestr KNF, ocena człowieka („Potwierdź naruszenie”, „Fałszywy alarm”, pozostałe etykiety z listy), przypisanie, status, historia; URL materiału: kopiuj lub otwórz w nowej karcie; podsumowanie tylko, gdy napisał je model | `/findings/{id}`, `/findings/{id}/events`, `PATCH /findings/{id}` |
| Raport Modułu 1 | tabela podmiotów z eksportem CSV | `/reports/module1(.csv)` |
| Raport Modułu 2 | liczniki, najczęściej naruszane wymogi art. 44, najpoważniejsze przypadki (ryzyko wysokie i średnie) | `/stats?module=2`, `/findings?module=2` |
| Raport Modułu 3 | potwierdzone naruszenia reguły M3, a pod nimi kandydaci z trasy R3 (podmiot spoza rejestru KNF); wiersz prowadzi do szczegółów; eksport CSV | `/reports/module3(.csv)` |
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
