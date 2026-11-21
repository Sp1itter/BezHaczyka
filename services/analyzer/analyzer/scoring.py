"""Scoring ryzyka — par. 9 design doca.

Kluczowa decyzja: reguly `not_applicable` NIE wchodza do mianownika. Inaczej
reklama milczaca o podatkach (regula 16 nieadekwatna) dostawalaby sztucznie
niski score tylko dlatego, ze o czyms nie wspomniala.
"""

from __future__ import annotations

from analyzer.contracts import RiskLevel, RuleResult, Verdict

# Progi poziomu ryzyka. Panel kalibracji przesuwa `flag_threshold` po stronie
# klienta na podstawie zapisanych rule_results — BEZ ponownej inferencji.
DEFAULT_FLAG_THRESHOLD = 50.0
HIGH_THRESHOLD = 70.0
MEDIUM_THRESHOLD = 40.0


def risk_score(results: list[RuleResult]) -> float:
    """Wazony udzial zlamanych regul w regulach, ktore dalo sie ocenic.

    Zwraca 0.0 dla pustej listy i dla przypadku, w ktorym zadnej reguly
    nie dalo sie zastosowac — brak danych nie jest dowodem naruszenia.
    """
    numerator = 0.0
    denominator = 0.0

    for r in results:
        if r.verdict is Verdict.NOT_APPLICABLE:
            continue
        denominator += r.severity
        if r.verdict is Verdict.FAIL:
            numerator += r.severity * r.confidence

    if denominator == 0.0:
        return 0.0
    return round(100.0 * numerator / denominator, 1)


# Progi eskalacji po NAJCIEZSZYM potwierdzonym naruszeniu.
# Ponizej tej pewnosci nie eskalujemy — heurystyki (np. regula 7 z confidence 0.6)
# nie moga same podnosic materialu do poziomu wysokiego.
ESCALATION_MIN_CONFIDENCE = 0.7
ESCALATION_HIGH_SEVERITY = 5
ESCALATION_MEDIUM_SEVERITY = 4


def max_breach_severity(results: list[RuleResult]) -> int:
    """Waga najciezszej PEWNEJ zlamanej reguly. 0, gdy nie ma takiej."""
    return max(
        (
            r.severity
            for r in results
            if r.verdict is Verdict.FAIL and r.confidence >= ESCALATION_MIN_CONFIDENCE
        ),
        default=0,
    )


def risk_level(score: float, results: list[RuleResult] | None = None) -> RiskLevel:
    """Poziom ryzyka. `high` odpala alert WebSocket w dashboardzie.

    DWA NIEZALEZNE SYGNALY, bo mierza rozne rzeczy:

    `score` mowi, JAKA CZESC wymogow material narusza. Jest proporcjonalny,
    wiec rozciencza sie liczba regul, ktore material spelnia: to samo naruszenie
    o wadze 5 daje 45 punktow przy dwoch zdanych regulach i tylko 17 przy osmiu.
    Jako miara "ile wymogow naruszono" jest poprawny i zostaje bez zmian —
    panel kalibracji przemiata prog wlasnie po nim.

    `results` mowi, JAK POWAZNE jest najciezsze naruszenie. Nadzorca nie myśli
    "ta reklama narusza jeden z dziewieciu wymogow, wiec jest 17% zla", tylko
    "ta reklama narusza art. 44 ust. 8". Dlatego potwierdzone naruszenie reguly
    o wadze 5 podnosi material do poziomu wysokiego NIEZALEZNIE od tego, ile
    innych wymogow spelnia.

    Eskalacja NIGDY nie obniza poziomu wynikajacego ze score — bierzemy wyzszy
    z dwoch sygnalow. Przy `results=None` zachowanie jest takie jak wczesniej.
    """
    if score >= HIGH_THRESHOLD:
        ze_score = RiskLevel.HIGH
    elif score >= MEDIUM_THRESHOLD:
        ze_score = RiskLevel.MEDIUM
    else:
        ze_score = RiskLevel.LOW

    if not results:
        return ze_score

    severity = max_breach_severity(results)
    if severity >= ESCALATION_HIGH_SEVERITY:
        return RiskLevel.HIGH
    if severity >= ESCALATION_MEDIUM_SEVERITY and ze_score is RiskLevel.LOW:
        return RiskLevel.MEDIUM
    return ze_score


def is_flagged(score: float, threshold: float = DEFAULT_FLAG_THRESHOLD) -> bool:
    """Czy material zostaje oflagowany przy danym progu.

    Ta funkcja jest celowo trywialna i czysta: front implementuje dokladnie
    ten sam warunek w JS, zeby suwak thresholdu dzialal natychmiast, bez
    requestu do modelu. Jesli tu cokolwiek sie zmieni, zmien tez w `web`.
    """
    return score >= threshold


def failed_rules(results: list[RuleResult]) -> list[RuleResult]:
    """Zlamane reguly, od najciezszej. To kolejnosc wyswietlania w UI —
    nadzorca ma najpierw zobaczyc najpowazniejsze naruszenie."""
    return sorted(
        (r for r in results if r.verdict is Verdict.FAIL),
        key=lambda r: (r.severity * r.confidence),
        reverse=True,
    )


def coverage(results: list[RuleResult]) -> float:
    """Jaki odsetek regul udalo sie w ogole ocenic (0.0-1.0).

    Niskie pokrycie znaczy, ze material wymaga oceny recznej, nawet jesli
    score wyszedl niski. Pokazujemy to w UI obok score'u, bo inaczej
    'ryzyko 5%' przy 14 regulach not_applicable jest mylace.
    """
    if not results:
        return 0.0
    assessed = sum(1 for r in results if r.verdict is not Verdict.NOT_APPLICABLE)
    return round(assessed / len(results), 3)
