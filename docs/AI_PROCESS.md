# Jak pracowaliśmy z asystentami AI

Byliśmy sześcioosobowym zespołem i pracę podzieliliśmy na trzy
strumienie: zbieranie danych, analizę oraz panel z API. Asystentów AI używaliśmy do pisania kodu, testów i dokumentacji, ale zakres, architekturę, podział pracy i ocenę wyników zostawiliśmy
sobie. Niżej opisujemy, jak to wyglądało w praktyce i gdzie w repozytorium są tego ślady.

## Narzędzia

- **Claude Code** – asystent kodowania, każdy z nas pracował na własnej instancji.
- **Plugin superpowers** – narzucał stały rytm pracy: najpierw rozmowa o wymaganiach, potem
  specyfikacja, plan z etapami, implementacja z testami i przegląd.
- **graphify** – graf zależności w kodzie (`graphify-out/`). Asystent korzystał z niego, zanim zaczął
  czytać pliki, dzięki czemu mniej zgadywał.
- W samym produkcie nie ma żadnego zewnętrznego API. Analizę robi lokalny Bielik 4.5B i bge-m3
  przez Ollamę, a `tools/check_compliance.py` pilnuje, żeby tak zostało.

## Przebieg pracy

1. **Wymagania i zakres.** Opis wyzwania i załączniki przeczytaliśmy sami i sami zdecydowaliśmy,
   co jest w zakresie. Najważniejsza decyzja: o zakresie decyduje opakowanie instrumentu, a nie aktywo,
   więc CFD i ETP na kryptowaluty zostają, a zakup krypto spot odpada (MiCA).
2. **Specyfikacja i plan.** Asystent pomagał rozpisać design, ale wersję drugą przyjęliśmy dopiero
   po wspólnym przeglądzie (commit `9920070`). Każdy etap miał plan z listą zadań i testów.
3. **Podział pracy.** Każdy strumień miał swój obszar: zbieranie danych, analiza, panel i API.
   Każdy pracował na osobnej gałęzi i w osobnym katalogu roboczym, a wspólne pliki miały jednego właściciela.
   Zmiany wchodziły przez pull requesty po każdym etapie.
4. **Kontrakty danych.** Formaty `AdDocument`, `Finding` i `RuleResult` ustaliliśmy na początku
   i zapisaliśmy przykłady w `fixtures/contract-examples/`. Test `test_spojnosc.py` łapie każdą
   rozbieżność kopii kontraktu między serwisami.
5. **Implementacja i przegląd.** Asystent pisał kod razem z testami (w analyzerze ponad 900 testów).
   Każdą większą zmianę przeglądaliśmy przed scaleniem: osobno zgodność z wymaganiami, osobno jakość.
6. **Weryfikacja na żywym systemie.** Testy nie wystarczały, więc każdą wersję puszczaliśmy na
   prawdziwych danych z internetu i czytaliśmy wyniki. Tak wyszły błędy, których żaden test nie
   przewidział: zwiastun „Toy Story: Buzz Lightyear” oceniony jako reklama brokera Lightyear,
   gra z „+50% szybkości” potraktowana jak obietnica zysku, zastrzeżenie „nie stanowi rekomendacji”
   uznane za rekomendację. Każdy taki przypadek trafił do testów regresji
   (`services/analyzer/tests/test_live_regressions*.py`).

## Jak sprawdzaliśmy, czy model ocenia dobrze

- **Zbiory kontrolne zamrożone przed strojeniem.** Etykiety commitowaliśmy, zanim uruchomiliśmy
  model, więc historia gita pokazuje, że nie dopasowaliśmy ich do wyników (`5370254`, `e12544d`).
  Na zbiorze, którego nie używaliśmy do strojenia (`fixtures/module2-holdout-2/`, 99 etykiet),
  trafność wynosi 81–82%. To uważamy za uczciwą miarę. Wyższe wyniki na zbiorze strojenia
  traktujemy jako optymistyczne.
- **Kod tam, gdzie model zawodził.** Bielik 4.5B potrafił zignorować polecenie albo „zobaczyć”
  ostrzeżenie, którego w tekście nie było. Elementy, które da się zmierzyć, rozstrzyga więc kod
  (`rules_llm/guards.py`, `scope_gate.py`), a model ocenia tylko to, co wymaga rozumienia języka.
- **Powtarzalność.** Po tym, jak ta sama reklama dostała dwa różne werdykty, ustawiliśmy
  `temperature 0` i stały `seed`. Nadzorca nie może dostać innej oceny przy każdym odświeżeniu.
- **Człowiek ma ostatnie słowo.** W panelu każdy wynik ma decyzję analityka (potwierdzenie albo
  odrzucenie z uzasadnieniem), a próg alertów ustawia się w kalibracji na podstawie ocen ludzi.

## Bezpieczeństwo łańcucha dostaw

Wersje zależności są przypięte. `tools/audit.sh` skanuje pakiety Pythona (pip-audit), panel
sprawdzamy `npm audit`, a wyniki są w `docs/SECURITY-AUDIT.md`. Licencje zebraliśmy
w `docs/LICENSES.md`. Sekrety są tylko w `infra/.env`, poza repozytorium.

## Czego nie oddaliśmy asystentowi

- interpretacji przepisów i decyzji, co jest w zakresie nadzoru,
- etykiet zbioru złotego do kalibracji (`fixtures/gold/`),
- decyzji o scaleniu zmian i oceny, czy wynik na żywych danych ma sens.

Etykiety zbioru kontrolnego Modułu 1 (`fixtures/module1-labels/`) przygotowaliśmy z pomocą asystenta
według ustalonej rubryki, więc nie przedstawiamy ich jako oceny eksperckiej.
