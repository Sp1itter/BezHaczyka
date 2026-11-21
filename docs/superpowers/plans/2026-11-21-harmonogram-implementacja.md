# Harmonogram Modułu 1 — plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dać analyzerowi konfigurowalny autoskaler puli workerów oraz detektor zmian, który z porównania dwóch przebiegów produkuje zdarzenie nadzorcze (np. „ostrzeżenie o ryzyku zostało usunięte").

**Architecture:** Dwa niezależne podsystemy, oba jako **czyste funkcje decyzyjne** oddzielone od efektów ubocznych. Autoskaler: `stan kolejek + konfiguracja → lista decyzji`, a osobny executor je wykonuje (`dry-run` / `pool`). Detektor zmian: `poprzedni Finding + aktualny Finding → ChangeEvent | None`, bez dostępu do bazy i bez modelu. Dzięki temu całość jest testowalna bez Dockera, bez Valkeya i bez Ollamy.

**Tech Stack:** Python 3.12, pydantic 2.9.2, PyYAML 6.0.2, rq 2.9.1, stdlib `http.server`, `subprocess`, `multiprocessing`.

**Spec:** `docs/superpowers/specs/2026-11-22-harmonogram-design.md`

## Global Constraints

- Zakres zmian: **wyłącznie `services/analyzer/`**. Nie dotykamy `services/scraper/`, `services/api/`, `services/web/`, `infra/init.sql` ani niczego związanego ze schematem bazy i scraperem HTML — to obszary innych osób.
- Interpreter: `services/analyzer/.venv/Scripts/python.exe`. Testy uruchamiane z `services/analyzer`.
- Zero nowych zależności. Wolno używać tylko tego, co jest w `requirements.txt`.
- Zero zewnętrznych adresów sieciowych poza `localhost`, `127.0.0.1`, `host.docker.internal` i nazwami serwisów compose. `tools/check_compliance.py` to weryfikuje.
- Komentarze i docstringi po polsku, **bez polskich znaków diakrytycznych w kodzie Python, .yaml i .json** (konwencja repo: „wylacznie", nie „wyłącznie"). W plikach `.md` znaki polskie są OK.
- Brak danych i awarie **nigdy** nie dają `fail` ani wyjątku lecącego w górę — zawsze degradacja z zapisanym powodem.
- Każdy tekst przeznaczony dla nadzorcy (`reason`, `summary`) to zdanie po polsku, nie kod błędu.
- Testy muszą przechodzić **bez** Dockera, Valkeya, Ollamy i `rq`. Zależności zewnętrzne wstrzykiwane.
- Na starcie: 427 testów zielonych. Po każdym zadaniu liczba rośnie, zero regresji.

## Review Focus

Pięć klas wejścia, których specyfikacja nie opisuje, a które urwą się użytkownikowi. Test pinujący każdą z nich jest dopisany do zadania, które jest właścicielem kodu.

1. **Konfiguracja prosząca o więcej workerów GPU niż jest endpointów Ollamy** — musi zostać odrzucona przy starcie z czytelnym komunikatem, a nie wystartować puste workery. (Zadanie 1)
2. **Suma `desired` przekraczająca `hard_max_total`** — przycinanie musi być deterministyczne, inaczej dwa przebiegi na tych samych danych dadzą różny wynik. (Zadanie 2)
3. **Oscylacja skalowania** — backlog chwilowo rośnie i spada; bez histerezy autoskaler będzie startował i zamykał workery w pętli. (Zadanie 2)
4. **`Finding` bez poprzednika** (pierwsze zetknięcie z reklamą) — detektor nie może rzucić wyjątkiem ani wyprodukować fałszywego zdarzenia „zmiana". (Zadanie 5)
5. **Reguła, która w poprzednim przebiegu była `not_applicable`, a teraz jest `fail`** — to NIE jest „usunięcie ostrzeżenia", tylko pojawienie się możliwości oceny. Pomylenie tych dwóch rzeczy da fałszywy alarm nadzorczy. (Zadanie 5)

---

## CZĘŚĆ A — Autoskaler

### Zadanie 1: Konfiguracja skalowania i jej walidacja

**Files:**
- Create: `services/analyzer/analyzer/config/scaling.yaml`
- Create: `services/analyzer/analyzer/scaling.py`
- Test: `services/analyzer/tests/test_scaling_config.py`

**Interfaces:**
- Consumes: `analyzer.config_loader` (wzór ładowania YAML z fallbackiem)
- Produces:
  - `QueuePolicy(name: str, min_workers: int, max_workers: int, scale_up_backlog: int, scale_down_idle_s: int)` — frozen dataclass
  - `ScalingConfig(executor: str, hard_max_total: int, queues: dict[str, QueuePolicy], ollama_endpoints: tuple[str, ...])` — frozen dataclass
  - `ScalingConfigError(ValueError)`
  - `load_scaling_config(path: Path | None = None) -> ScalingConfig`
  - `DEFAULT_SCALING_CONFIG: ScalingConfig`

`scaling.yaml` ma zawierać dokładnie wartości z §4 design doca: `executor: dry-run`, `hard_max_total: 6`, kolejki `ingest {min 1, max 4, scale_up_backlog 10, scale_down_idle_s 300}`, `render {1, 2, 5, 300}`, `gpu {1, 1, 3, 600}`, oraz `ollama_endpoints: [http://host.docker.internal:11434]`. Każda sekcja z komentarzem po polsku wyjaśniającym, co próg znaczy.

- [ ] **Step 1: Write the failing tests**

```python
def test_domyslny_plik_sie_wczytuje():
    cfg = load_scaling_config()
    assert cfg.executor == "dry-run"
    assert cfg.hard_max_total == 6
    assert cfg.queues["gpu"].max_workers == 1

def test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(tmp_path):
    cfg = load_scaling_config(tmp_path / "nie-ma.yaml")
    assert cfg == DEFAULT_SCALING_CONFIG

def test_uszkodzony_yaml_daje_domyslna_konfiguracje(tmp_path):
    p = tmp_path / "scaling.yaml"
    p.write_text("scaling: [to nie slownik", encoding="utf-8")
    assert load_scaling_config(p) == DEFAULT_SCALING_CONFIG

def test_wiecej_workerow_gpu_niz_endpointow_jest_odrzucane(tmp_path):
    # Review Focus 1: puste workery GPU nie daja przepustowosci,
    # bo caly czas analizy to model (zmierzone: 100% czasu).
    p = tmp_path / "scaling.yaml"
    p.write_text(
        "scaling:\n"
        "  executor: dry-run\n"
        "  hard_max_total: 6\n"
        "  queues:\n"
        "    gpu: {min: 1, max: 4, scale_up_backlog: 3, scale_down_idle_s: 600}\n"
        "  ollama_endpoints: ['http://127.0.0.1:11434']\n",
        encoding="utf-8",
    )
    with pytest.raises(ScalingConfigError, match="endpoint"):
        load_scaling_config(p)

def test_min_wieksze_od_max_jest_odrzucane(tmp_path): ...   # ScalingConfigError
def test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(tmp_path): ...  # ScalingConfigError
def test_nieznany_executor_jest_odrzucany(tmp_path): ...    # ScalingConfigError
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_scaling_config.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'analyzer.scaling'`

- [ ] **Step 3: Implement `scaling.yaml` oraz `load_scaling_config` w `analyzer/scaling.py`**

Brakujący albo uszkodzony plik → `DEFAULT_SCALING_CONFIG` z ostrzeżeniem na stderr (wzór: `config_loader.load_thresholds`). Niespełniony **niezmiennik** → `ScalingConfigError` z komunikatem po polsku. Cztery niezmienniki: `min_workers <= max_workers`, `queues["gpu"].max_workers <= len(ollama_endpoints)`, `hard_max_total >= sum(min_workers)`, `executor in {"dry-run", "pool", "compose"}`.

Różnica jest celowa: brak konfiguracji to sytuacja normalna (degradujemy do domyślnej), a konfiguracja wewnętrznie sprzeczna to błąd operatora i musi być głośna.

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_scaling_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/analyzer/analyzer/config/scaling.yaml services/analyzer/analyzer/scaling.py services/analyzer/tests/test_scaling_config.py
git commit -m "feat(analyzer): konfiguracja skalowania z walidacja niezmiennikow"
```

---

### Zadanie 2: Funkcja decyzyjna autoskalera

**Files:**
- Modify: `services/analyzer/analyzer/scaling.py`
- Test: `services/analyzer/tests/test_scaling_decide.py`

**Interfaces:**
- Consumes: `ScalingConfig`, `QueuePolicy` z Zadania 1
- Produces:
  - `QueueState(name: str, backlog: int, workers: int, idle_s: float)` — frozen dataclass
  - `ScalingDecision(queue: str, current: int, desired: int, reason: str, capped_by: str | None)` — frozen dataclass
  - `decide(states: list[QueueState], config: ScalingConfig) -> list[ScalingDecision]`

Algorytm, w tej kolejności (implementer go nie wyznaczy sam):

1. Dla każdej kolejki: `desired = current`.
2. Skalowanie w górę: gdy `backlog >= policy.scale_up_backlog` → `desired = current + 1`.
3. Skalowanie w dół: gdy `backlog == 0` **i** `idle_s >= policy.scale_down_idle_s` → `desired = current - 1`.
   Oba warunki są konieczne — to jest histereza z Review Focus 3.
4. Przycięcie do `[policy.min_workers, policy.max_workers]`; przy trafieniu w górną granicę `capped_by = "max_workers"`.
5. Dla kolejki `gpu`: `desired = min(desired, len(config.ollama_endpoints))`, `capped_by = "ollama_endpoints"` przy trafieniu.
6. Limit globalny: dopóki `sum(desired) > config.hard_max_total`, odejmij 1 od kolejki o **najmniejszym `backlog`** spośród tych z `desired > min_workers`; przy remisie decyduje nazwa alfabetycznie. `capped_by = "hard_max_total"`. Determinizm jest tu wymogiem (Review Focus 2).
7. `reason` to zdanie po polsku, np. `"backlog 12 >= progu 10, zwiekszam z 1 do 2"` albo `"limit globalny hard_max_total=6 osiagniety, zostaje 1"`.

- [ ] **Step 1: Write the failing tests**

```python
def test_brak_backlogu_nie_zmienia_liczby_workerow():
    d = decide([QueueState("ingest", backlog=0, workers=2, idle_s=10)], CFG)
    assert d[0].desired == 2

def test_backlog_powyzej_progu_zwieksza_o_jeden():
    d = decide([QueueState("ingest", backlog=10, workers=1, idle_s=0)], CFG)
    assert d[0].desired == 2
    assert "10" in d[0].reason

def test_skalowanie_w_dol_wymaga_pustej_kolejki_I_bezczynnosci():
    # Review Focus 3: bez obu warunkow autoskaler oscyluje
    assert decide([QueueState("ingest", 0, 3, idle_s=10)], CFG)[0].desired == 3
    assert decide([QueueState("ingest", 5, 3, idle_s=999)], CFG)[0].desired == 3
    assert decide([QueueState("ingest", 0, 3, idle_s=300)], CFG)[0].desired == 2

def test_nie_schodzi_ponizej_min_ani_nie_rosnie_powyzej_max():
    assert decide([QueueState("ingest", 0, 1, idle_s=999)], CFG)[0].desired == 1
    d = decide([QueueState("ingest", 100, 4, idle_s=0)], CFG)[0]
    assert d.desired == 4 and d.capped_by == "max_workers"

def test_gpu_nie_przekracza_liczby_endpointow():
    d = decide([QueueState("gpu", backlog=50, workers=1, idle_s=0)], CFG)[0]
    assert d.desired == 1 and d.capped_by == "ollama_endpoints"

def test_limit_globalny_przycina_deterministycznie():
    # Review Focus 2: dwa przebiegi na tych samych danych daja ten sam wynik
    stany = [QueueState("ingest", 20, 4, 0), QueueState("render", 1, 2, 0),
             QueueState("gpu", 5, 1, 0)]
    a = decide(stany, CFG_HARD_MAX_5)
    b = decide(stany, CFG_HARD_MAX_5)
    assert [x.desired for x in a] == [x.desired for x in b]
    assert sum(x.desired for x in a) <= 5
    assert any(x.capped_by == "hard_max_total" for x in a)

def test_nieznana_kolejka_jest_pomijana_bez_wyjatku(): ...
def test_reason_jest_zdaniem_po_polsku(): ...  # len > 20, nie jest kodem bledu
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_scaling_decide.py -v`
Expected: FAIL, `ImportError: cannot import name 'decide'`

- [ ] **Step 3: Implement `decide` w `analyzer/scaling.py` wg algorytmu powyżej**

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(analyzer): funkcja decyzyjna autoskalera z histereza i limitem globalnym"
```

---

### Zadanie 3: Endpoint `/scaling`

**Files:**
- Modify: `services/analyzer/analyzer/scaling.py`
- Modify: `services/analyzer/analyzer/health.py` (klasa `_Handler`, obecnie obsługuje tylko `GET /health`)
- Test: `services/analyzer/tests/test_scaling_endpoint.py`

**Interfaces:**
- Consumes: `decide`, `ScalingConfig`, `QueueState` z Zadań 1–2
- Produces:
  - `scaling_payload(states: list[QueueState], config: ScalingConfig) -> dict` w `scaling.py`
  - `health.STATE_PROVIDER: Callable[[], list[QueueState]]` — domyślnie `lambda: []`, nadpisywalny w testach i przez workera

Kształt odpowiedzi (§8 design doca):
```json
{"executor": "dry-run", "hard_max_total": 6,
 "queues": [{"name": "ingest", "backlog": 12, "workers": 1, "desired": 2,
             "reason": "...", "capped_by": null}]}
```

- [ ] **Step 1: Write the failing tests**

```python
def test_payload_ma_decyzje_dla_kazdej_kolejki(): ...
def test_payload_jest_serializowalny_do_json(): ...   # json.dumps nie rzuca
def test_endpoint_scaling_zwraca_200_i_json(): ...    # przez _Handler, bez sieci
def test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad(): ...
def test_nieznana_sciezka_nadal_daje_404(): ...       # /health i /scaling, nic wiecej
```

Endpoint testujemy bez otwierania portu: instancja `_Handler` z podstawionym `wfile`/`rfile`, albo wydzielona czysta funkcja routingu zwracająca `(status, body)`. Wybór należy do implementera, ale **test nie może nasłuchiwać na porcie**.

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement `scaling_payload` i routing `/scaling` w `_Handler`**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(analyzer): endpoint /scaling z decyzjami autoskalera"
```

---

### Zadanie 4: Executor `pool`

**Files:**
- Create: `services/analyzer/analyzer/pool.py`
- Test: `services/analyzer/tests/test_pool.py`

**Interfaces:**
- Consumes: `ScalingDecision`, `ScalingConfig` z Zadań 1–2
- Produces:
  - `PoolExecutor(config: ScalingConfig, spawn: Callable[[str], object] | None = None)`
  - `PoolExecutor.apply(decisions: list[ScalingDecision]) -> dict[str, int]` — zwraca faktyczną liczbę workerów per kolejka
  - `PoolExecutor.shutdown() -> None`
  - `DryRunExecutor` z tym samym interfejsem — tylko loguje, nic nie startuje

`spawn` jest wstrzykiwany, żeby testy nie uruchamiały procesów. Domyślnie `subprocess.Popen([sys.executable, "-m", "analyzer.worker", "--queue", nazwa])`.

- [ ] **Step 1: Write the failing tests**

```python
def test_apply_startuje_brakujace_workery(): ...        # fałszywy spawn, licznik wywolan
def test_apply_zamyka_nadmiarowe_workery(): ...
def test_apply_jest_idempotentne(): ...                 # dwa razy ta sama decyzja = zero zmian
def test_padniety_worker_nie_przewraca_executora(): ... # spawn rzuca -> log, idziemy dalej
def test_shutdown_zamyka_wszystkie(): ...
def test_dry_run_nic_nie_startuje(): ...
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement `PoolExecutor` i `DryRunExecutor`**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(analyzer): executor pool i dry-run dla autoskalera"
```

---

## CZĘŚĆ B — Detektor zmian

### Zadanie 5: Kontrakt `ChangeEvent` i diff reguł

**Files:**
- Modify: `services/analyzer/analyzer/contracts.py` (dodać na końcu, **nie zmieniać istniejących modeli**)
- Create: `services/analyzer/analyzer/change_detect.py`
- Test: `services/analyzer/tests/test_change_detect.py`

**Interfaces:**
- Consumes: `Finding`, `RuleResult`, `Verdict`, `RiskLevel` z `contracts.py`
- Produces:
  - `ChangeKind` (str Enum): `OSTRZEZENIE_USUNIETE`, `OSTRZEZENIE_DODANE`, `ESKALACJA_RYZYKA`, `NOWY_WARIANT_KAMPANII`, `TRESC_ZMIENIONA`, `REKLAMA_ZNIKNELA`
  - `RuleDiff(rule_id: str, from_verdict: Verdict, to_verdict: Verdict)` — model pydantic
  - `ChangeEvent` — model pydantic, pola dokładnie jak §10 design doca
  - `RISK_WARNING_RULES: frozenset[str]` = `{"3", "6", "14"}`
  - `diff_rule_results(previous: list[RuleResult], current: list[RuleResult]) -> list[RuleDiff]`

`diff_rule_results` zwraca tylko reguły, których werdykt **się zmienił**, w kolejności `rule_id`. Reguła obecna w jednym przebiegu, a brakująca w drugim, **nie jest** różnicą werdyktu i jest pomijana.

- [ ] **Step 1: Write the failing tests**

```python
def test_identyczne_wyniki_daja_pusty_diff(): ...

def test_zmiana_werdyktu_jest_wykrywana():
    d = diff_rule_results([_r("6", Verdict.PASS)], [_r("6", Verdict.FAIL)])
    assert d == [RuleDiff(rule_id="6", from_verdict=Verdict.PASS, to_verdict=Verdict.FAIL)]

def test_przejscie_z_not_applicable_nie_jest_usunieciem_ostrzezenia():
    # Review Focus 5: not_applicable -> fail znaczy "dalo sie ocenic",
    # NIE "reklamodawca usunal ostrzezenie". Pomylenie da falszywy alarm.
    d = diff_rule_results([_r("6", Verdict.NOT_APPLICABLE)], [_r("6", Verdict.FAIL)])
    assert d[0].from_verdict is Verdict.NOT_APPLICABLE

def test_regula_tylko_w_jednym_przebiegu_jest_pomijana(): ...
def test_diff_jest_posortowany_po_rule_id(): ...
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement `ChangeKind`, `RuleDiff`, `ChangeEvent`, `diff_rule_results`**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(analyzer): kontrakt ChangeEvent i diff wynikow regul"
```

---

### Zadanie 6: Klasyfikacja zdarzenia

**Files:**
- Modify: `services/analyzer/analyzer/change_detect.py`
- Test: `services/analyzer/tests/test_change_detect.py`

**Interfaces:**
- Consumes: wszystko z Zadania 5; `analyzer.embeddings.cosine`, `hamming_distance`, `simhash`, `NEAR_DUPLICATE_COSINE`, `SAME_CAMPAIGN_COSINE`, `SIMHASH_MAX_DISTANCE`
- Produces:
  - `detect_change(previous: Finding, current: Finding, *, previous_doc: AdDocument, current_doc: AdDocument) -> ChangeEvent | None`
  - `detect_disappeared(previous: Finding, *, previous_doc: AdDocument) -> ChangeEvent` — dla pobrania, które zwróciło 404

Pierwszeństwo rodzajów zdarzeń, w tej kolejności (implementer go nie wyznaczy sam):

1. którakolwiek reguła z `RISK_WARNING_RULES` przeszła `pass` → `fail` ⇒ `OSTRZEZENIE_USUNIETE`
2. `risk_level` wzrósł ⇒ `ESKALACJA_RYZYKA`
3. którakolwiek z `RISK_WARNING_RULES` przeszła `fail` → `pass` ⇒ `OSTRZEZENIE_DODANE`
4. `simhash` identyczny ⇒ `None` (brak zdarzenia, brak nowego `Finding`)
5. `cosine >= SAME_CAMPAIGN_COSINE` ⇒ `NOWY_WARIANT_KAMPANII`
6. w pozostałych przypadkach ⇒ `TRESC_ZMIENIONA`

`summary` to zdanie po polsku dla nadzorcy. Dla `OSTRZEZENIE_USUNIETE` musi nazwać regułę i podstawę prawną, np. `"Ostrzezenie o ryzyku zostalo usuniete (regula 6, art. 44 ust. 2 lit. e)."`

Brak `embedding` w którymkolwiek dokumencie ⇒ `cosine` traktujemy jako `0.0` i opieramy się na `simhash`. To degradacja, nie błąd.

- [ ] **Step 1: Write the failing tests**

```python
def test_usuniecie_ostrzezenia_ma_pierwszenstwo_nad_eskalacja(): ...
def test_usuniecie_ostrzezenia_nazywa_regule_i_podstawe_prawna(): ...
def test_identyczny_simhash_nie_daje_zdarzenia(): ...        # None
def test_przeredagowany_wariant_daje_nowy_wariant_kampanii(): ...
def test_istotna_zmiana_tresci_daje_tresc_zmieniona(): ...
def test_brak_embeddingu_degraduje_do_simhasha_bez_wyjatku(): ...
def test_detect_disappeared_daje_reklama_zniknela(): ...
def test_summary_jest_zdaniem_po_polsku(): ...
def test_zmiana_regul_spoza_RISK_WARNING_RULES_nie_daje_usuniecia_ostrzezenia(): ...
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement `detect_change` i `detect_disappeared` wg pierwszeństwa powyżej**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(analyzer): klasyfikacja zdarzen zmiany z pierwszenstwem usuniecia ostrzezenia"
```

---

### Zadanie 7: Brama idempotencji przed kolejką GPU

**Files:**
- Modify: `services/analyzer/analyzer/change_detect.py`
- Test: `services/analyzer/tests/test_idempotency_gate.py`

**Interfaces:**
- Consumes: `detect_change` z Zadania 6; `analyzer.embeddings.simhash_hex`
- Produces:
  - `GateDecision(analyze: bool, reason: str, kind: ChangeKind | None)` — frozen dataclass
  - `should_analyze(previous_doc: AdDocument | None, current_doc: AdDocument) -> GateDecision`

Reguły (§6 design doca):
- `previous_doc is None` ⇒ `analyze=True`, `reason="pierwsze zetkniecie z materialem"` (Review Focus 4)
- `simhash` identyczny ⇒ `analyze=False`, `reason="material bez zmian, podbijam last_seen"`
- inaczej ⇒ `analyze=True` z powodem nazywającym różnicę

Sens biznesowy w docstringu: bez tej bramy harmonogram co 15 minut wrzuca na `q:gpu` materiały, które się nie zmieniły, a przy jednym workerze GPU i 18 s na dokument korkuje kolejkę i produkuje śmietnik identycznych `Finding`.

- [ ] **Step 1: Write the failing tests**

```python
def test_pierwsze_zetkniecie_zawsze_analizujemy(): ...      # Review Focus 4
def test_identyczny_material_nie_idzie_na_gpu(): ...
def test_zmieniony_material_idzie_na_gpu_z_powodem(): ...
def test_brak_simhasha_nie_wywraca_bramy(): ...             # dolicza go sama
def test_reason_zawsze_niepusty(): ...
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement `should_analyze` i `GateDecision`**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(analyzer): brama idempotencji - nowa analiza tylko gdy material sie zmienil"
```

---

## Poza zakresem tego planu — świadomie, z powodem

Autoprzegląd planu wobec design doca wykazał trzy elementy specyfikacji, których tu
nie ma. Nazywam je, zamiast milczeć:

| Element design doca | Dlaczego nie teraz |
|---|---|
| §7 backoff i wyłącznik bezpieczeństwa wobec Meta | Dotyczy wywoływania **scrapera**, a to obszar innej osoby i jawne zastrzeżenie zakresu. Dodatkowo wymaga działającej kolejki Valkey do przechowania stanu zadań, czego nie da się tu zweryfikować. |
| §11.4 pętla orkiestratora na `rq-scheduler` | Wymaga Valkeya i `rq` w locie; nieuruchomialne na tej maszynie, więc oddane byłoby nieprzetestowane. Funkcja decyzyjna (Zadanie 2) i brama (Zadanie 7) są jej mózgiem i **są** testowalne — pętla to tylko ich wywoływanie w czasie. |
| §11.6 para wersji reklamy w korpusie demo | Modyfikacja korpusu należy do właściciela scrapera. Detektor zmian (Zadania 5–6) działa na dwóch `Finding` niezależnie od tego, skąd pochodzą, więc para wersji może dojść później bez zmian w kodzie. |

Executor `compose` z §9 również pozostaje niezaimplementowany — bez Dockera byłby
oddany nieprzetestowany, a historię skalowania opowiada już `DryRunExecutor`
i `PoolExecutor` z Zadania 4.

## Weryfikacja końcowa (po obu częściach)

- [ ] `cd services/analyzer && ./.venv/Scripts/python.exe -m pytest tests/ -q` — zero regresji wobec 427
- [ ] `./services/analyzer/.venv/Scripts/python.exe tools/check_compliance.py` z katalogu głównego — 5× `[OK]`
- [ ] `graphify update .` — graf aktualny (wymóg `CLAUDE.md`)
- [ ] Brak polskich znaków diakrytycznych w nowych plikach `.py`, `.yaml`
