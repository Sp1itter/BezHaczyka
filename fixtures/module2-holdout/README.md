# Zbiór kontrolny (held-out) Modułu 2 (SYNTETYCZNY)

Wszystkie materiały są SYNTETYCZNE: firmy ("Fikcyjne TFI Gamma S.A."), fundusze i adresy
(`example.invalid`) są wymyślone. To nie są prawdziwe reklamy.

## Cel

Niezależny zbiór do uczciwego pomiaru trafności reguł, na którym system NIE był strojony
(w odróżnieniu od `fixtures/module2-cases/`). 18 przypadków, 83 etykiety, tylko tekst
(bez `RenderProbe`, więc reguły 4-8 i 13 nie są tu oceniane).

## Zasady uczciwości

- Autor zbioru nie widział kodu reguł, promptów, guardów ani zbioru `module2-cases`;
  znał tylko kontrakty danych, format pliku i treść 18 kryteriów UKNF (art. 44 rozp. del. 2017/565).
- Etykiety nadano z treści przypadku i kryteriów PRZED uruchomieniem jakiegokolwiek modelu
  (uruchomiono wyłącznie `--offline` w celu walidacji formatu).
- Nie dopasowywać etykiet do wyników modelu. Zmiana dozwolona tylko dla etykiety obiektywnie
  błędnej wg kryterium i musi być jawnie opisana. Zbioru nie używać do strojenia reguł.
- Przypadki o niejednoznacznej ocenie (patrz niżej) warto interpretować ostrożnie.

## Format i uruchomienie

`cases.json`: `{"synthetic": true, "holdout": true, "cases": [{id, opis, expected, doc}]}`
(identycznie jak `module2-cases`). Z `services/analyzer`:

    ./.venv/Scripts/python.exe tools/eval_rules.py --cases ../../fixtures/module2-holdout/cases.json --offline
    ./.venv/Scripts/python.exe tools/eval_rules.py --cases ../../fixtures/module2-holdout/cases.json --out <plik>

Uwaga: bez `--out` narzędzie nadpisuje `fixtures/module2-cases/eval_results.json` — przy
pomiarze held-out podaj własne `--out`.

## Liczba etykiet per reguła

| reguła | razem | pass | fail | n/a |
|---|---|---|---|---|
| 1 | 17 | 15 | 2 | 0 |
| 2 | 16 | 14 | 2 | 0 |
| 3 | 12 | 4 | 3 | 5 |
| 9 | 3 | 2 | 1 | 0 |
| 10 | 6 | 4 | 1 | 1 |
| 11 | 3 | 1 | 1 | 1 |
| 12a | 5 | 2 | 3 | 0 |
| 12b | 4 | 1 | 3 | 0 |
| 14 | 5 | 2 | 3 | 0 |
| 15 | 4 | 1 | 2 | 1 |
| 16 | 2 | 1 | 1 | 0 |
| 17 | 3 | 2 | 1 | 0 |
| 18 | 3 | 1 | 2 | 0 |

## Przypadki graniczne w etykietowaniu

- hold-02: `#współpraca` bez słowa "reklama" uznane za NIEjednoznaczne oznaczenie (reguła 2 = fail).
- hold-08: "działamy pod ścisłym nadzorem KNF" jako argument bezpieczeństwa = 18 fail,
  ale bez sugestii aprobaty produktu = 17 pass.
- hold-16: "nie gwarantują takich wyników w przyszłości" uznane za wystarczające dla reguły 14.
- hold-06: pułapka (nadzór KNF z zastrzeżeniem o braku gwarancji i zatwierdzenia) = 17/18 pass.
