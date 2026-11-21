"""Interfejs Rule — wspolny dla regul DET (osoba A) i LLM (osoba B).

!!! TEN PLIK JEST ZDUPLIKOWANY !!!
Kopia osoby B: services/analyzer/analyzer/rules_llm/base.py (ta jest kopia osoby A)
Obie kopie musza miec IDENTYCZNA sygnature `Rule`. Zrodlo prawdy dla kształtu
`RuleResult` to par. 6.3 design doca, a test kontraktowy pilnuje zgodnosci.

Dlaczego duplikat, a nie services/common/: wspolny modul wymusilby `context: .`
w docker-compose, czyli cale repozytorium jako kontekst budowania KAZDEGO obrazu
(wolne buildy, fixtures/ i node_modules w kontekscie) i zlamalby wymog separacji
lekkich serwisow ze specyfikacji par. 5. 15 linii duplikatu < sprzeganie buildow.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RuleResult,
    Verdict,
)


@runtime_checkable
class Rule(Protocol):
    """Jedna regula oceny materialu reklamowego.

    Kazda regula z zalacznika UKNF to osobna implementacja. Dodanie reguly 19
    nie wymaga ruszania silnika — wystarczy zarejestrowac nowa klase.
    """

    rule_id: str
    rule_name: str
    engine: Engine
    severity: int
    legal_basis: str

    def evaluate(self, doc: AdDocument) -> RuleResult:
        """Ocen material. NIGDY nie rzucaj wyjatkiem na brakujace dane —
        zwroc `not_applicable` z powodem. Nadzorca musi widziec roznice miedzy
        'sprawdzilem i jest w porzadku' a 'nie dalo sie sprawdzic'."""
        ...


# --------------------------------------------------------------------------- #
# Pomocniki do budowania wynikow — zeby kazda regula nie powtarzala boilerplate
# --------------------------------------------------------------------------- #


class RuleBase:
    """Baza z gotowymi konstruktorami RuleResult. Dziedziczenie opcjonalne —
    wystarczy spelniac protokol `Rule`."""

    rule_id: str = ""
    rule_name: str = ""
    engine: Engine = Engine.LLM
    severity: int = 3
    legal_basis: str = ""

    def _result(
        self,
        verdict: Verdict,
        evidence: Evidence,
        confidence: float = 1.0,
    ) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            engine=self.engine,
            verdict=verdict,
            confidence=confidence,
            severity=self.severity,
            legal_basis=self.legal_basis,
            evidence=evidence,
        )

    def failed(
        self,
        summary: str,
        *,
        quote: str | None = None,
        measured: dict[str, float] | None = None,
        confidence: float = 1.0,
        **ev_kwargs: object,
    ) -> RuleResult:
        kind = EvidenceKind.MEASUREMENT if measured else EvidenceKind.QUOTE
        if quote is None and measured is None:
            kind = EvidenceKind.ABSENCE
        return self._result(
            Verdict.FAIL,
            Evidence(
                kind=kind,
                summary=summary,
                quote=quote,
                measured=measured,
                **ev_kwargs,  # type: ignore[arg-type]
            ),
            confidence,
        )

    def passed(
        self,
        summary: str,
        *,
        quote: str | None = None,
        measured: dict[str, float] | None = None,
        confidence: float = 1.0,
        **ev_kwargs: object,
    ) -> RuleResult:
        kind = EvidenceKind.MEASUREMENT if measured else EvidenceKind.QUOTE
        return self._result(
            Verdict.PASS,
            Evidence(
                kind=kind,
                summary=summary,
                quote=quote,
                measured=measured,
                **ev_kwargs,  # type: ignore[arg-type]
            ),
            confidence,
        )

    def not_applicable(self, reason: str) -> RuleResult:
        """Uzywaj zawsze, gdy brakuje danych do oceny.

        Krytyczne dla reguly 5: przy background_confidence == "unknown"
        (tlo graficzne) NIE wolno zwrocic `fail`. Falszywy alarm na oczach
        jury jest drozszy niz przyznanie sie do niepewnosci.
        """
        return self._result(
            Verdict.NOT_APPLICABLE,
            Evidence(kind=EvidenceKind.ABSENCE, summary=reason),
            confidence=1.0,
        )
