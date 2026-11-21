"""Regula 10 — spojnosc jezykowa — rozstrzygana DETERMINISTYCZNIE.

Art. 44 ust. 2 lit. f rozporzadzenia del. 2017/565: informacja o ryzyku nie moze
byc podana w innym jezyku niz glowny przekaz materialu. Klasyczne naruszenie to
polska reklama z ostrzezeniem wylacznie po angielsku — odbiorca go nie przeczyta.

DLACZEGO NIE LLM

Bielik 4.5B konsekwentnie uznawal "Risk warning: investing involves risk and you
may lose your capital" w polskiej reklamie za zgodny z przekazem. Dwie proby
doprecyzowania promptu nie pomogly. Tymczasem to zadanie jest w pelni mierzalne:
wystarczy porownac jezyk zdania z ostrzezeniem z jezykiem reszty materialu.

Regula 10 staje sie wiec HYBRYDOWA: deterministyczne rozstrzygniecie ma
pierwszenstwo, a werdykt modelu zostaje tylko wtedy, gdy pomiar jest niepewny
(np. material zbyt krotki, zeby wykryc jezyk).
"""

from __future__ import annotations

import re

from analyzer.contracts import Engine, Evidence, EvidenceKind, RuleResult, Verdict
from analyzer.router import normalize

# Slowa funkcyjne — najpewniejszy sygnal jezyka, bo wystepuja w kazdym zdaniu
# i nie sa terminami branzowymi, ktore moglyby wystapic w obu jezykach.
PL_STOPWORDS = {
    "i", "w", "na", "nie", "jest", "sie", "ze", "oraz", "lub", "dla", "do",
    "z", "za", "od", "przez", "jako", "tylko", "moze", "takze", "ale", "juz",
    "sa", "byc", "tego", "ten", "ta", "to", "nasz", "nasza", "nasze", "swoje",
}
EN_STOPWORDS = {
    "the", "and", "of", "to", "is", "are", "you", "your", "may", "with",
    "that", "this", "can", "will", "be", "not", "in", "on", "for", "all",
    "it", "as", "at", "or", "if", "we", "our", "have", "has", "been",
}

# Frazy ostrzegajace o ryzyku, po polsku i po angielsku.
PL_RISK_PATTERNS = (
    r"\bryzyk\w*",
    r"\bstrat\w*\s+kapital\w*",
    r"\bmozesz\s+stracic",
    r"\butrat\w*\s+kapital\w*",
    r"\bnie\s+gwarantuj\w*",
)
EN_RISK_PATTERNS = (
    r"\brisk\b",
    r"\brisks\b",
    r"\bwarning\b",
    r"\byou\s+may\s+lose\b",
    r"\bcapital\s+at\s+risk\b",
    r"\bpast\s+performance\b",
    r"\blosses\b",
)

# Ponizej tylu slow funkcyjnych pomiar jest niepewny i oddajemy decyzje modelowi.
MIN_STOPWORDS_FOR_CONFIDENCE = 2


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", normalize(text))


def detect_language(text: str) -> str:
    """Zwraca "pl", "en" albo "unknown" na podstawie slow funkcyjnych."""
    words = _words(text)
    if not words:
        return "unknown"
    pl = sum(1 for w in words if w in PL_STOPWORDS)
    en = sum(1 for w in words if w in EN_STOPWORDS)
    if max(pl, en) < MIN_STOPWORDS_FOR_CONFIDENCE:
        return "unknown"
    if pl > en:
        return "pl"
    if en > pl:
        return "en"
    return "unknown"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def risk_sentences(text: str) -> list[str]:
    """Zdania zawierajace ostrzezenie o ryzyku, w ktorymkolwiek z dwoch jezykow."""
    out: list[str] = []
    for sentence in split_sentences(text):
        norm = normalize(sentence)
        if any(re.search(p, norm) for p in PL_RISK_PATTERNS + EN_RISK_PATTERNS):
            out.append(sentence)
    return out


def assess_rule_10(
    text: str, rule_meta_entry: tuple[str, int, str]
) -> RuleResult | None:
    """Oceń regule 10 deterministycznie.

    Zwraca None, gdy pomiar jest niepewny — wtedy wolajacy zachowuje werdykt
    modelu. Nigdy nie zwraca `fail` na podstawie niepewnego pomiaru.
    """
    name, severity, basis = rule_meta_entry

    sentences = risk_sentences(text)
    if not sentences:
        return None  # brak ostrzezenia to sprawa reguly 3, nie 10

    # Jezyk glownego przekazu wyznaczamy z czesci BEZ zdan o ryzyku, zeby
    # angielskie ostrzezenie nie przeciagnelo wyniku na "en".
    main_part = " ".join(s for s in split_sentences(text) if s not in sentences)
    main_lang = detect_language(main_part)

    if main_lang == "unknown":
        return None

    def _result(verdict: Verdict, summary: str, quote: str | None) -> RuleResult:
        return RuleResult(
            rule_id="10",
            rule_name=name,
            engine=Engine.HYBRID,
            verdict=verdict,
            confidence=1.0,
            severity=severity,
            legal_basis=basis,
            evidence=Evidence(
                kind=EvidenceKind.QUOTE if quote else EvidenceKind.ABSENCE,
                summary=summary,
                quote=quote,
            ),
        )

    for sentence in sentences:
        risk_lang = detect_language(sentence)
        if risk_lang != "unknown" and risk_lang != main_lang:
            return _result(
                Verdict.FAIL,
                (
                    f"Ostrzezenie o ryzyku jest w jezyku '{risk_lang}', a glowny "
                    f"przekaz materialu w jezyku '{main_lang}'. Odbiorca grupy "
                    f"docelowej moze go nie zrozumiec."
                ),
                sentence,
            )

    return _result(
        Verdict.PASS,
        (
            f"Ostrzezenie o ryzyku jest w tym samym jezyku ('{main_lang}') "
            f"co glowny przekaz materialu."
        ),
        sentences[0],
    )


def apply_rule_10_override(
    results: list[RuleResult], text: str, rule_meta: dict[str, tuple[str, int, str]]
) -> list[RuleResult]:
    """Podmien werdykt reguly 10 na deterministyczny, gdy pomiar jest pewny.

    NIE wchodzi w sciezke awarii. Jesli regula 10 wrocila jako `not_applicable`,
    znaczy to, ze model padl, nie odpowiedzial albo pominal te regule — i wtedy
    zostawiamy `not_applicable`.

    Dlaczego tak, mimo ze pomiar nie zalezy od modelu: niezmienniczosc "awaria
    modelu niczego nie twierdzi" jest wazniejsza niz zlapanie jednego naruszenia
    wiecej. Narzedzie nadzorcze, ktore przy padnietym modelu nadal wydaje
    werdykty, jest trudne do obronienia przed nadzorca. Koszt: gdy model
    bledenie oznaczy regule 10 jako nieadekwatna, nie poprawimy go. To rzadkie
    i bezpieczny kierunek bledu.
    """
    if "10" not in rule_meta:
        return results

    current = next((r for r in results if r.rule_id == "10"), None)
    if current is None or current.verdict is Verdict.NOT_APPLICABLE:
        return results

    deterministic = assess_rule_10(text, rule_meta["10"])
    if deterministic is None:
        return results
    return [deterministic if r.rule_id == "10" else r for r in results]
