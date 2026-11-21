# Drugi zbiór kontrolny (held-out 2) Modułu 2 (SYNTETYCZNY)

Wszystkie materiały są SYNTETYCZNE: firmy ("Fikcyjny Dom Maklerski Omega S.A.", "Fikcyjne TFI Sigma S.A."),
fundusze i adresy (`example.invalid`) są wymyślone. To nie są prawdziwe reklamy.

## Cel

Drugi, niezależny od `module2-holdout/` i `module2-cases/` zbiór do pomiaru trafności reguł.
17 przypadków, 99 etykiet, tylko tekst (bez `RenderProbe`, więc reguły 4-8 i 13 nie są oceniane).
Inny styl niż typowy: długie landing page, krótkie posty z emoji, opisy podcastów i filmów,
maile, komentarze influencerów.

## Zasady uczciwości

- Autor zbioru nie widział kodu reguł, promptów ani innych zbiorów; znał tylko kontrakty danych,
  format pliku, zakres (scope gate) i treść 18 kryteriów UKNF (art. 44 rozp. del. 2017/565).
- Etykiety nadano z treści przypadku i kryteriów PRZED uruchomieniem jakiegokolwiek modelu
  (uruchomiono wyłącznie `--offline` w celu walidacji formatu).
- Nie dopasowywać etykiet do wyników modelu. Zmiana dozwolona tylko dla etykiety obiektywnie
  błędnej wg kryterium i musi być jawnie opisana. Zbioru nie używać do strojenia reguł.

## Format i uruchomienie

`cases.json`: `{"synthetic": true, "holdout": true, "cases": [{id, opis, expected, doc}]}`. Z `services/analyzer`:

    ./.venv/Scripts/python.exe tools/eval_rules.py --cases ../../fixtures/module2-holdout-2/cases.json --offline --out <plik>
    ./.venv/Scripts/python.exe tools/eval_rules.py --cases ../../fixtures/module2-holdout-2/cases.json --out <plik>

Zawsze podawaj własne `--out` (domyślnie narzędzie nadpisuje `fixtures/module2-cases/eval_results.json`).

## Liczba etykiet per reguła

| reguła | razem | pass | fail | n/a |
|---|---|---|---|---|
| 1 | 16 | 14 | 2 | 0 |
| 2 | 16 | 13 | 3 | 0 |
| 3 | 14 | 3 | 7 | 4 |
| 9 | 6 | 3 | 1 | 2 |
| 10 | 5 | 3 | 1 | 1 |
| 11 | 3 | 1 | 1 | 1 |
| 12a | 5 | 2 | 2 | 1 |
| 12b | 4 | 2 | 2 | 0 |
| 14 | 5 | 2 | 2 | 1 |
| 15 | 3 | 1 | 1 | 1 |
| 16 | 4 | 2 | 2 | 0 |
| 17 | 10 | 9 | 1 | 0 |
| 18 | 8 | 6 | 2 | 0 |

## Przypadki graniczne w etykietowaniu

- h2-03: "stabilny dochód pasywny" z ostrzeżeniem w tym samym akapicie = pułapka bez naruszeń (3 pass).
- h2-06, h2-08, h2-13, h2-17: pułapki w pełni zgodne (m.in. neutralne "zezwolenie KNF nr ...").
- h2-09: ostrzeżenie wyłącznie po angielsku: 10 fail, ale 9 i 15 pass (treść jest jasna i wskazuje ryzyko);
  etykieta 15 jest dyskusyjna, bo ostrzeżenie nie jest w języku przekazu.
- h2-10: ostrzeżenie w żargonie prawniczym: 9 fail, 3 fail (nie mówi wprost o możliwej stracie), 10 pass.
- h2-12: "to nie jest reklama" przy kodzie promocyjnym = 2 fail (oznaczenie wprowadza w błąd).
- h2-15: "pod nadzorem KNF, więc Twoje pieniądze są bezpieczne" = 18 fail, ale 17 pass (brak sugestii
  aprobaty produktu; nadzór dotyczy firmy).
- h2-14: "zatwierdzony przez KNF - gwarancja jakości" = 17 fail i 18 fail.
- Wyniki historyczne bez twierdzeń o przyszłych zyskach (h2-05) nie mają etykiety reguły 3, bo
  ocena "twierdzenia o potencjalnych zyskach" jest tam niejednoznaczna.
- h2-11: oszczędność podatkowa ("zaoszczędzisz 1800 zł") nie jest twierdzeniem o zysku z inwestycji: 3 n/a.
