"""Pelny smoke test na zywym modelu: wszystkie 4 wsady + embeddingi.

Uruchomienie (z services/analyzer), bez argumentow:
    python tools/smoke_all.py

Dla kazdego materialu zdefiniowano OCZEKIWANE werdykty regul. Reguly, ktorych
material nie dotyczy, musza byc `pass` albo `not_applicable` (nigdy `fail`),
chyba ze wpisano inaczej. Kod wyjscia 1, gdy sa rozbieznosci.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import AdDocument  # noqa: E402
from analyzer.embeddings import cosine, embed_document_text  # noqa: E402
from analyzer.llm import OllamaClient  # noqa: E402
from analyzer.rules_llm.batch_1 import evaluate_batch_1  # noqa: E402
from analyzer.rules_llm.batch_2 import evaluate_batch_2  # noqa: E402
from analyzer.rules_llm.batch_3 import evaluate_batch_3  # noqa: E402
from analyzer.rules_llm.batch_4 import evaluate_batch_4  # noqa: E402

BATCHES = [
    ("wsad 1 (1,2,17,18)", evaluate_batch_1),
    ("wsad 2 (9,10,11)", evaluate_batch_2),
    ("wsad 3 (12a,12b,14)", evaluate_batch_3),
    ("wsad 4 (15,16)", evaluate_batch_4),
]

ALL_RULES = ["1", "2", "17", "18", "9", "10", "11", "12a", "12b", "14", "15", "16"]

OK_DEFAULT = {"pass", "not_applicable"}
ANY = {"pass", "fail", "not_applicable"}

RISK_PL = (
    "Inwestowanie wiąże się z ryzykiem, w tym z ryzykiem utraty części lub "
    "całości zainwestowanych środków."
)

# nazwa -> (tekst, {regula: dozwolone werdykty}); reszta regul: OK_DEFAULT
MATERIALS: dict[str, tuple[str, dict[str, set[str]]]] = {
    "czysty": (
        "REKLAMA. Alfa Dom Maklerski S.A. oferuje rachunki maklerskie dla "
        "osób prywatnych. Otwórz rachunek online w kilka minut i korzystaj "
        "z prostej aplikacji. " + RISK_PL,
        {},
    ),
    "batch_1 (brak oznaczenia, nadzor jako gwarancja)": (
        "Inwestuj z XYZ Dom Maklerski S.A. i zarabiaj do 18% rocznie! "
        "Nasza inwestycja jest w pełni bezpieczna — spełniamy rygorystyczne "
        "wymogi nadzorcze KNF. Zacznij już dziś, liczba miejsc ograniczona.",
        {
            "1": {"pass"},
            "2": {"fail"},
            "18": {"fail"},
            "17": {"pass", "fail"},
            "15": ANY,
        },
    ),
    "batch_2 (angielskie ostrzezenie, porownanie bez zrodla)": (
        "REKLAMA. Beta Dom Maklerski S.A. — fundusze akcji. Nasze fundusze są "
        "znacznie lepsze i tańsze niż fundusze wszystkich konkurentów. "
        "Risk warning: investing involves risk and you may lose all of your "
        "invested capital. Please read the prospectus before investing.",
        {"10": {"fail"}, "11": {"fail"}, "9": ANY},
    ),
    "batch_3 (wyniki historyczne bez zastrzezen)": (
        "REKLAMA. Gamma Towarzystwo Funduszy Inwestycyjnych S.A. Nasz fundusz "
        "Gamma Akcje przyniósł w ubiegłym roku 32% zysku! Dołącz do "
        "inwestorów, którzy już zarabiają.",
        {"12a": {"fail"}, "12b": {"fail"}, "14": {"fail"}},
    ),
    "batch_4 (prognoza i podatki bez zastrzezen)": (
        "REKLAMA. Delta Dom Maklerski S.A. Z naszym planem oszczędnościowym "
        "za rok zarobisz 20%, a zysk jest zwolniony z podatku. Wpłacaj "
        "co miesiąc i patrz, jak rośnie Twój kapitał.",
        {"15": {"fail"}, "16": {"fail"}},
    ),
}

AD_A = (
    "REKLAMA. Alfa Dom Maklerski S.A. Otwórz rachunek maklerski online "
    "bez opłat za prowadzenie. Inwestowanie wiąże się z ryzykiem utraty kapitału."
)
AD_A2 = (
    "Reklama: Alfa Dom Maklerski S.A. — rachunek maklerski otwierasz online, "
    "bez opłat za prowadzenie rachunku. Inwestowanie niesie ryzyko utraty kapitału."
)
AD_B = (
    "Przepis na szarlotkę: obierz pięć jabłek, wymieszaj z cynamonem i cukrem, "
    "przełóż do formy i piecz w 180 stopniach przez czterdzieści minut."
)


def make_doc(idx: int, text: str) -> AdDocument:
    return AdDocument(
        id=f"smoke-{idx}",
        source="web",
        url=f"https://example.invalid/smoke/{idx}",
        fetched_at=datetime.now(timezone.utc),
        text=text,
    )


def check_embeddings(client: OllamaClient) -> bool:
    print("=== EMBEDDINGI (bge-m3) ===")
    t0 = time.perf_counter()
    ea, ea2, eb = (embed_document_text(t, client) for t in (AD_A, AD_A2, AD_B))
    dt = time.perf_counter() - t0
    if not (ea and ea2 and eb):
        print("BLAD: embedding zwrocil None (model niedostepny?)")
        return False
    same = cosine(ea.vector, ea2.vector)
    diff = cosine(ea.vector, eb.vector)
    ok_dim = ea.dim == 1024 and ea2.dim == 1024 and eb.dim == 1024
    ok_cos = same > diff
    print(f"wymiar: {ea.dim} ({'OK' if ok_dim else 'BLAD, oczekiwano 1024'})")
    print(f"cosine(ta sama reklama, 2 warianty) = {same:.4f}")
    print(f"cosine(dwie rozne reklamy)          = {diff:.4f}")
    print(f"warianty blizsze niz rozne: {'OK' if ok_cos else 'BLAD'}  (czas {dt:.1f} s)\n")
    return ok_dim and ok_cos


def main() -> int:
    client = OllamaClient()
    print(f"Ollama: {client.base_url}  model: {client.model}")
    if not client.health():
        print("BLAD: Ollama nie odpowiada.")
        return 1
    models = client.available_models()
    for needed in (client.model, client.embed_model):
        if needed not in models and f"{needed}:latest" not in models:
            print(f"BLAD: brak modelu {needed} (dostepne: {', '.join(models)})")
            return 1
    print()

    failures = 0
    rows: list[tuple[str, str, str, str, bool]] = []

    for idx, (name, (text, expected)) in enumerate(MATERIALS.items()):
        print(f"=== MATERIAL: {name} ===")
        doc = make_doc(idx, text)
        got: dict[str, str] = {}
        total = 0.0
        for label, fn in BATCHES:
            t0 = time.perf_counter()
            results = fn(doc, client)
            dt = time.perf_counter() - t0
            total += dt
            print(f"  {label}: {dt:.1f} s")
            for r in results:
                got[r.rule_id] = r.verdict.value
                q = f' cytat: "{r.evidence.quote}"' if r.evidence.quote else ""
                print(f"    [{r.verdict.value:>14}] {r.rule_id:>3} {r.evidence.summary}{q}")
        print(f"  SUMA na dokument: {total:.1f} s\n")

        for rule in ALL_RULES:
            allowed = expected.get(rule, OK_DEFAULT)
            actual = got.get(rule, "brak")
            ok = actual in allowed
            if not ok:
                failures += 1
            rows.append((name, rule, "/".join(sorted(allowed)), actual, ok))

    emb_ok = check_embeddings(client)

    print("=== PODSUMOWANIE ===")
    print(f"{'material':<56} {'reg':<4} {'oczekiwano':<26} {'otrzymano':<15} wynik")
    for name, rule, exp, act, ok in rows:
        print(f"{name[:55]:<56} {rule:<4} {exp:<26} {act:<15} {'OK' if ok else 'BLAD'}")
    print(f"\nEmbeddingi: {'OK' if emb_ok else 'BLAD'}")
    print(f"Rozbieznosci regul: {failures} z {len(rows)}")
    return 0 if (failures == 0 and emb_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
