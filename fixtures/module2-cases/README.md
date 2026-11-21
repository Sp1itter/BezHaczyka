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

## Korekty niespojnosci danych (nie dopasowanie do wyniku)

m2-29, m2-30, m2-31: pole `render_probe.viewports.*.dominant_font_px` mialo 28 (rozmiar
naglowka). Wg `services/scraper/render/probe.js` dominant_font_px to czcionka o najwiekszej
LACZNEJ liczbie znakow widocznych wezlow (`fontChars`, wygrywa max), a nie najwiekszy
naglowek. Liczone na wezlach fixture'u: 14 px = 41 + 50 = 91 znakow, 28 px = 30-34, 16 px = 37
-> dominant = 14. Poprawiono dane na 14 (we wszystkich viewportach tych trzech przypadkow).
Etykiety `expected` bez zmian: ostrzezenie 14 px / 14 px = 1.0 >= 0.9 -> regula 4 pass.
Kod fallbacku byl poprawny; niespojny byl fixture.

Uwaga otwarta (poza zakresem tej korekty): m2-28 ma ten sam typ danych (dominant 28), ale
wg definicji probe.js dominantem bylby tam 8 px (50 znakow samego ostrzezenia), co dawaloby
ratio 1.0 i pass wbrew etykiecie fail. Definicja "po liczbie znakow" jest wrazliwa na to,
ze samo ostrzezenie jest dlugim tekstem; przypadek wymaga decyzji autora zbioru.
