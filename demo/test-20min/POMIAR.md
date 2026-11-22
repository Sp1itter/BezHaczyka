# Test: 20 minut zbierania z internetu i pełna analiza

22.11.2026, start na pustej bazie (tylko rejestr KNF: 1088 podmiotów).
Laptop: RTX 3070 Ti 8 GB, 16 wątków CPU, 16 GB RAM. Model: Bielik 4.5B v3 w Ollamie.

## Najważniejsze liczby

| | |
|---|---|
| Zebrane materiały w 20 minut | **448** z 4 źródeł (ok. 22 na minutę) |
| Przeanalizowane | **371** (wszystkie zakwalifikowane), **0 błędów** |
| Czas od startu do pełnej analizy | **55 minut** |
| Skalowanie analizy | 1 → **4 kontenery w 70 s**, automatycznie |
| Wykryte wysokie ryzyko | **20** materiałów, średnie: 29 |
| Odfiltrowane jako poza zakresem | 100 |

## Zebrane materiały

| Źródło | Zebrane | Do analizy |
|---|---|---|
| WWW (wyszukiwanie w internecie) | 182 | 182 |
| TikTok | 100 | 66 |
| Facebook / Instagram (Meta Ad Library) | 89 | 89 |
| YouTube | 77 | 34 |
| **Razem** | **448** | **371** |

Scraper od razu pomija materiały bez związku z firmami inwestycyjnymi, dlatego do analizy trafia
ich mniej, niż zostało zebranych. Tempo zbierania wyznaczają limity zapytań platform (Meta, YouTube),
a nie sprzęt: po 20 minutach system miał w kolejce kolejne ok. 900 znalezionych materiałów.

## Przebieg

Analiza działa równolegle ze zbieraniem. Autoskaler uruchomił 4 kontenery analizy po 70 sekundach,
a GPU pracowało średnio na 75% mocy (szczytowo 95%).

| Minuta | Zebrane | Przeanalizowane |
|---|---|---|
| 5 | 189 | 22 |
| 10 | 327 | 67 |
| 20 | 448 | 115 |
| 30 | 448 | 196 |
| 40 | 448 | 253 |
| 55 | 448 | 371 |

Pełny przebieg co 30 sekund: `przebieg.csv`.

## Wyniki analizy

Materiały wysokiego ryzyka to m.in. strony z sygnałami transakcyjnymi i „pulpitami sygnałów na dziś”,
oferty doradztwa inwestycyjnego, sklepy ze złotem inwestycyjnym, rankingi kursów tradingu
i filmy finfluencerów na TikToku. Moduł 3 wskazał doradcę finansowego oferującego rekomendacje
inwestycyjne bez wpisu w rejestrze KNF.

Najczęściej naruszane wymogi:

| Reguła | Naruszeń |
|---|---|
| 2 Oznaczenie reklamy | 60 |
| 1 Identyfikacja firmy | 57 |
| 3 Informacja o ryzyku przy obietnicy zysku | 51 |
| 9 Zrozumiałość ostrzeżenia | 25 |
| 7 Ostrzeżenie dostępne dopiero po kliknięciu | 25 |
| 4 Za mała czcionka ostrzeżenia | 21 |
| 12a Wyniki historyczne bez okresu i źródła | 21 |
| 6 Ukryte ostrzeżenie | 17 |

Reguły pomiarowe działają na prawdziwych stronach: 43 materiały zostały wyrenderowane i zmierzone
w trzech rozdzielczościach (telefon, tablet, komputer), a reguły 4–8 wykazały w nich łącznie
75 naruszeń widoczności ostrzeżeń.

Przegląd wyników testu posłużył do doprecyzowania zakresu analizy (np. reklamy nieruchomości
i sprzedaży rzeczy używanych są teraz automatycznie odfiltrowywane). Baza w tym katalogu zawiera
wyniki po tej korekcie.

## Pliki

- `baza.dump` – zrzut bazy po teście,
- `media.tar` – zrzuty reklam, strony i nagrania (wydanie `demo-2026-11-22` na GitHubie),
- `przebieg.csv` – stan systemu co 30 sekund.

Wgranie: [demo/README.md](../README.md).
