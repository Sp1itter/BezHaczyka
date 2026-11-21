# analyzer — Moduły Analityczne / AI

Serwis **Osoby B**. Python. Nie zawiera reguł wizualnych (DET) — te liczy
`services/scraper` z geometrii Playwrighta, bo tylko on ma `RenderProbe`.

## Quick start

```bash
cd services/analyzer
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # Windows
# source .venv/bin/activate && pip install -r requirements-dev.txt  # Linux/macOS
.venv/Scripts/python.exe -m pytest tests/ -q
```

Wymagania zewnętrzne: **Ollama** z modelami `SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0`
i `bge-m3`, oraz **ffmpeg** dla speech-to-text.

## Co już jest (gotowe i przetestowane)

| Plik | Co robi | Testy |
|---|---|---|
| `analyzer/contracts.py` | Zamrożone kontrakty danych (par. 6 design doca) | `test_contracts.py` |
| `analyzer/rules_llm/base.py` | Interfejs `Rule` + `RuleBase` z konstruktorami wyników | `test_contracts.py` |
| `analyzer/scoring.py` | `risk_score`, `risk_level`, `is_flagged`, `coverage` | `test_scoring.py` |
| `analyzer/scope_gate.py` | Brama zakresu — kryterium instrumentowe (par. 6.6) | `test_scope_gate.py` |
| `analyzer/router.py` | Tablica decyzyjna R1–R4 (par. 6.5) | `test_router.py` |
| `analyzer/llm.py` | Klient Ollamy (Bielik + bge-m3), wstrzykiwany transport | `test_llm.py` |
| `analyzer/rules_llm/batch_1.py` | Reguły 1, 2, 17, 18 jednym wywołaniem + weryfikacja cytatu | `test_llm.py` |
| `analyzer/prompts/batch_1.txt` | Prompt wsadowy: reguły 1, 2, 17, 18 | — |
| `tools/gen_contract_examples.py` | Generuje `fixtures/contract-examples/` z modeli | — |
| `tools/smoke_llm.py` | Smoke test na żywo — uruchom, gdy Ollama wstanie | — |

Żaden z tych plików nie wymaga działającej Ollamy, więc dało się je napisać
i przetestować, zanim modele się pobrały. Testy używają `httpx.MockTransport`.

## Co trzeba zrobić dalej (kolejność ma znaczenie)

1. **Uruchom `python tools/smoke_llm.py`**, gdy tylko Ollama i Bielik będą
   gotowe. To jedyna rzecz, której testy nie mogą sprawdzić: czy prawdziwy
   model rozumie nasz prompt i trzyma się schematu. Jeśli reguły wyjdą
   `not_applicable` — iteruj `prompts/batch_1.txt`, nie kod.
2. **`analyzer/embeddings.py`** — `bge-m3` przez `client.embed()` → wektor 1024,
   plus `simhash` na znormalizowanym tekście i cosine do dedupu.
3. **`analyzer/rules_llm/registry.py`** — rejestr zbierający reguły DET (od A)
   i LLM (nasze) po wspólnym interfejsie `Rule`.
4. Prompty wsadowe 2–4: reguły `9+10+11`, `12a+12b+14`, `15+16`.
   Kopiuj strukturę z `batch_1.py` — `RULE_META` + `FAIL_MEANS_ABSENCE` i gotowe.
5. **Reguły HYBRID 3 i 13** — potrzebują `RenderProbe` od osoby A.
6. **`analyzer/stt.py`** — `faster-whisper`, `device="cpu"`, `compute_type="int8"`.
7. **`analyzer/module3.py`** — shadow advisory (korzysta z resolvera osoby A).
8. **`tools/evaluate.py`** — precision / recall / F1 / macierz pomyłek.

### Weryfikacja cytatu — zabezpieczenie przed halucynacją

`batch_1.py` sprawdza, czy cytat podany przez model **faktycznie występuje
w materiale** (po normalizacji wielkości liter i białych znaków). Jeśli nie:

- dla reguł **17 i 18** (`fail` twierdzi, że coś w materiale *jest*) —
  `confidence` spada do 40%, cytat jest usuwany, a w `summary` ląduje adnotacja
  o potrzebie weryfikacji ręcznej. Ustalenie zostaje, ale samo się wytłumia
  w `risk_score`, bo `confidence` wchodzi do wzoru.
- dla reguł **1 i 2** (`fail` oznacza, że czegoś *brakuje*) — brak cytatu jest
  poprawny i nie obniża pewności. Lista takich reguł to `FAIL_MEANS_ABSENCE`.

Dodawając kolejne prompty wsadowe, **zadeklaruj dla każdej reguły, czy jej
`fail` oznacza obecność czy brak** — inaczej zabezpieczenie będzie karać
poprawne ustalenia.

## Zasady, których trzymamy się w tym serwisie

- **18 reguł = 4 prompty wsadowe, nie 18 wywołań modelu na dokument.**
  Osiemnaście requestów zabije przepustowość przy 8 GB VRAM.
- **`evidence` reguł LLM zawiera dosłowny cytat, nigdy parafrazę.**
  Nadzorca musi móc odnaleźć fragment w materiale.
- **Brak danych → `not_applicable`, nigdy `fail`.** Fałszywy alarm na oczach
  jury jest droższy niż przyznanie się do niepewności.
- **Whisper na CPU int8.** GPU jest zarezerwowane dla Bielika — przy 8 GB VRAM
  Bielik 4.5B (~5 GB) + bge-m3 (~1,2 GB) mieści się, Whisper by się nie zmieścił.
- **Prompty w plikach `prompts/*.txt`, nie w kodzie.**
- **Nie dotykamy `services/scraper/` ani `services/api/` ani `services/web/`.**

## Brama zakresu — najważniejsza decyzja domenowa

Kryterium jest **instrumentowe, nie aktywowe**. Materiał jest w zakresie, gdy
rozpoznano opakowanie będące instrumentem finansowym wg art. 2 ustawy o obrocie,
**bez względu na aktywo bazowe**.

CFD na kryptoaktywo **jest** instrumentem finansowym (art. 2 ust. 1 pkt 2 lit. h)
i zostaje w zakresie z podwyższonym priorytetem. Poza zakresem jest wyłącznie
zakup spot bez opakowania — reżim MiCA, nie MiFID II.

Słownikowe wykluczanie słów „krypto"/„bitcoin" dawałoby false negative na
najagresywniej reklamowanych produktach detalicznych pod nadzorem KNF.

## Regeneracja przykładów kontraktów

```bash
.venv/Scripts/python.exe tools/gen_contract_examples.py
```

Pliki lądują w `fixtures/contract-examples/` i są walidowane przez
`tests/test_contracts.py`. To mechanizm, który chroni zduplikowany interfejs
`Rule` przed rozjechaniem się z kopią osoby A w `services/scraper/rules_det/base.py`.
