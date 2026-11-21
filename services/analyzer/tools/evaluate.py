"""Metryki trafnosci klasyfikacji ryzyka dla panelu kalibracji (par. 9 design doca).

Skrypt jest czysto obliczeniowy: operuje na zapisanych wynikach (risk_score
z pola `score` w zbiorze zlotym), nie wola modelu ani Ollamy. Flagowanie liczy
`analyzer.scoring.is_flagged`, zeby metryki i panel zawsze uzywaly tego samego
warunku.

Uruchomienie (z services/analyzer):
    ./.venv/Scripts/python.exe tools/evaluate.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.scoring import DEFAULT_FLAG_THRESHOLD, is_flagged  # noqa: E402

# tools/ -> analyzer/ -> services/ -> korzen repo
DEFAULT_GOLD_PATH = Path(__file__).resolve().parents[3] / "fixtures" / "gold" / "labels.json"


@dataclass
class GoldItem:
    """Jedna pozycja zbioru zlotego."""

    id: str
    source: str
    is_violation: bool
    note: str = ""
    rule_labels: dict[str, str] = field(default_factory=dict)
    # risk_score zapisany przez analizator; None = brak wyniku, pozycja pomijana w metrykach
    score: float | None = None


def _ostrzez(komunikat: str) -> None:
    print(f"OSTRZEZENIE: {komunikat}", file=sys.stderr)


def _parse_item(entry: object) -> GoldItem | None:
    """Zamienia surowy obiekt JSON na GoldItem. Zwraca None przy zlej strukturze."""
    if not isinstance(entry, dict):
        return None
    item_id = entry.get("id")
    is_violation = entry.get("is_violation")
    if not isinstance(item_id, str) or not isinstance(is_violation, bool):
        return None

    raw_rules = entry.get("rule_labels")
    rule_labels: dict[str, str] = {}
    if isinstance(raw_rules, dict):
        rule_labels = {str(k): str(v) for k, v in raw_rules.items()}

    raw_score = entry.get("score")
    score: float | None = None
    if isinstance(raw_score, (int, float)) and not isinstance(raw_score, bool):
        score = float(raw_score)

    return GoldItem(
        id=item_id,
        source=str(entry.get("source", "")),
        is_violation=is_violation,
        note=str(entry.get("note", "")),
        rule_labels=rule_labels,
        score=score,
    )


def load_gold(path: Path | str | None = None) -> list[GoldItem]:
    """Wczytuje zbior zloty. Nigdy nie rzuca: przy bledzie zwraca pusta liste.

    Brakujacy plik, uszkodzony JSON i zla strukture raportuje ostrzezeniem na stderr.
    Pojedyncze zle pozycje sa pomijane, reszta zostaje.
    """
    p = Path(path) if path is not None else DEFAULT_GOLD_PATH

    if not p.exists():
        _ostrzez(f"brak zbioru zlotego: {p}. Metryki beda puste.")
        return []

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _ostrzez(f"nie mozna odczytac zbioru zlotego {p} ({exc}). Metryki beda puste.")
        return []

    raw_items = raw.get("items") if isinstance(raw, dict) else None
    if not isinstance(raw_items, list):
        _ostrzez(f"w {p} brakuje listy 'items'. Metryki beda puste.")
        return []

    items: list[GoldItem] = []
    for idx, entry in enumerate(raw_items):
        item = _parse_item(entry)
        if item is None:
            _ostrzez(f"pozycja #{idx} w {p} pominieta: zla struktura lub brak id/is_violation")
            continue
        items.append(item)
    return items


def confusion_matrix(scores: list[float], labels: list[bool], threshold: float) -> dict[str, int]:
    """Macierz pomylek. Material jest 'pozytywny', gdy ma naruszenie (labels=True).

    Blad dlugosci list to blad wywolujacego, wiec rzucamy ValueError.
    """
    if len(scores) != len(labels):
        raise ValueError(f"scores ({len(scores)}) i labels ({len(labels)}) maja rozna dlugosc")

    tp = fp = fn = tn = 0
    for score, is_violation in zip(scores, labels):
        flagged = is_flagged(score, threshold)
        if flagged and is_violation:
            tp += 1
        elif flagged:
            fp += 1
        elif is_violation:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def _safe_div(licznik: float, mianownik: float) -> float:
    """Dzielenie, ktore przy zerowym mianowniku zwraca 0.0 zamiast wyjatku."""
    return licznik / mianownik if mianownik else 0.0


def metrics(scores: list[float], labels: list[bool], threshold: float) -> dict[str, float]:
    """Precision, recall, F1, accuracy oraz liczby z macierzy pomylek.

    Przy progu skrajnym mianownik bywa zerowy (nic nie oflagowane, brak pozytywow),
    wtedy odpowiedni wskaznik wynosi 0.0.
    """
    cm = confusion_matrix(scores, labels, threshold)
    tp, fp, fn, tn = cm["tp"], cm["fp"], cm["fn"], cm["tn"]
    total = tp + fp + fn + tn
    return {
        **cm,
        "precision": _safe_div(tp, tp + fp),
        "recall": _safe_div(tp, tp + fn),
        "f1": _safe_div(2 * tp, 2 * tp + fp + fn),
        "accuracy": _safe_div(tp + tn, total),
    }


def threshold_sweep(
    scores: list[float], labels: list[bool], step: float = 5.0
) -> list[dict[str, float]]:
    """Metryki dla progow 0, step, 2*step, ..., 100 (domyslnie 21 punktow)."""
    if step <= 0:
        raise ValueError("step musi byc dodatni")
    count = int(round(100.0 / step)) + 1
    rows: list[dict[str, float]] = []
    for i in range(count):
        threshold = round(i * step, 6)
        rows.append({"threshold": threshold, **metrics(scores, labels, threshold)})
    return rows


def best_threshold(scores: list[float], labels: list[bool]) -> float:
    """Prog z siatki 0..100 maksymalizujacy F1.

    Przy remisie wybiera prog najblizszy DEFAULT_FLAG_THRESHOLD, zeby rekomendacja
    nie odplywala od domyslnej wartosci bez powodu. Dla pustego zbioru zwraca domyslny prog.
    """
    if not scores:
        return DEFAULT_FLAG_THRESHOLD
    rows = threshold_sweep(scores, labels)
    best = max(
        rows,
        key=lambda r: (r["f1"], -abs(r["threshold"] - DEFAULT_FLAG_THRESHOLD)),
    )
    return float(best["threshold"])


def build_report(items: list[GoldItem]) -> list[str]:
    """Tekst raportu: przemiatanie progow, macierz dla progu domyslnego, rekomendacja."""
    scored = [item for item in items if item.score is not None]
    lines = [f"Zbior zloty: {len(items)} pozycji, z zapisanym score: {len(scored)}"]
    if not scored:
        lines.append("Brak pozycji z polem score. Uzupelnij score z zapisanych wynikow analizatora.")
        return lines
    if len(scored) < len(items):
        lines.append(f"Pominieto {len(items) - len(scored)} pozycji bez score.")

    scores = [item.score for item in scored]
    labels = [item.is_violation for item in scored]

    lines.append("")
    lines.append("Przemiatanie progow:")
    lines.append(f"{'prog':>6} {'TP':>4} {'FP':>4} {'FN':>4} {'TN':>4} {'prec':>7} {'rec':>7} {'f1':>7} {'acc':>7}")
    for row in threshold_sweep(scores, labels):
        lines.append(
            f"{row['threshold']:>6.1f} {row['tp']:>4} {row['fp']:>4} {row['fn']:>4} {row['tn']:>4} "
            f"{row['precision']:>7.3f} {row['recall']:>7.3f} {row['f1']:>7.3f} {row['accuracy']:>7.3f}"
        )

    cm = confusion_matrix(scores, labels, DEFAULT_FLAG_THRESHOLD)
    lines.append("")
    lines.append(
        f"Macierz pomylek dla progu domyslnego {DEFAULT_FLAG_THRESHOLD:.1f}: "
        f"TP={cm['tp']} FP={cm['fp']} FN={cm['fn']} TN={cm['tn']}"
    )

    best = best_threshold(scores, labels)
    best_m = metrics(scores, labels, best)
    lines.append(
        f"Rekomendowany prog (max F1): {best:.1f} "
        f"(F1={best_m['f1']:.3f}, precision={best_m['precision']:.3f}, recall={best_m['recall']:.3f})"
    )
    return lines


def main() -> int:
    items = load_gold()
    for line in build_report(items):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
