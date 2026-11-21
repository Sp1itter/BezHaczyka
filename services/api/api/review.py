"""Ocena findingu przez czlowieka: etykiety feedbacku i ich skutek dla statusu.

Model tylko zaweza prace (risk_score, routing). Status koncowy `confirmed`/`dismissed`
wynika z decyzji analityka. Etykieta mowi DLACZEGO - to sygnal do kalibracji progu
i poprawy regul (np. ile FP wynika z blednego dopasowania podmiotu).
"""

from __future__ import annotations

from typing import Literal

# klucz -> (opis w panelu, status po ocenie, grupa)
REVIEW_LABELS: dict[str, tuple[str, str, str]] = {
    "true_positive": ("Trafne (TP): naruszenie potwierdzone", "confirmed", "tp"),
    "true_positive_wrong_entity": ("Naruszenie, ale błędny podmiot / rejestr KNF", "confirmed", "tp"),
    "true_positive_wrong_rule": ("Naruszenie, ale błędna reguła lub podstawa prawna", "confirmed", "tp"),
    "true_positive_wrong_risk": ("Naruszenie, ale zły poziom ryzyka", "confirmed", "tp"),
    "false_negative": ("Przeoczone (FN): model zaniżył ocenę, a to naruszenie", "confirmed", "fn"),
    "false_positive": ("Fałszywy alarm (FP): brak naruszenia", "dismissed", "fp"),
    "out_of_scope": ("Poza zakresem: to nie reklama usług inwestycyjnych", "dismissed", "fp"),
    "duplicate": ("Duplikat innego zgłoszenia", "dismissed", "other"),
    "bad_data": ("Błąd danych: zły materiał, transkrypcja lub zrzut", "dismissed", "other"),
    "other": ("Inny błąd modelu (opisz w notatce)", "dismissed", "other"),
}

ReviewLabel = Literal[
    "true_positive", "true_positive_wrong_entity", "true_positive_wrong_rule", "true_positive_wrong_risk",
    "false_negative", "false_positive", "out_of_scope", "duplicate", "bad_data", "other",
]
assert set(ReviewLabel.__args__) == set(REVIEW_LABELS)  # jedno zrodlo prawdy


def verdict_for(label: str) -> str:
    return REVIEW_LABELS[label][1]


def labels_payload() -> list[dict[str, str]]:
    return [
        {"value": k, "label": desc, "verdict": verdict, "group": group}
        for k, (desc, verdict, group) in REVIEW_LABELS.items()
    ]
