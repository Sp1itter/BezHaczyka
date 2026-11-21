# InvestWatch — stan projektu

**Aktualizacja:** 2026-11-21, noc · **Deadline oddania:** 2026-11-22, 11:00

Dokument dla całego zespołu. Opisuje stan **faktyczny**, nie zamierzony — jeśli coś
jest niezweryfikowane, jest to napisane wprost.

---

## 1. Co działa i jest zweryfikowane

### Osoba A — `services/scraper` (zmergowane, PR #2)

| Element | Stan |
|---|---|
| `FacebookAdsSource` z trybem replay | ✅ |
| `RenderProbe` (geometria renderu, 3 viewporty) | ✅ |
| Reguły DET 4–8, z nadpisaniami typografii Meta | ✅ **tylko dla FB**; brak `rules_det/` dla innych źródeł |
| Korpus 8 reklam z Meta Ad Library (`page.html` + `node.json.gz`) | ✅ |
| Złoty `AdDocument` + `RuleResult` jako przykłady kontraktowe | ✅ |

### Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`)

**640 testów przechodzi** (2 pominięte: E2E bazy bez Postgresa), kontrola zgodności 5× OK, zweryfikowane na żywym Bieliku.

| Element | Stan |
|---|---|
| Kontrakty danych (pydantic) | ✅ pola **identyczne** z kopią scrapera, pilnuje test |
| Brama zakresu (kryterium instrumentowe) | ✅ CFD/ETP na krypto **zostaje** w zakresie |
| Router R1–R4 | ✅ |
| 12 reguł LLM w 4 wsadach wsadowych | ✅ |
| Strażnicy w kodzie (`rules_llm/guards.py`) dla obiektywnych elementów reguł 2, 12a, 12b, 14, 16, 17 i warunku „odwołanie do nadzoru” dla 17/18 | ✅ Bielik ignorował część poleceń promptu |
| Reguła 3 (hybrydowa: geometria / czas / tekst) | ✅ |
| Reguła 10 (hybrydowa: spójność językowa) | ✅ |
| Reguła 13 (hybrydowa: dominacja wyników historycznych, `font_px`/`bbox` z RenderProbe) | ✅ — Moduł 2 ma komplet 18 reguł |
| Reguła 3: dowód proporcjonalności (czcionka ostrzeżenia / czcionka obietnicy zysku) w `evidence.measured` | ✅ |
| Reguły DET 4–8 liczone w analyzerze z RenderProbe, gdy scraper ich nie dał (poza FB) | ✅ `rules_det_fallback.py`; przeważająca czcionka liczona **bez** węzłów ostrzeżenia |
| Reguły DET 4–8 bez RenderProbe → `not_applicable` z powodem (nie znikają, `coverage` nie jest zawyżone) | ✅ |
| Worker przyjmuje payload scrapera z pełnym `AdDocument`; `FINDINGS_OUT_DIR` zapisuje Finding do pliku, gdy API nie ma | ✅ |
| Moduł 3 — shadow advisory | ✅ |
| Scoring + eskalacja po najcięższym naruszeniu | ✅ |
| Embeddingi bge-m3 (1024) + simhash + dedup kampanii | ✅ |
| Worker kolejki `q:gpu` + klient API + `/health` | ✅ |
| Whisper dla wideo bez napisów (FB) | ✅ faster-whisper small, CPU int8, **bez ffmpeg**; media z `media[]`: plik, http(s), `s3://`; E2E na polskim nagraniu: 4,7 s na 18 s audio |
| Napisy YouTube z casedb (klipy ≤ 2×30 s) jako transkrypcja **częściowa** | ✅ FAIL reguł „brak” (1, 2, 3, 11, 12a, 12b, 14, 15, 16) → `not_applicable`: brak ostrzeżenia w klipie nie dowodzi braku w filmie |
| Most do `services/casedb` | ✅ `tools/casedb_batch.py`: tryb plikowy (zweryfikowany na żywo) i `--db` (claim SKIP LOCKED, statusy, upsert `ai_results`, `--retry`) — `--db` testowany tylko na atrapie, brak Postgresa na maszynie |
| Pełny potok w produkcyjnych punktach wejścia | ✅ **naprawione**: worker RQ wołał analizę z pustą konfiguracją (zero reguł LLM); teraz `registry.default_config()` |
| Metryki: macierz pomyłek, F1, przemiatanie progów | ✅ |
| Dockerfile analyzera | ✅ napisany, **nieprzetestowany** (brak Dockera) |

### Osoba C — `services/api`, `services/web`

**Minimum działa lokalnie (bez Dockera).** API: dokumenty, findingi z filtrami,
zmiana statusu, `/stats`, `/calibration`, WebSocket `/ws/alerts`; 25 testów, a
`ApiClient` analyzera sprawdzony przeciw niemu (pobranie dokumentu + `POST /findings`).
Dashboard: tabela + szczegóły z dowodami, przegląd z wykresami, panel kalibracji
liczony po stronie klienta (zgodny z `evaluate.py`: próg 50 → TP 0, FP 0, FN 3, TN 5),
alerty na żywo. **Zweryfikowane w Dockerze:** postgres + api + web z compose, 45 testów API
na SQLite i na Postgresie, dashboard na `localhost:8090` z alertami przez nginx.

---

## 2. Pomiary na żywym modelu

Sprzęt: RTX 3070 Ti Laptop, **8 GB VRAM**, 15,3 GB RAM. Profil `gpu8`.

| Metryka | Wartość |
|---|---|
| Jedno wywołanie wsadowe Bielika | 3–8 s |
| Pełna analiza dokumentu (4 wsady + reguły) | ~23 s |
| Powtarzalność werdyktów | ✅ `temperature 0` + stały `seed`, 3 identyczne przebiegi |
| Embeddingi bge-m3 | wymiar 1024 |
| Cosine: warianty tej samej reklamy | 0,9733 |
| Cosine: dwie różne reklamy | 0,3041 |
| Smoke test 4 wsadów × 5 materiałów | **0 rozbieżności na 60** |

---

## 3. Trafność Modułu 2 — pomiary na żywym Bieliku 4.5B (21.11, noc)

Trzy zbiory syntetyczne (fikcyjne firmy, `example.invalid`, etykiety nadane **przed**
uruchomieniem modelu i zacommitowane przed poprawkami — historia gita to dokumentuje)
oraz prawdziwy korpus FB.

| Zbiór | Etykiet | Przed | Po | Uwagi |
|---|---|---|---|---|
| `fixtures/module2-cases/` (strojenie) | 73 | 79% | **96%** | na tym zbiorze projektowano strażników — wynik optymistyczny |
| `fixtures/module2-holdout/` (kontrolny 1) | 83 | 75% | 89% | po wykryciu na nim błędów uogólnienia **nie jest już czysty** |
| `fixtures/module2-holdout-2/` (kontrolny 2) | 99 | — | **82%** | **czysty**: autor nie widział kodu, zbiór nieużyty do strojenia — to uczciwa miara |

Najsłabsze na czystym zbiorze: reguła 3 (71%), 15 (67%), 2 i 12b i 18 (75%).
Fałszywe alarmy (FP) na czystym zbiorze: 4 na 99 etykiet (reguła 2: 3, reguła 3: 1).
Uruchomienie: `tools/eval_rules.py [--cases ...]`, wyniki w `eval_results.json` przy zbiorach.

**Co podniosło trafność:** Bielik 4.5B ignoruje część poleceń promptu i „widzi”
w tekście zastrzeżenia, których nie ma. Obiektywne elementy rozstrzygamy więc
w kodzie (`rules_llm/guards.py`, `preconditions.py`), model ocenia tylko to,
co wymaga rozumienia języka.

### Zbiór złoty — 8 prawdziwych reklam FB (`fixtures/gold/`)

```
F1 maksymalne:            0,571 (próg 25)      — wcześniej 0,545
Przy progu domyślnym 50:  TP=0  FP=0  FN=3  TN=5
```

Złapana i usunięta regresja: pośredni stan poprawek dał na tym korpusie dwa fałszywe
naruszenia reguły 18 (model zmyślił „powoływanie się na nadzór KNF” w reklamie
apartamentu) i score 90 dla reklamy bez naruszenia. Teraz 0 takich alarmów.

**Niskie F1 to pokrycie, nie klasyfikator:** `coverage` 0,00–0,42; 5 z 8 reklam to
wideo bez transkrypcji (brak plików mp4 w repo), 7 z 8 nie ma `RenderProbe`, a 8 pozycji
to za mało na stabilne metryki. Etykiety `is_violation` nadane z treści, bez patrzenia
na score.

---

## 4. Decyzje podjęte w trakcie, których nie ma w pierwotnym design docu

Każda wynikła z problemu znalezionego na prawdziwych danych, nie z teorii.

| Decyzja | Dlaczego |
|---|---|
| `temperature 0` + stały `seed` | Przy 0,1 ta sama reklama raz łamała reguły 1, 2 i 18, raz tylko 1 i 2. Nadzorca nie może dostawać innego ustalenia przy każdym odświeżeniu, a demo musi zachować się jak na próbie. |
| `risk_level` eskaluje po najcięższym naruszeniu | Proporcjonalny score rozcieńczał poważne naruszenie: to samo `fail` o wadze 5 dawało 45 pkt przy 2 zdanych regułach i **17 przy 8**. Nadzorca nie myśli „narusza 1 z 9 wymogów", tylko „narusza art. 44 ust. 8". |
| Bramka warunku wstępnego w kodzie | Bielik 4.5B ignorował warunek z promptu i dawał `fail` dla reguł 12a/12b/14 na materiale z samą prognozą. Fałszywy alarm to najgorszy kierunek błędu w narzędziu nadzorczym. |
| Reguła 10 hybrydowa, nie LLM | Model konsekwentnie uznawał angielskie ostrzeżenie w polskiej reklamie za zgodne. Zadanie jest mierzalne, więc mierzymy. |
| Moduł 2 jako ocena **bazowa** każdego materiału w zakresie | R4 dawało `modules=[]`, więc każda świeżo zescrapowana reklama (bez dopasowania do rejestru KNF) nie była oceniana w ogóle — razem z gotowymi wynikami DET. Wymogi art. 44 dotyczą materiału, nie statusu publikującego. |
| `det_results` w payloadzie zadania, nie w `AdDocument` | Kontrakt dokumentu zostaje nietknięty, a API osoby C nie wymaga zmian. |
| Transkrypcja jako etap ①, warunek medialny nie modułowy | Jajko i kura: moduł wyznacza router, router czyta sygnały z tekstu, a w wideo mogą one istnieć tylko w narracji. |
| Ollama **nie** jest serwisem w compose | Konteneryzacja wymagałaby przepuszczania GPU; członkowie zespołu z AMD/Intelem dostaliby tylko CPU. Ollama działa natywnie, kontenery celują w `host.docker.internal:11434`. |
| `rq` i `redis` wyrównane do wersji scrapera | Mieliśmy `rq 1.16.2` przy `2.9.1` u A, na **tych samych kolejkach**. RQ zmieniło format zadań między 1.x i 2.x. |

---

## 5. Do zrobienia

### Nasze (Osoba B) — Moduł 1, harmonogram
Specyfikacja, część „Harmonogram": *CronJob jako mechanizm uruchamiania scrapperów
lub system orchestratora.* Moduł 1 wymaga też wprost **mechanizmu okresowej
aktualizacji**. Projekt: `docs/superpowers/specs/2026-11-22-harmonogram-design.md`.

### Osoba A
1. **Transkrypcje albo pliki wideo** — to największy pojedynczy zysk w całym projekcie.
   Albo uzupełnić `media[]` i dostarczyć mp4 (nasz resolver je znajdzie), albo
   przetranskrybować u siebie i wstawić gotowy `transcript` do `AdDocument`.
   Podniesie pokrycie dwukrotnie i odblokuje osie czasowe reguł 3 i 10.
2. `RenderProbe` dla pozostałych 7 reklam korpusu — odblokuje reguły DET 4–8.
3. ~~Reguła 13~~ — zrobiona po stronie analyzera (B), korzysta z RenderProbe.

### Osoba C
1. Uruchomić w compose pozostałe serwisy (valkey, seaweedfs, nginx, analyzer) i przejść GATE 1 na jednym dokumencie.
2. Prawdziwe findingi z korpusu w bazie (analyzer → `POST /findings`) zamiast samych przykładów kontraktowych.
3. Wycinki `screenshot_crop` przy dowodach, widok zmian w czasie (`ChangeEvent`), `npm audit`.

### Wspólne, blok dokumentacyjny
`README.md` (Quick Start ≤ 1 ekran), `docs/AI_PROCESS.md` (**20% oceny**),
`docs/LICENSES.md`, prezentacja PDF, opcjonalny film ≤ 3 min.

---

## 6. Do udoskonalenia — uszeregowane po wpływie na demo

1. **Pliki wideo korpusu FB i pełne napisy YouTube.** Ścieżka Whisper działa
   (E2E na polskim nagraniu), brakuje tylko plików mp4 w `media[]`. Scraper YouTube
   pobiera pełne napisy, ale oddaje tylko klipy ≤ 2×30 s — **prośba do osoby A:**
   dodać w `services/scraper/youtube/demo.py::analyze` pole `"transcript": captions`
   (lista `{text,start,duration}`); adapter casedb już je obsługuje jako transkrypcję pełną.
2. **Wykrywanie zmian w czasie** (część harmonogramu). „Reklama X: 21.11 ostrzeżenie
   obecne → 22.11 usunięte" to najmocniejszy możliwy moment demo i realna wartość
   nadzorcza. Opis w design docu harmonogramu.
3. **Panel kalibracji z prawdziwymi liczbami.** Dane są gotowe (`fixtures/gold/`,
   `tools/evaluate.py`), brakuje frontu.
4. **Próg domyślny.** Przy 50 nic się nie flaguje na naszym korpusie; rozkład score
   to 0–42. Do decyzji: obniżyć domyślny próg czy zostawić i pokazać na demo, jak
   suwak zmienia wynik. Rekomendacja: **zostawić i pokazać** — to dokładnie to,
   co jury testuje, a eskalacja `risk_level` i tak wyciąga poważne naruszenia.
5. **Więcej pozycji w zbiorze złotym.** Przy 8 metryki są szumne.
6. Wycinki screenshotów przy `evidence` (mocny wizualnie dowód).
7. Najsłabsze reguły na czystym zbiorze kontrolnym: 3, 15, 2, 12b, 18 (67–75%).

---

## 7. Znane ograniczenia — mówimy je wprost

- **Tryb `--db` mostu casedb nie był uruchomiony na prawdziwym Postgresie** (brak Dockera i bazy na maszynie dewelopera) — testowany na atrapie połączenia; tryb plikowy zweryfikowany na żywo.

- **`infra/.env.example` ma `OLLAMA_TEMPERATURE=0.1` i nie ma `OLLAMA_SEED`.** Kod domyślnie używa `0` + seed 42 (patrz §4); compose z tym plikiem nadpisze to na 0,1 i werdykty przestaną być powtarzalne. Poprawka: `OLLAMA_TEMPERATURE=0`, `OLLAMA_SEED=42`.
- **Coverage na korpusie (przeliczone 21.11 wieczór, mianownik 19 reguł): 0,00–0,42.** Wcześniej reguły DET bez wyniku znikały z mianownika.

- **Docker nie był uruchomiony.** Dockerfile analyzera i cały `infra/` są napisane,
  ale nigdy nie zbudowane ani nie wystartowane. Brak Dockera na maszynie dewelopera.
- **Testy scrapera nie były u nas uruchamiane** — brak jego venva (Playwright).
  Nie tknęliśmy natomiast ani jednego jego pliku.
- **Ścieżka STT nieuruchomiona** — `media[]` jest puste we wszystkich 8 dokumentach,
  a pliki mp4 są w `.gitignore` i leżą tylko na maszynie, która je nagrała.
- **Pokrycie reguł 0,00–0,46** z powodów z sekcji 3.
- Dla fraz „zarządzanie majątkiem" i „CFD" `discover` Meta zwrócił 0 reklam; nie
  ustalono, czy to brak aktywnych reklam, czy inny wariant strony wyników.

---

## 8. Mapa odpowiedzialności za reguły

| Reguły | Silnik | Właściciel | Stan |
|---|---|---|---|
| 1, 2, 9, 11, 12a, 12b, 14, 15, 16, 17, 18 | LLM | B | ✅ |
| 3 | HYBRID (geometria / czas / tekst) | B | ✅ |
| 10 | HYBRID (język) | B | ✅ |
| 4, 5, 6, 7, 8 | DET (geometria renderu) | A | ✅ |
| 13 | HYBRID (dominacja wyników hist.) | B (RenderProbe od A) | ✅ |
| M3 | LLM + rejestr | B | ✅ |
