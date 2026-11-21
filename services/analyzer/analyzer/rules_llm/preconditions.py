"""Warunki wstepne regul warunkowych — rozstrzygane W KODZIE, nie w promptcie.

DLACZEGO TO ISTNIEJE

Czesc regul z zalacznika UKNF jest warunkowa:
  - reguly 12a, 12b, 14 dotycza WYLACZNIE materialow prezentujacych wyniki
    historyczne (art. 44 ust. 4 rozporzadzenia del. 2017/565),
  - reguly 15 i 16 dotycza materialow z prognoza albo wzmianka o podatkach
    (art. 44 ust. 6 i 7).

Bielik 4.5B ignorowal ten warunek zapisany w promptcie: na materiale z sama
prognoza ("za rok zarobisz 20%"), bez zadnych wynikow historycznych, zwracal
`fail` dla 12a, 12b i 14. To falszywy alarm — najgorszy kierunek bledu
w narzedziu nadzorczym, bo nadzorca dostaje zarzut, ktory nie ma podstawy
w materiale.

Dwie proby doprecyzowania promptu nie pomogly, wiec warunek rozstrzygamy
deterministycznie. Zysk jest podwojny: znika cala klasa falszywych alarmow
i oszczedzamy jedno wywolanie modelu na dokument.

Wszystkie wzorce sa odporne na polska fleksje i dzialaja na tekscie
po normalizacji (male litery, bez ogonkow).
"""

from __future__ import annotations

import re

from analyzer.router import normalize

# --------------------------------------------------------------------------- #
# Wyniki historyczne (reguly 12a, 12b, 14)
# --------------------------------------------------------------------------- #

# rok do 2025 wlacznie — pozniejsze to horyzont prognozy, nie wynik historyczny
_PAST_YEAR = r"(?:19\d{2}|20[01]\d|202[0-5])"

# czas przeszly czasownikow wyniku (zyskal, zarobila, wypracowalismy, osiagnelo...)
_PAST_VERB = r"(?:zyskal|zarobil|wypracowal|osiagnel|osiagnal|przynios|wzrosl)\w*"

HISTORICAL_PATTERNS: tuple[str, ...] = (
    r"\bhistoryczn\w*",
    r"\bwynik\w*\s+(za|z)\s+(19|20)\d{2}",
    r"\bw\s+(ubieglym|minionym|poprzednim)\s+(roku|kwartale|miesiacu|polroczu)",
    r"\bw\s+ostatnich\s+\d+\s+(lat|latach|miesiacach|kwartalach)",
    r"\bw\s+latach\s+(19|20)\d{2}",
    r"\bod\s+poczatku\s+roku",
    r"\bytd\b",
    r"\bdotychczasow\w*\s+(wynik|stop|zwrot)\w*",
    r"\bosiagn\w*\s+\d+[.,]?\d*\s*%",
    r"\bstop\w*\s+zwrotu\s+za\b",
    r"\bzysk\w*\s+za\s+(19|20)\d{2}",
    # "zysk 34% w 2023 roku" — rok miniony (do 2025); "w 2030 roku zarobisz"
    # to prognoza i nie moze tu wpadac.
    r"\bw\s+(19\d{2}|20[01]\d|202[0-5])\s+roku",
    # "wyniosl 12%", "wzrosl o 8%", "spadl o 3%" — zdania o tym, co SIE STALO
    r"\b(wynios|wzros|spad)\w*\s+o?\s*\d+[.,]?\d*\s*%",
    # zakres lat MINIONYCH ("pelne lata 2019-2023"); lata prognozy (2026+) nie wpadaja
    rf"\b{_PAST_YEAR}\s*[–\-−—]\s*{_PAST_YEAR}\b",
    # rok + zmiana procentowa ("2019 +6%", "2022 -5%")
    rf"\b{_PAST_YEAR}\s*:?\s*[+\-−]\s*\d+[.,]?\d*\s*%",
    r"\bstop\w*\s+zwrotu\s+w\s+(pelnych\s+)?latach",
    r"\bw\s+(zeszlym|ubieglym)\s+roku",
    # rok MINIONY (do 2025) + czasownik przeszly wyniku + procent, w jednym zdaniu:
    # "w 2022 r. zyskalismy 18%". Prognoza ("w 2027 r. zarobisz 18%") nie wpada:
    # rok > 2025 nie pasuje do _PAST_YEAR, a "zarobisz" nie jest czasem przeszlym.
    rf"\b{_PAST_YEAR}\b(?:\s*r\.)?[^.!?%]{{0,40}}?\b{_PAST_VERB}[^.!?%]{{0,30}}?\d+[.,]?\d*\s*%",
    # i odwrotnie: "zyskalismy 18% w 2022 r."
    rf"\b{_PAST_VERB}[^.!?%]{{0,30}}?\d+[.,]?\d*\s*%[^.!?]{{0,30}}?\b{_PAST_YEAR}\b",
    # "od 2018 roku przynosi srednio 7% rocznie": wynik liczony od roku minionego
    rf"\bod\s+(?:roku\s+)?{_PAST_YEAR}\b[^.!?]{{0,60}}?\d+[.,]?\d*\s*%",
    rf"\d+[.,]?\d*\s*%[^.!?]{{0,40}}?\bod\s+(?:roku\s+)?{_PAST_YEAR}\b",
    r"\br\s*/\s*r\b",
)

HISTORICAL_REASON = (
    "Material nie prezentuje wynikow historycznych, wiec reguly dotyczace ich "
    "okresu, waluty i zastrzezenia nie maja zastosowania "
    "(art. 44 ust. 4 rozporzadzenia del. 2017/565)."
)

# --------------------------------------------------------------------------- #
# Prognozy i podatki (reguly 15, 16)
# --------------------------------------------------------------------------- #

FORECAST_PATTERNS: tuple[str, ...] = (
    r"\bprognoz\w*",
    r"\bszacuj\w*",
    r"\bszacunk\w*",
    r"\bspodziewa\w*",
    r"\bprzewidu\w*",
    r"\bw\s+(przyszlym|kolejnym|nastepnym)\s+(roku|kwartale|miesiacu)",
    r"\bza\s+rok\b",
    r"\boczekiwan\w*\s+(zysk|stop|zwrot)\w*",
    r"\bpotencjaln\w*\s+(zysk|zwrot|stop)\w*",
    r"\bmoze\s+(wzrosnac|przyniesc|dac)",
    r"\bdocelow\w*\s+(cena|wartosc|poziom)",
)

TAX_PATTERNS: tuple[str, ...] = (
    r"\bpodatk\w*",
    r"\bpodatek\b",
    r"\bopodatkowan\w*",
    r"\bbelki\b",
    r"\bbelka\b",
    r"\bpit\b",
    r"\bzwolnien\w*\s+podatkow\w*",
    r"\bulg\w*\s+podatkow\w*",
)

FORECAST_OR_TAX_REASON = (
    "Material nie zawiera prognozy przyszlych wynikow ani odwolania do "
    "traktowania podatkowego, wiec te reguly nie maja zastosowania "
    "(art. 44 ust. 6 i 7 rozporzadzenia del. 2017/565)."
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    norm = normalize(text)
    return any(re.search(p, norm) for p in patterns)


def mentions_historical_performance(text: str) -> bool:
    """Czy material PREZENTUJE wyniki historyczne.

    Prognoza nie jest wynikiem historycznym: "za rok zarobisz 20%" mowi
    o przyszlosci i NIE uruchamia regul 12a, 12b ani 14.
    """
    return _matches_any(text, HISTORICAL_PATTERNS)


def mentions_forecast(text: str) -> bool:
    return _matches_any(text, FORECAST_PATTERNS)


def mentions_tax(text: str) -> bool:
    return _matches_any(text, TAX_PATTERNS)


def mentions_forecast_or_tax(text: str) -> bool:
    """Warunek wstepny wsadu 4 (reguly 15 i 16).

    Wystarczy jedno z dwoch — jesli material ma prognoze, ale nie mowi
    o podatkach, model nadal musi ocenic regule 15, a regule 16 sam oznaczy
    jako not_applicable.
    """
    return mentions_forecast(text) or mentions_tax(text)
