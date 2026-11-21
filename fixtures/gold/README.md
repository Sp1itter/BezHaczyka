# Zbior zloty (gold set)

Recznie oznaczone materialy reklamowe, na ktorych liczymy trafnosc klasyfikacji
ryzyka i wplyw progu w panelu kalibracji. Plik: `labels.json` w tym katalogu.

## Jak dodac pozycje

Dopisz obiekt do listy `items`:

```json
{
  "id": "demo-011",
  "source": "fixtures/demo-ads/demo-011.html",
  "is_violation": true,
  "note": "krotki opis, dlaczego to naruszenie",
  "rule_labels": {"4": "fail"},
  "score": 62.5
}
```

- `id` musi byc unikalny w zbiorze.
- `source` to sciezka do materialu (HTML, wideo lub zrzut).
- `score` to `risk_score` zapisany przez analizator dla tego materialu. Bez niego
  pozycja jest w zbiorze, ale pomijana w metrykach.

## Co znaczy `is_violation`

`is_violation: true` oznacza, ze material wedlug czlowieka narusza wymogi
(co najmniej jedna regula). `false` oznacza material w porzadku. To etykieta na
poziomie dokumentu, wzgledem ktorej liczone sa TP, FP, FN i TN.

## `rule_labels` (opcjonalne)

Mapa `numer reguly -> "pass" | "fail"` dla pozycji, ktore maja oznaczenia per
regula. Pole jest opcjonalne i moze byc pominiete. Obecnie nie wplywa na metryki
panelu kalibracji, sluzy do analizy bledow per regula.

## Skad etykiety demo

Materialy z `fixtures/demo-ads/` piszemy sami, celowo lamiac konkretne reguly.
Ich etykiety znamy z konstrukcji, bo to my wpisalismy naruszenie, wiec nie wymagaja
recznego oznaczania. Pozostale pozycje (materialy prawdziwe) oznacza zespol recznie.
