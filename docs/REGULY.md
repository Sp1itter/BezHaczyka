# Reguły oceny materiałów

Moduł 2 sprawdza 18 wymogów z art. 44 rozporządzenia delegowanego 2017/565 (lista z materiałów
konkursowych). Moduł 3 dodaje regułę doradztwa bez zezwolenia. Każdy wynik ma werdykt
(zgodne / naruszenie / nie oceniono), cytat lub pomiar jako dowód i podstawę prawną.

Sposób oceny:
- **pomiar** – liczony z renderu strony w przeglądarce (Playwright) w trzech rozdzielczościach,
- **model** – ocena Bielika 4.5B na treści materiału (tekst, napisy, transkrypcja),
- **model + kod** – model ocenia język, a elementy mierzalne rozstrzyga kod.

| # | Reguła | Co sprawdza | Sposób |
|---|---|---|---|
| 1 | Identyfikacja firmy | czy materiał podaje oficjalną nazwę firmy inwestycyjnej | model |
| 2 | Oznaczenie reklamy | czy materiał jest jednoznacznie oznaczony jako reklama (także oznaczenie platformy, np. „Sponsorowane”) | model + kod |
| 3 | Informacja o ryzyku | czy obietnicy zysku towarzyszy ostrzeżenie (odległość na stronie, w tekście albo w czasie nagrania) | model + kod |
| 4 | Rozmiar czcionki ryzyka | czcionka ostrzeżenia w porównaniu z przeważającą czcionką materiału | pomiar |
| 5 | Ekspozycja i kontrast | kontrast i przesłonięcie ostrzeżenia | pomiar |
| 6 | Ukrywanie ryzyka | ostrzeżenie w przypisach, sekcji „Legal” lub w miejscu o niskiej widoczności | pomiar |
| 7 | Dostępność za 1 kliknięciem | czy ostrzeżenie wymaga rozwinięcia lub przejścia dalej | pomiar |
| 8 | Responsywność | czy na telefonie, tablecie i komputerze tekst nie jest ucinany ani zbyt mały | pomiar |
| 9 | Zrozumiałość | czy ostrzeżenie jest zrozumiałe dla odbiorcy | model |
| 10 | Spójność językowa | czy ostrzeżenie jest w tym samym języku co reklama | model + kod |
| 11 | Porównania produktów | porównania, ich źródło i założenia | model |
| 12a | Wyniki historyczne – okres | 5 lat, pełne okresy 12-miesięczne, okres referencyjny i źródło | model + kod |
| 12b | Wyniki historyczne – waluta i opłaty | ostrzeżenie o kursach walut oraz wpływie prowizji i opłat | model + kod |
| 13 | Dominacja wyników historycznych | czy wyniki historyczne nie są najbardziej wyeksponowanym elementem | pomiar + kod |
| 14 | Ostrzeżenie przy wynikach historycznych | „wyniki historyczne nie są wiarygodnym wskaźnikiem przyszłych” | model + kod |
| 15 | Prognozy | prognoza przyszłych wyników i ostrzeżenie przy niej | model |
| 16 | Informacja podatkowa | zależność od indywidualnej sytuacji klienta i możliwość zmian | model + kod |
| 17 | Sugerowanie aprobaty KNF | odwołanie do organu nadzoru jako zatwierdzenia produktu | model + kod |
| 18 | Nadzór jako argument bezpieczeństwa | „bezpieczne, bo nadzorowane przez KNF” | model + kod |
| M3 | Doradztwo bez zezwolenia | rekomendacje kupna lub sprzedaży instrumentów od podmiotu spoza rejestru KNF | model + rejestr |

Reguły pomiarowe (4–8, 13) działają dla materiałów, które da się wyrenderować: reklam z Meta Ad Library
i stron WWW. Dla nagrań i postów bez renderu dostają „nie oceniono” z podanym powodem – brak danych
nie jest traktowany jako naruszenie.

Zanim materiał trafi do reguł, brama zakresu odrzuca treści bez związku z instrumentami finansowymi
(np. kredyty frankowe, kupony, promocje kont bankowych, gry). Kryptoaktywa kupowane bezpośrednio są poza
zakresem, a CFD i ETP na kryptowaluty – w zakresie.

Poziom ryzyka wynika z najpoważniejszego naruszenia, a wynik liczbowy (0–100) jest z nim spójny:
poziom wysoki to zawsze co najmniej 70 punktów. Próg alertów ustawia się w panelu kalibracji.
