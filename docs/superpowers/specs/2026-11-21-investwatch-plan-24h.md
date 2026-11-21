# InvestWatch — plan wykonawczy 23 h

**Start:** 2026-11-21, 11:50 · **Hard deadline oddania:** 2026-11-22, **11:00**
**Submit o:** 10:15 (45 min buforu — po 11:00 regulamin nie dopuszcza oceny)
**Zespół:** 3 osoby · Design: `2026-11-21-investwatch-design.md`

---

## Co zmieniło się po review zespołu (wersja 2)

Osiem uwag z przeglądu, z czego sześć zmieniło plan istotnie. Dla orientacji, czego nie
szukać w starej wersji:

| Uwaga | Zmiana |
|---|---|
| Licencje pod wdrożenie w UKNF | `redis:7` → **Valkey** (BSD-3), MinIO → **SeaweedFS** (Apache-2.0); nowa §3.1 z tabelą licencji + `docs/LICENSES.md` w oddaniu |
| Embeddingi wymagane przez specyfikację | Warstwa wektorowa (**bge-m3** + pgvector) **zdjęta z drabinki cięcia**, dostała trzy realne zadania: dedup kampanii, kNN jako druga opinia, wyszukiwanie semantyczne (§6.7) |
| Filtr krypto wycinałby CFD | Słownikowy filtr **zastąpiony bramą zakresu opartą na opakowaniu instrumentu** (§6.6). CFD na BTC jest w zakresie — art. 2 ust. 1 pkt 2 lit. h |
| Brak routera modułów | Nowy **ROUTER** z tablicą decyzyjną R1–R4 (§6.5); `Finding.module` → `primary_module` + `modules[]` + `routing.reason` |
| Pułapki `RenderProbe` | Nowa §6.2.1: kompozycja tła po przodkach + `background_confidence`, **zakaz klikania**, detekcja stanu zwiniętego statycznie |
| Konflikt o VRAM | Nowa §9.1: kolejka **`q:gpu` z jednym workerem**, Whisper na CPU int8, Chromium `--disable-gpu`, profile `cpu`/`gpu8`/`gpu16` |
| Przeciążenie osoby B | Reguły DET i rejestr KNF → **A**, oznaczanie zbioru złotego → **C**; etykiety korpusu demo darmowe z konstrukcji |
| WebSockety na drabince cięcia | **Usunięte z drabinki** — są wprost w specyfikacji i na liście testów jury, a w FastAPI kosztują ~20 linii |

---

## Podział roli

| Osoba | Rola | Odpowiada za |
|---|---|---|
| **A** | Dane, render, reguły wizualne | `services/scraper`, `RenderProbe`, **reguły DET 4,5,6,7,8**, źródła, SeaweedFS, kolejki RQ, scheduler, **rejestr KNF + fuzzy matching**, korpus demo + jego etykiety |
| **B** | AI, reguły semantyczne, logika | `services/analyzer`, Ollama/Bielik, **reguły LLM (4 prompty wsadowe) + HYBRID 3, 13**, embeddingi, brama zakresu, router, Moduł 3, scoring, skrypt metryk |
| **C** | API, dashboard, oznaczanie | `services/api`, Postgres+pgvector, WebSocket, `services/web`, panel kalibracji, wykresy, docker-compose, **oznaczanie zbioru złotego z danych prawdziwych**, README |

**Przebudowa po review (poprzedni podział przeciążał osobę B i został odrzucony):**

Pierwotnie osoba B miała między 15:20 a 22:00 zrobić 18 reguł, prompty, Whisper, Moduł 1,
Moduł 3 i 50 ręcznych etykiet. To było nierealne i słusznie zostało zakwestionowane.
Trzy przesunięcia naprawiają bilans:

1. **Reguły DET (4, 5, 6, 7, 8) → osoba A.** Liczą się wyłącznie z `RenderProbe`, który A
   buduje i którego semantykę zna najlepiej. Przekazywanie tej wiedzy do B było sztucznym
   kosztem komunikacji. To zdejmuje z B pięć reguł i całą pracę z geometrią.
2. **Rejestr KNF i fuzzy matching (warstwa podmiotowa Modułu 1) → osoba A.** To scraping
   plus `rapidfuzz`, czyli dokładnie domena A, nie domena modeli.
3. **Oznaczanie zbioru złotego → osoba C**, i to na mocno zmniejszonym zakresie:
   **korpus demo piszemy sami, więc jego etykiety znamy z konstrukcji** i zapisujemy
   w tym samym commicie co plik HTML (`fixtures/demo-ads/<nazwa>.labels.json`).
   Ręcznie trzeba oznaczyć ~35 materiałów prawdziwych, nie 50.

**Przeliczenie zakresu B:** 12 reguł LLM to nie 12 jednostek pracy, a **4 prompty wsadowe**
po 3–4 reguły (inaczej 18 wywołań modelu na dokument zabije przepustowość). Realny zakres B
to: 4 prompty + 2 reguły hybrydowe + router + brama zakresu + embeddingi + Whisper + scoring.
Nadal najtrudniejsza rola, ale wykonalna.

**Zasada integracji:** nikt nie czeka na nikogo. Kontrakty z sekcji 6 design doca są zamrożone
o 12:30, a do czasu gotowości serwisów każdy pracuje na własnym pliku-przykładzie
(`fixtures/contract-examples/*.json`) zgodnym z kontraktem.

**Zasada antykolizyjna:** A pisze reguły DET w `services/scraper/rules_det/`, B pisze reguły
LLM w `services/analyzer/rules_llm/`. Rejestr reguł zbiera jedne i drugie po wspólnym
interfejsie `Rule`. Dzięki temu A i B **nie dotykają tych samych plików** przez całą noc.

---

## T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min)

Najważniejsze 40 minut całego hackathonu. Nie kodujemy jeszcze — ustawiamy tory.

**Natychmiast, w pierwszych 5 minutach, w tle (to są największe pobrania, blokują wszystko):**
```bash
# Osoba B, uruchom OD RAZU i zostaw w tle:
ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0     # ~5.1 GB, Apache-2.0
ollama pull bge-m3                                        # ~1.2 GB, MIT, embeddingi
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M    # ~7 GB, zapas na profil gpu16
python -c "from faster_whisper import WhisperModel; WhisperModel('medium', compute_type='int8')"

# Osoba A, uruchom OD RAZU:
playwright install chromium
docker pull postgres:16 nginx:alpine
docker pull valkey/valkey:8-alpine          # BSD-3, NIE redis:7 (SSPL)
docker pull chrislusf/seaweedfs:latest      # Apache-2.0, NIE minio (AGPLv3)
docker pull pgvector/pgvector:pg16          # obraz postgresa z pgvector w komplecie
```

**Równolegle, w tych samych 40 minutach:**
- [ ] **A:** idzie na stoisko UKNF i **odbiera pendrive z próbkami danych** (§7 opisu wyzwania).
      To jedyne zadanie poza budynkiem — zrobić teraz, nie o 3 w nocy.
- [ ] **C:** tworzy repo, strukturę katalogów z design doca, pusty `docker-compose.yml`
      ze wszystkimi serwisami (puste Dockerfile), `.env.example`, `.gitignore`, pusha `main`.
- [ ] **B:** zapisuje `fixtures/contract-examples/` — po jednym ręcznie napisanym JSON-ie
      dla `AdDocument`, `RenderProbe`, `RuleResult`, `Finding`, `scope`. **To jest kontrakt.**
- [ ] **A i B razem, 5 minut:** ustalcie sygnaturę interfejsu `Rule`. Reguły DET pisze A,
      reguły LLM pisze B, ale rejestr zbiera jedne i drugie — jeśli interfejs się rozjedzie,
      integracja o 19:00 padnie. Zapiszcie go w `services/common/rule.py` i nie ruszajcie.
- [ ] **Wszyscy:** 10 min na przeczytanie sekcji 6 i 7 design doca. Pytania zadajemy teraz,
      nie o 20:00.

**Decyzje do podjęcia i zapisania teraz (nie wracamy do nich):**
- Nazwa projektu i tytuł zgłoszenia.
- Kto prowadzi demo przed jury (jedna osoba, pozostałe dwie odpowiadają na pytania).
- Rotacja snu (patrz blok 02:00).

**GATE T-0:** repo na GitHubie, wszyscy mają sklonowane, pobrania modeli lecą w tle,
pendrive odebrany, kontrakty w repo.

---

## T+1 — 12:30–15:00 · Pionowe cięcia (2,5 h, równolegle)

Każdy buduje **najcieńszą możliwą ścieżkę end-to-end** w swoim serwisie. Zero dopieszczania.

### A — scraper + reguły DET
- [ ] `Source` protocol + `LocalCorpusSource` (czyta `fixtures/demo-ads/*.html`).
- [ ] Playwright headless z `--disable-gpu`: otwórz stronę → **`RenderProbe` dla viewportu
      `mobile`** (tylko jeden na razie). Zbierz: `text`, `font_px`, `color`, `bbox`,
      `visible`, `dom_path`.
- [ ] **Tło efektywne wg algorytmu z §6.2.1 design doca** — wejście w górę drzewa, kompozycja
      alfa, `background_confidence`. Nie bierz `backgroundColor` z węzła tekstowego,
      prawie zawsze zwraca `rgba(0,0,0,0)`.
- [ ] `dominant_font_px` = mediana `font_px` ważona długością tekstu.
- [ ] **Reguły DET 4 (czcionka) i 5 (kontrast)** w `scraper/rules_det/`, po wspólnym
      interfejsie `Rule`. Reguła 5 przy `background_confidence == "unknown"` zwraca
      `not_applicable`, **nigdy `fail`**.
- [ ] Zapis `AdDocument` jako JSON do pliku. Postgres podłączamy później.
- [ ] 3 pierwsze pliki w `fixtures/demo-ads/` **wraz z plikami `.labels.json`**:
      jedna reklama czysta, jedna z ostrzeżeniem 7 px, jedna z ryzykiem w `<details>`.

### B — analyzer
- [ ] Rejestr reguł: `Rule` z `id`, `engine`, `severity`, `legal_basis`, `evaluate(doc) -> RuleResult`.
      **Ten interfejs musi pasować też do reguł DET osoby A** — ustalić w 5 minut na starcie.
- [ ] Klient Ollamy. **Pierwszy prompt wsadowy** (reguły 1, 2, 17, 18) z wymuszonym JSON-em.
      Reguła 18 (nadzór jako argument bezpieczeństwa) jest najefektowniejsza na demo.
- [ ] **Embeddingi:** `bge-m3` przez Ollamę → wektor 1024, zapis do `AdDocument.embedding`.
      Plus `simhash` na znormalizowanym tekście.
- [ ] Funkcja `score(rule_results) -> risk_score` wg wzoru z §9 design doca.
- [ ] Prompty w `analyzer/prompts/batch_N.txt`, nie w kodzie.

### C — api + web
- [ ] Postgres z pgvector: `documents` (z kolumną `vector(1024)`), `findings`,
      `authorized_entities`. `rule_results` jako `JSONB`.
- [ ] FastAPI: `POST /documents`, `GET /findings` (filtry: data, źródło, poziom, moduł, zakres),
      `PATCH /findings/{id}/status`, `WS /ws/alerts`.
- [ ] React + Vite: tabela findingów z filtrami, zaciągana z API.
- [ ] `docker compose up` stawia **pgvector + valkey + seaweedfs + nginx + api + web**.
- [ ] ESLint z `no-console: error` **od początku** (potem nikt tego nie posprząta).

**GATE 1 — 15:00, 20 min, wszyscy razem**
Jeden plik HTML z `fixtures/demo-ads/` → scraper → analyzer → API → **wiersz widoczny
w przeglądarce z oceną 6 reguł (DET 4, 5 od A + wsad 1, 2, 17, 18 od B) i risk_score**. Jeśli to nie działa o 15:20, przerywamy
wszystko inne i naprawiamy integrację. Przepływ przez wszystkie 4 serwisy jest ważniejszy
niż jakakolwiek funkcja.

---

## T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### A — scraper + reguły DET
- [ ] `RenderProbe` na **3 viewportach** (1920 / 768 / 390) → odblokowuje regułę 8.
- [ ] `behind_interaction` **wyłącznie detekcją statyczną, bez klikania** — tablica sygnałów
      z §6.2.1 design doca (`details` bez `open`, `display:none`, `max-height:0`+`overflow`,
      `clip-path: inset(100%)`, `aria-expanded="false"`, `aria-hidden`, `<a href>`, `<dialog>`).
      Zapisuj, który sygnał zadziałał, w `collapsed_evidence`.
      **Klikanie jest zakazane** — wywołuje nawigację i psuje DOM. Jeśli trzeba rozwinąć
      `<details>`, to przez `page.evaluate(el => el.open = true)` na świeżej stronie.
- [ ] Przewijanie do końca strony (limit ~10 kroków) przed sondowaniem — bez tego stopka
      z ryzykiem może nie istnieć w DOM (lazy loading).
- [ ] `in_footer` + pozycja względna `bbox.y / page_height_px` → odblokowuje regułę 6.
- [ ] **Reguły DET 6, 7, 8** (4 i 5 już są z poprzedniego bloku). Komplet DET gotowy.
- [ ] Screenshoty pełnej strony + **wycinki `bbox` dla ostrzeżenia o ryzyku** → SeaweedFS.
      Te wycinki są tym, co jury zobaczy obok liczb. Nie pomijać.
- [ ] **Trzy kolejki RQ:** `q:ingest` (n=4), `q:render` (n=2), `q:gpu` (n=1).
      Jeden worker na `q:gpu` to zabezpieczenie przed konfliktem o VRAM (§9.1).
- [ ] `WebPageSource` dla prawdziwych stron. Rotacja User-Agent z listy w `.env`.
- [ ] Korpus demo rośnie do **12 plików** + `.labels.json` do każdego.
      Dorzuć parę z tłem graficznym pod ścieżkę `background_confidence: "unknown"`.

### B — analyzer
- [ ] **Pozostałe 3 prompty wsadowe** (łącznie 4): reguły 9+10+11, 12a+12b+14, 15+16.
      Grupowanie jest konieczne — 18 osobnych wywołań na dokument zabije przepustowość.
- [ ] **Reguły HYBRID: 3 i 13.** Reguła 3: LLM zwraca cytaty twierdzeń o zyskach → DET
      sprawdza odległość `bbox` najbliższego ostrzeżenia. Reguła 13: LLM znajduje wyniki
      historyczne → DET porównuje ich `font_px` z największym na stronie.
- [ ] **BRAMA ZAKRESU (§6.6) — nie słownikowy filtr krypto.** Klasyfikacja dwuwymiarowa:
      opakowanie (CFD, ETN, ETF, certyfikat, fundusz, akcje, obligacje, opcje, kontrakty
      terminowe) × aktywo bazowe. `in_scope` wtedy, gdy rozpoznano opakowanie będące
      instrumentem finansowym wg art. 2 ustawy o obrocie — **bez względu na aktywo bazowe**.
      **CFD na bitcoina JEST w zakresie** (art. 2 ust. 1 pkt 2 lit. h) i dostaje znacznik
      `crypto_derivative` z podwyższonym priorytetem. Poza zakresem jest wyłącznie zakup
      spot bez opakowania (`reason: spot_crypto_mica`). Lista instrumentów z Załącznika 3
      idzie do promptu — regex tego nie rozstrzygnie.
- [ ] **ROUTER (§6.5):** tablica decyzyjna R1–R4 → `modules[]` + `primary_module`
      + `routing.reason` **po polsku, do pokazania w UI**. Pierwszeństwo R3 > R2 > R1.
- [ ] **Dedup:** simhash + cosine na embeddingach > 0.95 → grupowanie w kampanie.
- [ ] Każda reguła ma test na przykładzie z korpusu. Reguły DET są deterministyczne,
      więc testy są tanie i warto je mieć. Testy DET pisze A, testy LLM — B.

### C — api + web
- [ ] Widok szczegółów findingu: lista 18 reguł, verdict, **evidence (cytat lub pomiar)**,
      podstawa prawna, wycinek screenshota. To jest ekran, na którym jury spędzi najwięcej czasu.
- [ ] Wykresy trendów (Recharts): liczba incydentów w czasie, rozkład po modułach,
      najczęściej łamane reguły.
- [ ] Zmiana statusu findingu (`new` → `in_review` → `confirmed` / `dismissed`).
- [ ] WebSocket: broadcast przy `risk_level == "high"`, toast w UI.
- [ ] **Pasek routingu** na widoku findingu: które moduły objęły dokument + `routing.reason`
      po polsku. Nadzorca musi widzieć, dlaczego materiał trafił tam, gdzie trafił.
- [ ] **Zakładka „poza zakresem"** z kolumną podstawy prawnej — pokazuje odrzucone materiały
      z powodem (`spot_crypto_mica`, `not_financial_instrument`), nie kasuje ich.
- [ ] Znacznik `crypto_derivative` wyróżniony w tabeli — to materiały w zakresie
      i o podwyższonym priorytecie, nie wykluczone.

**GATE 2 — 19:00, 30 min, wszyscy razem**
Wszystkie 18 reguł zwraca `RuleResult` dla całego korpusu demo. Dashboard pokazuje
szczegóły z dowodami. Robimy **pierwszy przejazd próbny demo** — na głos, z zegarkiem.
Co się sypie, trafia na listę do naprawy.

---

## T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)

### A — scraper + warstwa podmiotowa Modułu 1
- [ ] **Rejestr KNF:** scrape 5 adresów z Załącznika 1/2 → `authorized_entities`.
      Normalizacja nazw (usuń „S.A.", „sp. z o.o.", małe litery, bez ogonków) pod fuzzy match.
      **Zapisz migawkę rejestru do `fixtures/registry-snapshot.json`** — jeśli KNF padnie
      albo zmieni layout w noc hackathonu, demo nadal działa.
- [ ] **Resolver podmiotów:** fuzzy match nazwy firmy z reklamy do rejestru
      (`rapidfuzz`, próg 0.85), wyznaczenie `relation_to_firm` (`official` / `third_party`
      / `unknown`) na podstawie domeny i handle'a.
- [ ] Detekcja ujawnienia współpracy (`#reklama`, `współpraca`, `materiał promocyjny`)
      i linku afiliacyjnego (`?ref=`, `?aff=`, `utm_campaign`).
- [ ] `YouTubeSource` przez yt-dlp: wideo → `ffmpeg -vn -ar 16000 -ac 1` → wav → SeaweedFS.
- [ ] Import z pendrive'a organizatora (`PendriveImportSource`).
- [ ] Scheduler (`rq-scheduler`): cykliczne odświeżanie źródeł — „mechanizm okresowej
      aktualizacji" wymagany przez Moduł 1.

### B — analyzer
- [ ] **faster-whisper, `language="pl"`, `device="cpu"`, `compute_type="int8"`** →
      `transcript` z segmentami czasowymi. **Na CPU świadomie** — zdejmuje STT z GPU
      i likwiduje konflikt o VRAM z Bielikiem (§9.1).
- [ ] Reguła 3 na osi czasu: pozycja ostrzeżenia względem twierdzenia o zyskach w sekundach.
- [ ] Tempo ostrzeżenia: `len(text) / (end - start)` vs. mediana dla reszty materiału.
- [ ] **Moduł 3:** słownik fraz doradczych + warunek podwójny (rekomendacja dotycząca
      instrumentu finansowego ORAZ brak podmiotu w rejestrze). Korzysta z resolvera A
      i z bramy zakresu, więc jest to głównie logika decyzyjna, nie nowy kod bazowy.
- [ ] **kNN druga opinia:** k=5 najbliższych sąsiadów ze zbioru złotego po cosine →
      `knn_score` obok scoringu regułowego (§6.7).
- [ ] Skrypt `evaluate.py`: precision / recall / F1 / macierz pomyłek dla danego thresholdu,
      liczony na `fixtures/gold/`.

### C — api + web
- [ ] **Panel kalibracji:** suwak thresholdu → przeliczanie flag **po stronie klienta**
      z `rule_results` już obecnych w odpowiedzi API. Zero requestów do modelu.
- [ ] Pod suwakiem: macierz pomyłek, precision, recall, F1 na zbiorze złotym.
- [ ] Wykres FP vs. FN w funkcji thresholdu + **druga krzywa: kNN** jako niezależna opinia.
      Miejsca, gdzie krzywe się rozchodzą, to najciekawszy materiał do przeglądu —
      i dobry, nieoczywisty moment w demo.
- [ ] Odtwarzacz wideo z transkryptem i zaznaczonym segmentem ostrzeżenia na osi czasu.
- [ ] Widok Moduł 1: firma ↔ reklamujący ↔ relacja ↔ link afiliacyjny.
- [ ] Widok kampanii: warianty zgrupowane przez dedup, z licznikiem („7 wariantów od 3 dni").
- [ ] **ZBIÓR ZŁOTY — oznaczanie ~35 materiałów prawdziwych** w `fixtures/gold/labels.json`.
      Etykiety dla korpusu demo (15–18 pozycji) są już w repo z konstrukcji, więc tu zostaje
      tylko reszta. Rób to w przerwach między zadaniami frontowymi, nie jednym blokiem.
      **Bez tego panel kalibracji nie ma czego pokazać** — to zadanie nie jest opcjonalne.
      Jeśli C nie wyrabia, o 21:00 dołącza A (rejestr powinien być już skończony).

**GATE 3 — 22:00, 30 min**
Trzy moduły produkują findingi. Suwak thresholdu zmienia metryki na żywo. Transkrypcja
wideo działa. **Drugi przejazd demo, mierzony stoperem — musi zmieścić się w czasie,
jaki daje jury.**

---

## T+10.5 — 22:00–01:30 · Dopięcie i polish (3,5 h)

- [ ] **A:** korpus demo do pełnych **15–18 plików**, każdy z opisem, którą regułę łamie.
      Scenariusz demo zapisany jako konkretna lista URL-i w kolejności pokazywania.
- [ ] **B:** iteracja promptów na zbiorze złotym. Cel: F1 > 0.75 przy domyślnym thresholdzie.
      Zapisz wyniki metryk — wchodzą do prezentacji jako liczby, nie jako obietnice.
- [ ] **C:** stabilność UI, stany loading/empty/error, responsywność dashboardu,
      **czysta konsola przeglądarki** (jury sprawdza to wprost).
- [ ] **Wszyscy:** `docker compose down -v && docker compose up` z czystego stanu.
      Musi wstać bez ręcznych kroków. Jeśli trzeba coś kliknąć — to bug.
- [ ] Test świeżego klona: `git clone` do nowego katalogu → `docker compose up` → działa.

**GATE 4 — 01:30 · FEATURE FREEZE**
Po tej godzinie **żadnych nowych funkcji**. Tylko naprawy błędów, dokumentacja i prezentacja.
To nie jest sugestia — każdy hackathon przegrywa się właśnie tutaj.

---

## T+14 — 01:30–02:00 · Commit, push, tag

- [ ] Wszystko scommitowane i wypushowane. `git tag mvp-freeze`.
- [ ] Krótka notatka w repo: co działa, co nie działa, co jest następne.

---

## T+14.5 — 02:00–06:00 · Rotacja snu (4 h)

Dwie osoby śpią, jedna czuwa. Zmiana po 2 h. Osoba czuwająca **tylko naprawia błędy
i pisze dokumentację** — nie dotyka architektury o 4 w nocy.

| Czas | Śpi | Czuwa | Zadanie czuwającego |
|---|---|---|---|
| 02:00–04:00 | A, B | C | README (Quick Start, wymagania sprzętowe, konfiguracja) |
| 04:00–06:00 | C, + jedna z A/B | pozostała | `docs/AI_PROCESS.md` + ADR-y |

**`docs/AI_PROCESS.md` to 20% oceny** („jak opisany jest ustandaryzowany proces tworzenia
oprogramowania przy pomocy asystentów AI"). Opisz to, co faktycznie zrobiliście:
`CLAUDE.md` jako kontrakt dla agenta, graf wiedzy graphify jako warstwa pobierania kontekstu,
skills jako powtarzalne procedury, design doc przed kodem, kontrakty zamrożone przed
pracą równoległą, gate'y integracyjne, TDD dla reguł deterministycznych, conventional commits,
ADR-y dla decyzji. Jedna strona konkretów bije pięć stron ogólników — i specyfikacja wprost
mówi „bez AI slop".

---

## T+18.5 — 06:00–08:00 · Dokumentacja i cybersec (2 h)

- [ ] `pip-audit` i `npm audit` → napraw co się da, **wynik wklej do README**.
- [ ] **`docs/LICENSES.md`** z `pip-licenses --format=markdown` i `npx license-checker --summary`.
      Sprawdź, czy nie wkradło się nic na AGPL / SSPL / gemma. To nasza historia wdrożeniowa
      dla UKNF i element weryfikowalnego łańcucha dostaw — tanie, a punktowane dwukrotnie.
- [ ] `requirements.txt` z przypiętymi wersjami, `package-lock.json` w repo.
- [ ] `.env` w `.gitignore`, w repo tylko `.env.example`. **Sprawdź `git log` — czy sekret
      nie wyciekł we wcześniejszym commicie.**
- [ ] Dockerfile: użytkownik nie-root, obrazy `-slim`.
- [ ] README ≤ 1 ekran: wymagania sprzętowe (RAM/VRAM pod Bielika), `docker compose up`,
      konfiguracja serwisów. Bez lania wody.
- [ ] `graphify update .` — graf wiedzy aktualny (zgodnie z `CLAUDE.md` projektu).
- [ ] Opis projektu z tytułem (wymóg formalny §4).

---

## T+20.5 — 08:00–09:30 · Prezentacja i film (1,5 h)

**Prezentacja PDF, maks. 11 slajdów, w tej kolejności:**
1. Problem — skala treści inwestycyjnych w polskim internecie, czego UKNF nie przejrzy ręcznie.
2. Co zbudowaliśmy — architektura, jeden diagram.
3. **Moduł 2 i mały druczek** — zrzut z liczbami: 7 px vs. 16 px, kontrast 1.9:1. To slajd,
   który zapamiętają.
4. Moduł 1 — finfluencer bez ujawnionego związku z firmą + link afiliacyjny.
5. Moduł 3 — doradztwo bez zezwolenia, z podstawą prawną (art. 76 ustawy o obrocie).
6. **Brama zakresu** — dwie reklamy krypto obok siebie: CFD na BTC **wchodzi** do analizy
   (art. 2 ust. 1 pkt 2 lit. h), zakup spot zostaje odrzucony jako reżim MiCA. Ten slajd
   pokazuje, że rozumiemy dziedzinę, a nie filtrujemy słowa kluczowe. Mocny punkt przy jurorach
   z UKNF, bo to dokładnie ten rodzaj rozróżnienia, który robią w pracy.
7. Speech-to-text — ostrzeżenie w sekundzie 33.8 z 34.2.
8. **Metryki** — precision / recall / F1 + krzywa thresholdu i druga krzywa kNN.
   Prawdziwe liczby ze zbioru złotego, nie obietnice.
9. Proces wytwarzania z asystentami AI (streszczenie `AI_PROCESS.md`).
10. Stack i licencje — wyłącznie open source **permisywny** (MIT / BSD / Apache-2.0),
    on-premise, zero płatnych API, polski model Bielik. Pokaż tabelę z `LICENSES.md`
    i powiedz wprost, że Valkey zamiast Redisa i SeaweedFS zamiast MinIO to decyzja
    pod wdrożenie w Urzędzie, nie przypadek.
11. Co dalej — droga do pilotażu w UKNF.

- [ ] Film ≤ 3 min (opcjonalny, ale podnosi ocenę): nagranie ekranu z narracją, ten sam
      scenariusz co demo live. **Nagrać z korpusu offline**, nie z internetu.

---

## T+22 — 09:30–10:15 · Próby demo

- [ ] **Trzy pełne przejazdy demo** z `docker compose down -v` przed każdym.
- [ ] Osoba prowadząca demo mówi na głos, pozostałe dwie słuchają i notują potknięcia.
- [ ] Naprawiamy **wyłącznie** to, co psuje demo. Nic innego.
- [ ] Plan B: jeśli cokolwiek padnie na żywo — gotowe zrzuty ekranu i film jako zapas.

---

## T+22.5 — 10:15–10:45 · ODDANIE

- [ ] Opis projektu z tytułem
- [ ] Prezentacja PDF
- [ ] README / opis kodu
- [ ] Link do repozytorium (sprawdź, czy publiczne albo czy organizator ma dostęp)
- [ ] Film (jeśli jest)
- [ ] **Potwierdzenie, że wysyłka przeszła.** Nie zakładaj — sprawdź.

**10:45–11:00 — bufor.** Nic nie robimy. Jeśli coś zostało na 10:55, było za późno.

---

## Drabinka cięcia zakresu

Gdy jesteśmy w tyle, ścinamy **od dołu**. Decyzję podejmuje cały zespół na gate'cie,
nigdy pojedyncza osoba w trakcie.

### Warstwa nietykalna — tego nie ścinamy nigdy

Każda pozycja jest tu z konkretnego powodu, nie z sympatii.

| Element | Dlaczego nietykalne |
|---|---|
| Moduł 2: reguły DET (4,5,6,7,8) + dashboard | Rdzeń i nasz jedyny realny wyróżnik |
| Panel kalibracji + metryki na zbiorze złotym | Jury testuje wpływ thresholdu **wprost** |
| `docker compose up` jednym poleceniem | Twardy wymóg specyfikacji §5 |
| **WebSocket alerty** | Specyfikacja wymienia je wprost („Implementacja WebSocketów"), a jury ma na liście testów „powiadomienia w czasie rzeczywistym". W FastAPI to ~20 linii — ścinanie czegoś, co jest tanie i punktowane, byłoby błędem. **Polling jako zamiennik został z drabinki usunięty.** |
| **Warstwa wektorowa (embeddingi + pgvector)** | Specyfikacja wymaga „reprezentacji wektorowej w postaci tokenów i embeddingów". Usunięcie = utrata punktów w kryterium zgodności (20%). W najgorszym razie redukujemy ją do samego dedupu, ale **nie usuwamy**. |
| Czystość konsoli przeglądarki | Jury sprawdza „Console.log" wprost |
| Licencje (brak AGPL/SSPL) | Wymóg mentorów pod wdrożenie w UKNF |

### Drabinka — ścinamy od dołu

| Priorytet | Element | Jak ścinać |
|---|---|---|
| 1 | Moduł 2: reguły LLM | Zredukuj do 2 promptów wsadowych (reguły 1, 2, 3, 15, 17, 18) |
| 2 | Moduł 1: rejestr KNF | Zamień scraping na `fixtures/registry-snapshot.json` (i tak go robimy jako zapas) |
| 3 | Moduł 3 (shadow advisory) | Zredukuj do słownika fraz + sprawdzenia rejestru, bez LLM |
| 4 | Speech-to-text | 2 wideo przetranskrybowane offline **przed** demo, bez pipeline'u na żywo |
| 5 | kNN jako druga opinia | Pomiń drugą krzywą, zostaw sam scoring regułowy |
| 6 | Widok kampanii (dedup w UI) | Zostaw dedup w backendzie, pomiń widok |
| 7 | Wykresy trendów | Zostaw jeden |
| 8 | Reguły DET na 3 viewportach | Zostaw `mobile` (najdotliwszy przypadek) — kosztem reguły 8 |
| 9 | SeaweedFS | Zamień na wolumen na dysku + nginx do serwowania plików |
| 10 | Fallback kontrastu przez próbkowanie pikseli | To i tak był stretch |
| 11 | Film 3 min | Pomiń, jest formalnie opcjonalny |

---

## Rejestr ryzyk

| Ryzyko | Prawdopodob. | Mitygacja | Kto pilnuje |
|---|---|---|---|
| Social media blokują scraping | **wysokie** | Korpus demo offline w compose; demo nie zależy od sieci | A |
| Bielik za wolny na naszym sprzęcie | średnie | Zacznij od 4.5B Q8_0; grupowanie reguł w jedno wywołanie; fallback na mniejszy quant | B |
| Pobranie modeli nie zdąży | średnie | **Uruchomione w minucie 0**, nie o 15:00 | B |
| Integracja sypie się o 19:00 | średnie | Kontrakty zamrożone o 12:30 + GATE 1 już o 15:00 | wszyscy |
| Zbiór złoty nie powstanie | średnie | Etykiety korpusu demo darmowe z konstrukcji (~18 szt.); ręcznie tylko ~35; właściciel C, wsparcie A od 21:00 | C → A |
| **Konflikt o VRAM zamraża inferencję na demo** | **wysokie** | `q:gpu` z jednym workerem; Whisper na CPU int8; Chromium headless `--disable-gpu`; profil `cpu` przetestowany przed demo | B |
| **Fałszywy `fail` na kontraście (tło `rgba(0,0,0,0)`)** | **wysokie** | Kompozycja alfa po przodkach; `background_confidence`; przy `unknown` → `not_applicable`, nigdy `fail` | A |
| **Klikanie akordeonów psuje DOM / nawiguje** | średnie | Zakaz klikania; detekcja statyczna z tablicy §6.2.1; `el.open = true` przez `evaluate` na świeżej stronie | A |
| **Licencja blokuje wdrożenie w UKNF** | średnie | Zero AGPL/SSPL/gemma; Valkey + SeaweedFS + bge-m3; `docs/LICENSES.md` w oddaniu | C |
| Rejestr KNF zmienia layout / strona nie odpowiada | średnie | `fixtures/registry-snapshot.json` zapisany od razu po pierwszym udanym scrapie | A |
| Threshold zacina demo | niskie | Przeliczanie po stronie klienta z `rule_results` w bazie | C |
| Sekret w commicie | niskie | `.env` w `.gitignore` od T-0; audyt `git log` o 06:00 | C |
| Ktoś nie śpi i psuje kod o 4:00 | średnie | Wymuszona rotacja; po 01:30 tylko bugfixy | wszyscy |
| Oddanie po 11:00 | niskie | Submit 10:15, bufor 45 min | prowadzący demo |

---

## Jedna rzecz na każdy gate

- **12:30** — kontrakty zamrożone, modele się pobierają, pendrive odebrany.
- **15:00** — jeden dokument przechodzi przez wszystkie 4 serwisy.
- **19:00** — 18 reguł zwraca dowody; pierwszy przejazd demo.
- **22:00** — 3 moduły + wideo + suwak thresholdu z metrykami.
- **01:30** — feature freeze. Koniec nowych funkcji.
- **06:00** — README, AI_PROCESS, audyty.
- **09:30** — 3 próby demo.
- **10:15** — oddane i potwierdzone.
