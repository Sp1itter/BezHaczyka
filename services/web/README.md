# web (osoba C)

Dashboard nadzorcy: React + Vite + Recharts.

- **Ustalenia** — tabela z filtrami (ryzyko, moduł 1–3, status, źródło, score, szukanie),
  szczegóły: `routing.reason`, dowody reguł (cytat / pomiar / brak), pokrycie,
  podmioty i rejestr KNF (Moduły 1 i 3), decyzja nadzorcy (`PATCH status`).
  Suwak progu pewności przelicza `fail` → „do weryfikacji” lokalnie, bez requestu.
- **Przegląd** — kafelki, rozkład poziomów ryzyka, najczęściej naruszane reguły.
- **Kalibracja** — próg score na zbiorze złotym: macierz pomyłek, P/R/F1,
  wykres metryk w funkcji progu, tabela pozycji. Liczone w przeglądarce (`src/lib/metrics.js`).
- **Alerty** — WebSocket `/ws/alerts`, powiadomienie i odświeżenie tabeli przy nowym `high`.

## Uruchomienie (dev)

Najpierw API na `:8000` (patrz `services/api/README.md`), potem:

```
cd services/web
npm install
npm run dev        # http://127.0.0.1:5173, /api i /ws przez proxy do :8000
npm test           # testy logiki kalibracji (node --test)
npm run build      # dist/ dla obrazu nginx
```

Inny adres API: `API_URL=http://127.0.0.1:9000 npm run dev`.

W compose obraz `web` serwuje build przez nginx (nie-root, port 8080 w kontenerze,
`WEB_PORT` na hoście) i proxuje `/api` oraz `/ws` do serwisu `api`.

Bez zewnętrznych zasobów (fonty, CDN) — wymóg on-premise.
