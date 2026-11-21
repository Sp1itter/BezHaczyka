# Zbior regresyjny Modulu 2 (SYNTETYCZNY)

**Wszystkie materialy w tym katalogu sa SYNTETYCZNE.** Napisal je zespol do testow;
to nie sa prawdziwe reklamy, a nazwy firm i funduszy ("Fikcyjny Dom Maklerski Alfa S.A.",
"Fikcyjny Fundusz Akcji Gamma"), numery zezwolen i adresy (`example.invalid`) sa wymyslone.
Nie wolno ich cytowac jako przykladow realnych naruszen.

## Cel

Zbior zloty (`fixtures/gold/`, 8 realnych reklam) jest maly i nie pokrywa wszystkich regul.
Tu jest ok. 30 krotkich przypadkow, kazdy celowo testuje 1-5 regul z 18 kryteriow UKNF
(art. 44 rozp. del. 2017/565). Dla regul 1, 2, 3, 9-11, 12a, 12b, 13-18 jest co najmniej
jeden przypadek `fail` i jeden `pass` lub `not_applicable`; reguly 4-8 (DET, z `RenderProbe`)
maja 4 przypadki. Pozwala to liczyc trafnosc PER REGULA (TP/FP/FN/TN, fail = pozytyw).

## Pliki

- `cases.json` — `{"synthetic": true, "cases": [...]}`; przypadek: `id`, `opis`,
  `expected` (`{rule_id: pass|fail|not_applicable}` TYLKO dla regul celowo testowanych)
  i `doc` (pelny `AdDocument`, ewentualnie z `render_probe`).
- `eval_results.json` — wynik ostatniego uruchomienia `tools/eval_rules.py` (nadpisywany).

## Uzycie

Z `services/analyzer`:

    ./.venv/Scripts/python.exe tools/eval_rules.py             # zywy Bielik (Ollama 127.0.0.1:11434)
    ./.venv/Scripts/python.exe tools/eval_rules.py --rule 12a  # jedna regula
    ./.venv/Scripts/python.exe tools/eval_rules.py --offline   # bez modelu (fake klient)
    ./.venv/Scripts/python.exe -m pytest tests/test_eval_rules.py -q

Reguly 4-8: jesli potok zwroci wypelniacz (regula nie zostala oceniona), wynik jest
raportowany jako "oczekiwane, niezaimplementowane" i nie wchodzi do macierzy pomylek.

## Zasada etykietowania (wazne dla uczciwosci metryk)

Etykiety `expected` zostaly nadane z TRESCI przypadku i tekstu kryteriow UKNF, ZANIM
uruchomiono jakikolwiek model na tym zbiorze. Nie dopasowywano ich do wynikow Bielika.
Zmiana etykiety po fakcie jest dopuszczalna wylacznie, gdy byla ona obiektywnie bledna
wg kryterium — i wtedy musi byc jawnie opisana (np. w commit message). Dopasowanie
etykiet do wyniku modelu uniewazniloby metryki.

Uwagi do etykiet: regula 7 (dostepnosc za 1 kliknieciem) ma tylko etykiete `pass`
(ostrzezenie widoczne bez klikania); regula 13 bez geometrii to `not_applicable`
(brak pomiaru nie jest dowodem dominacji).
