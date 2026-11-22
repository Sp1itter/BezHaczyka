# InvestWatch — sprint finałowy (3 strumienie pracy, zespół 6 osób, 22.11 01:00 → 10:15)

Stan na 22.11, 00:50. HEAD `6d9defd`. Źródła: wymagania z `DocsTaskINWESTWATCH/`, żywy test stosu
(`scheduler --once` + analiza na prawdziwych danych), audyt kodu, audyt UI ze zrzutami, research open source.
Wszystko poniżej jest **zmierzone albo wskazane w kodzie** — tam, gdzie nie, jest napisane „niezweryfikowane”.

Oddanie: **submit 10:15**, deadline 11:00. Feature freeze **08:30**. Od 08:30 tylko poprawki, demo, PDF.

---

## 1. Przegląd: co mamy, czego nie mamy

Legenda: ✅ jest i działa · 🟡 jest, ale słabe/częściowe · ❌ brak

### Silnik zbierania (scraper/crawler)

| Wymaganie | Stan | Fakt z testu / kodu |
|---|---|---|
| Kolejka zadań open source | ✅ | RQ na Valkey: `q:ingest`, `q:render`, `q:gpu` |
| Playwright / httpx | ✅ | Playwright (FB), httpx (WWW) — wszystko synchroniczne |
| Rotacja UA + proxy | 🟡 | `services/scraper/net.py`; lista proxy pusta, brak health-checku |
| HTML → JSON | ✅ | `AdDocument`, `meta_json.py` |
| SQL metadanych + object storage | ✅ | Postgres 16 + pgvector, SeaweedFS S3 |
| Harmonogram | ✅ | rq-scheduler + `schedule.yaml`, `--once` |
| **Facebook / Instagram (Meta Ad Library)** | 🟡 | **Prawdziwe reklamy** (13 z 14 nie z fixture'ów), ale **44% pobrań pada** (`SourceError: brak kreacji reklamy … zmiana DOM Meta?`), a nieudane trafiają na stałe do `facebook:seen` (`jobs.py:113`). 2 z 3 zapytań zwracają 0. Instagram tylko jako `publisher_platform` w reklamach Meta |
| **YouTube** | 🟡 | Prawdziwe filmy, ale **0 z 216 transkrypcji** (`IpBlocked`, `.env` ma `YT_MIN_INTERVAL_S=3`). 86% to szum (`skipped`) |
| **WWW** | ❌ | **Tylko fikcyjny korpus z nginx** (`http://nginx/www/index.html`). Zero prawdziwego internetu, a to źródło dla Modułu 3 |
| **TikTok** | ❌ | `sources/tiktok.py` = replay 2 syntetycznych plików, `enabled: false` |
| Reklamy płatne | 🟡 | Tylko Meta. Brak TikTok Ad Library, brak Google Ads Transparency (YouTube) |
| Szybkość | ❌ | ~2 nowe materiały/min, 0,6 analizy/min. Chromium uruchamiany **od nowa dla każdej reklamy**, 1 worker discover, limiter YT **śpi w workerze render** i blokuje FB |

### Moduły analityczne

| Wymaganie | Stan | Fakt |
|---|---|---|
| Preprocessing: HTML, normalizacja | ✅ | |
| Deduplikacja | 🟡 | tylko dokładny hash; simhash/embeddingi liczone, ale nieużywane |
| Embeddingi | ✅ | bge-m3, 1024 |
| Silnik inferencji + model open | ✅ | Ollama + Bielik 4.5B v3 Q8, `temperature 0`, `seed 42` |
| Ollama w Dockerze | ❌ | profil `ollama` = obraz 0.5.4, **bez GPU, bez auto-pull, bez healthchecka** |
| Scoring → kategoria | 🟡 | `risk_level` niezgodny ze `score` (high przy 18,5, low przy 20,8) |
| **Moduł 1** (raport podmioty trzecie) | 🟡 | raport działa (199 wierszy), ale 151 to szum YouTube; rejestr KNF w bazie: 1088 podmiotów |
| **Moduł 2** (18 reguł) | 🟡 | Na żywych danych **~1 z 6 reklam ma sensowny zestaw werdyktów** (szczegóły w §3) |
| **Moduł 3** (shadow advisory) | ❌ | `module3.assess_shadow_advisory` **nigdy nie jest wołany** (tylko w testach). Router taguje M3 regexem `rekomend\w*` bez negacji → **15 z 15 sprawdzonych to fałszywe alarmy** („nie stanowi rekomendacji”) |
| Agregator M1+M2+M3 | 🟡 | `Finding` łączy moduły, ale M3 nie ma wyniku |
| Autoskalowanie analizy | ❌ | `scaling.py`/`pool.py` istnieją, ale: `executor: dry-run`, zła nazwa kolejek (`gpu` zamiast `q:gpu`), provider stanu niepodpięty, brak pętli, executor `compose` niezaimplementowany |

### Dashboard

| Wymaganie | Stan | Fakt |
|---|---|---|
| Filtry data/źródło/ryzyko/moduł | 🟡 | `services/web` (:7090) **nie ma filtra dat**; `services/dashboard` (:7080) ma, ale filtruje 500 wierszy po stronie klienta; API nie ma `from/to` |
| Wykres trendu | 🟡 | tylko w `dashboard`, liczony w przeglądarce |
| Zmiana statusu | ✅ | `PATCH /findings/{id}`, historia `events` |
| WebSocket alerty | ✅ | `/ws/alerts` (polling bazy co 3 s); toasty w `web` nigdy nie znikają |
| Panel kalibracji | 🟡 | działa, ale zbiór złoty = **8 pozycji**, przy progu 50: TP 0 |
| Wygląd | ❌ | dwa różne frontendy, kafelki z zerami, 19 kart reguł z „nie oceniono”, żargon (`scope_gate`, `RenderProbe`), ikony z Unicode |
| `console.log` | ✅ | 0 w obu `src/` |

### Formalne

| Element | Stan |
|---|---|
| Opis + tytuł | 🟡 README |
| **Prezentacja PDF** | ❌ |
| README (Quick Start, sprzęt, konfiguracja) | ✅ (do odchudzenia, wskazuje stary UI) |
| **`docs/AI_PROCESS.md`** (kryterium 20%: proces z asystentami AI) | ❌ |
| **`docs/LICENSES.md`** | ❌ |
| Skan zależności | 🟡 pip-audit dla 3 serwisów; **brak `npm audit`**, brak `services/api` |
| Limity CPU/RAM w compose | ❌ |
| Film ≤ 3 min | ❌ (opcjonalny) |

---

## 2. Czy scrapery naprawdę zbierają prawdziwe dane — werdykt

| Źródło | Werdykt | Liczby (21.11) |
|---|---|---|
| Facebook Ad Library | **Tak, ale kulawo** | 14 reklam (zrzut z S3 = prawdziwa strona „XTB Online Investing”), 11 z 25 pobrań padło |
| YouTube | **Tak, ale bez treści mówionej** | 216 filmów, tytuły zgodne z oEmbed, **0 transkrypcji** |
| WWW | **Nie** | 3 fikcyjne strony z lokalnego nginx |
| TikTok | **Nie** | nie istnieje |

Świeży przebieg `scheduler --once`: 5,1 min, 30 pobrań, 0 błędów, ale **0 nowych reklam FB**
(wszystkie już w `seen`), 10 nowych filmów YT, z czego 3 zakwalifikowane.

---

## 3. Bielik: co zwraca na prawdziwych danych

Czas: mediana **18 s** na dokument. Batch 1 ≈ 6 s, batch 2 ≈ 5 s, batche 3–4 zwykle pomijane
warunkiem wstępnym. **Resztę zjada podsumowanie LLM**: 47 odrzuceń przez strażnika, potem i tak szablon.

Typowe bzdury (z prawdziwych findingów):
- „**76% rachunków traci pieniądze**” (czyli samo ostrzeżenie) uznane za obietnicę zysku → reguła 3 FAIL → HIGH.
- „zniżki do 90%” (kupony Revolut) i „przegrał 99% spraw” (kancelaria frankowa) jako zysk → HIGH.
- Reguła 1 FAIL „brak nazwy firmy”, choć mBank jest wymieniony z nazwy.
- Reguła 2 FAIL w reklamie FB, choć Meta oznacza ją jako „Sponsorowane”.
- Reguła 9 PASS, bo za ostrzeżenie uznano „✅ chcesz zacząć inwestować”.
- Reklama Virtune ETP (produkt w XTB) poszła tylko do M1 i **dostała 0 reguł**, więc score 0.
- Ostrzeżenie XTB przed oszustami (nie jest reklamą) analizowane jak reklama.
- Poza zakresem, a ocenione jako HIGH: kancelarie frankowe, karty walutowe, kupony.

Przyczyny (kod, nie model):
1. `router.py:77` — regex `\d+%` traktuje każdą liczbę z procentem jako zysk.
2. `router.py:32,50` — `rekomend\w*` bez maskowania negacji („nie stanowi rekomendacji”).
3. Brama zakresu zwraca `uncertain` dla każdego YouTube i **nie blokuje** analizy.
4. `pipeline.py:179` — reguły tylko gdy `2 in modules`; R2 bez słowa o zysku = 0 reguł.
5. Reguła 3 mierzy dystans znaków (próg 300) w opisach YT liczących 700–3000 znaków.
6. Eskalacja severity 5 w `scoring.risk_level` robi HIGH z jednego fałszywego FAIL-a.
7. Brak `num_ctx`: długie transkrypcje ucinają początek promptu, czyli instrukcje.

---

## 4. Które z 18 reguł co sprawdzają i jak

DET = deterministycznie z geometrii renderu (Playwright, `RenderProbe`) · LLM = Bielik, wsad N ·
HYB = kod + LLM (strażnicy w `rules_llm/guards.py`).
„Na żywo” = czy reguła daje werdykt na danych z 21.11 (32 findingi).

| # | Reguła | Co sprawdza | Jak / gdzie | Wejście | Na żywo |
|---|---|---|---|---|---|
| 1 | Identyfikacja firmy | oficjalna nazwa firmy w materiale | LLM wsad 1 (`batch_1.py`) + weryfikacja cytatu | tekst+transkrypcja | działa, FN/FP (mBank) |
| 2 | Oznaczenie reklamy | czy jednoznacznie oznaczona jako reklama | HYB: wsad 1 + `_guard_rule_2` | tekst | działa, **najwięcej FP** (ignoruje „Sponsorowane”) |
| 3 | Informacja o ryzyku | twierdzenia o zysku i czy obok jest ostrzeżenie | HYB `rules_hybrid.assess_rule_3`: geometria 600 px / 300 znaków / 5 s w wideo | RenderProbe, tekst, segmenty | **22 FAIL, prawie wszystkie fałszywe** |
| 4 | Rozmiar czcionki ryzyka | font ostrzeżenia vs przeważający | DET `scraper/rules_det/rules.py:71`, fallback w analyzerze | RenderProbe | **nigdy** (FB: wymuszone N/A) |
| 5 | Ekspozycja i kontrast | kontrast, przesłonięcie | DET `rules.py:98` | RenderProbe (kolory) | **nigdy** (FB: N/A) |
| 6 | Ukrywanie ryzyka | przypisy, „Legal”, niska widoczność | DET `rules.py:123` | RenderProbe | tylko FB, rzadko |
| 7 | Dostępność za 1 kliknięciem | czy trzeba rozwinąć/kliknąć | DET `rules.py:152` | RenderProbe | tylko FB, rzadko |
| 8 | Responsywność | 3 viewporty, ucięcie, skalowanie | DET `rules.py:174` | RenderProbe ×3 | **nigdy** (FB: N/A) |
| 9 | Zrozumiałość | język zrozumiały dla odbiorcy | LLM wsad 2 | tekst | działa, halucynuje dowody |
| 10 | Spójność językowa | ostrzeżenie w tym samym języku | HYB: detekcja języka nadpisuje LLM (`lang_consistency.py`) | tekst | działa |
| 11 | Porównania produktów | porównania, źródło, założenia | LLM wsad 2 | tekst | **zawsze N/A** |
| 12a | Wyniki historyczne: okres | 5 lat, pełne 12 mies., źródło | HYB: warunek wstępny + wsad 3 + strażnik | tekst | działa, halucynuje wyzwalacze |
| 12b | Wyniki historyczne: waluta/opłaty | ostrzeżenie kursowe i o opłatach | HYB: wsad 3 + strażnik | tekst | rzadko |
| 13 | Dominacja wyników historycznych | czy wyniki nie są najbardziej eksponowane | HYB `assess_rule_13`: `font_px`/`bbox` | RenderProbe + tekst | **nigdy** |
| 14 | Ostrzeżenie przy wynikach historycznych | „nie są wiarygodnym wskaźnikiem” | HYB: wsad 3 + strażnik | tekst | działa, halucynuje |
| 15 | Prognozy | prognoza + ostrzeżenie | LLM wsad 4 | tekst | najsłabsza (67%) |
| 16 | Informacja podatkowa | zależność od sytuacji klienta | HYB: wsad 4 + strażnik | tekst | rzadko |
| 17 | Sugerowanie aprobaty KNF | odwołanie do KNF jako zatwierdzenie | HYB: wsad 1 + strażnik nadzoru | tekst | zawsze PASS (z kodu) |
| 18 | Nadzór jako argument bezpieczeństwa | „bezpieczne, bo nadzór KNF” | HYB: wsad 1 + strażnik nadzoru | tekst | zawsze PASS (z kodu) |
| M3 | Shadow advisory | doradztwo bez zezwolenia | `module3.assess_shadow_advisory` (LLM + rejestr KNF) | tekst + autoryzacja | **niepodpięte** |

Wniosek: reguły DET (4–8, 13) są napisane, ale żadne źródło poza FB nie robi renderu, a na FB są wyłączone.
Najtańsza naprawa: **zrzut + RenderProbe dla stron WWW i landingów z reklam** (Playwright już jest).

---

## 5. Decyzje (moje propozycje — popraw, jeśli nie pasują)

1. **Jeden frontend: `services/web`** (README na niego wskazuje). Z `services/dashboard` przenosimy
   kod (filtr dat, trend, przegląd, historia), potem `dashboard` i `dashboard-mock` idą pod profil `legacy`.
2. **UI: Mantine 7 + mantine-react-table (TanStack) + Recharts**, jasny motyw instytucjonalny.
   Bez Tailwinda, bez shadcn (za długi setup).
3. **Ollama w Dockerze z GPU domyślnie**, Ollama na hoście jako fallback (`OLLAMA_BASE_URL`).
4. **Skalowanie analizy = równoległość Ollamy, nie liczba kontenerów.** Jeden GPU 8 GB = jedna Ollama.
   Kontenery analyzera skalujemy do `OLLAMA_NUM_PARALLEL` (np. 4). Autoskaler ogranicza się do maksimum
   ustawionego w panelu operatora i do tego limitu.
5. **Prawdziwy internet dla WWW**: odkrywanie przez `ddgs` (bez płatnego API), pobieranie przez
   `curl_cffi` + `trafilatura`. Korpus nginx zostaje tylko jako tryb offline.
6. **TikTok**: reklamy z publicznego `library.tiktok.com/api/v1/search?region=PL` (DSA),
   organiczne przez `yt-dlp` (`tiktok:user` dla listy finfluencerów). TikTokApi tylko jeśli starczy czasu.
7. **Nie dotykamy krypto spot** (z `ToDo.txt`); CFD/ETP na krypto zostaje w zakresie.

---

## 6. Podział na 3 strumienie pracy — zasady merge'a

**Każda osoba ma swoje katalogi. Nikt nie edytuje cudzych.** Jedyne współdzielone pliki mają właściciela:

| Plik | Właściciel | Inni |
|---|---|---|
| `services/scraper/**` | **A** | — |
| `services/analyzer/**`, `infra/docker-compose.yml`, `infra/.env.example` | **B** | A i C zgłaszają B zmiany w compose/env (Discord), B wkleja |
| `services/web/**`, `services/api/**`, `services/dashboard/**` | **C** | — |
| `services/casedb/casedb/migrations/**` | kto potrzebuje, **numer rezerwujesz na czacie** (A: 017–019, B: 020–022, C: 023–025) | |
| `README.md`, `docs/*.md` | każdy swoją sekcję; README scala C na końcu | |

Gałęzie: `feat/a-scraper-speed`, `feat/b-analyzer-ollama`, `feat/c-ui`. PR do `main` co etap
(nie na końcu!). Po merge'u inni robią `git pull` i przebudowują wg tabeli w `CLAUDE.md`.

### Kontrakt B ↔ C (panel operatora) — ustalony z góry, żeby nie czekać

Autoskaler (B) wystawia HTTP w sieci compose, `http://autoscaler:8090`. API (C) proxuje pod `/ops/*`:

```
GET  /scaling   -> {
  "executor": "compose",
  "ollama_parallel": 4,
  "queues": [
    {"name":"q:gpu","backlog":12,"running":2,"min":1,"max":4,
     "cpus":2.0,"memory_mb":3072,"scale_up_backlog":3}
  ],
  "workers": [{"id":"analyzer-2","queue":"q:gpu","state":"busy","job":"…","since":"ISO"}],
  "throughput_per_min": 7.5
}
PUT  /scaling   body: {"queues":[{"name":"q:gpu","max":4,"cpus":2.0,"memory_mb":3072}]}
                -> 200 nowy stan | 422 {"detail":"max > OLLAMA_NUM_PARALLEL (4)"}
```

Do czasu gotowości B, C używa atrapy zwracającej ten JSON.

### Kontrakt A ↔ B (bez zmian)

`AdDocument` + `det_results` w payloadzie `q:gpu` zostają. A dodaje tylko wartości `source`:
`tiktok`, `tiktok_ads`, `www_live` (migracja 017) oraz wypełnia `render_probe` dla WWW.

---

## 7. Osoba A — silnik zbierania (szybkość + TikTok + reklamy + prawdziwe WWW)

Cel mierzalny na 08:30: **≥ 20 nowych materiałów/min** w `scheduler --once`, 4 źródła live
(FB, YT, WWW, TikTok), ≥ 1 źródło płatnych reklam poza Meta, transkrypcje dla ≥ 50% wideo.

**A1 (01:00–02:30) — szybkość, szybkie wygrane**
- Jedna przeglądarka na proces workera, nowy `context` na reklamę (`sources/facebook.py:543-555`).
  Blokuj `media`/`font` poza krokiem RenderProbe.
- Osobne kolejki per źródło: `q:render:fb`, `q:render:yt`, `q:fetch:www`. Limiter YT robi
  `enqueue_in` zamiast `sleep` w workerze (`jobs.py:82`).
- `SCRAPER_INGEST_WORKERS=3`. Zapytania discover równolegle.
- `seen.add()` dopiero po udanym pobraniu (`jobs.py:113`). Wyczyść `facebook:seen` z 11 nieudanych.
- `job_timeout=600` + `Retry(max=2)` dla zadań analizy (`jobs.py:180`).
- Rejestr KNF ładowany raz na proces, nie na zadanie (`jobs.py:142`).
- `YT_MIN_INTERVAL_S=8` w `.env.example` (zgłoś B).

**A2 (02:30–04:30) — prawdziwe WWW (potrzebne dla Modułu 3)**
- Nowe `sources/www_live.py`: odkrywanie `ddgs` (region `pl-pl`) z listy fraz
  („doradztwo inwestycyjne”, „family office”, „zarządzanie majątkiem”, „sygnały giełdowe”,
  „portfel modelowy”, „konsultacje inwestycyjne”, „wealth management Polska”).
- Pobieranie `curl_cffi` `AsyncSession(impersonate="chrome")` z semaforem globalnym (~30)
  i per domena (2), `trafilatura` dla treści głównej, cache robots.txt w Valkey.
- Dla kandydatów (słowa kluczowe finansowe) zrzut + `RenderProbe` Playwrightem →
  **odblokowuje reguły DET 4–8 i 13 poza FB**.
- Filtr wstępny: odrzuć domeny z rejestru KNF (to M2, nie M3) i oczywisty szum.

**A3 (04:30–06:30) — TikTok + reklamy**
- `sources/tiktok_ads.py`: Playwright otwiera `library.tiktok.com` raz (cookies), potem httpx
  `POST /api/v1/search?region=PL&type=1` (page=12; HTTP 200 z „limit exceed” = rate limit).
  Kreacje pobieraj od razu (URL wygasa po ~24 h) do S3. **Najpierw 15 min w DevTools** na sprawdzenie payloadu.
- `sources/tiktok.py` live: `yt-dlp -j` dla listy kont finfluencerów (`config/tiktok_accounts.yaml`),
  napisy `--write-subs --sub-langs "pl.*"`, inaczej audio do Whispera (B).
- Meta: fallback dla 44% „brak kreacji”. Brać tekst i media z JSON-a `/api/graphql/`
  przechwyconego w wynikach wyszukiwania (`page.on("response")`), bez wchodzenia w `?id=`.
- YouTube: napisy przez `yt-dlp --write-auto-subs` zamiast blokowanego API transkrypcji.
  Fallback: audio m4a w S3, oznaczone do Whispera.

**A4 (06:30–08:30) — stabilizacja**
- Opcjonalnie (10 min próby): `Google-Ads-Transparency-Scraper` dla region=PL. Nie działa = porzuć.
- Test: `scheduler --once` na czystym `-p iwverify`, pomiar materiałów/min per źródło → wpisz do README.
- `pip-audit` scrapera → `docs/SECURITY-AUDIT.md`.

---

## 8. Osoba B — Bielik, analiza, Ollama w Dockerze, autoskaler, Moduł 3

Cel mierzalny na 08:30: **≤ 6 s na dokument** średnio przy 4 równoległych, **0 fałszywych HIGH**
w 20 ręcznie sprawdzonych żywych findingach, Moduł 3 z sensownymi wynikami na WWW od A.

**B1 (01:00–02:00) — Ollama w Dockerze**
- `infra/docker-compose.yml`: serwis `ollama` domyślny (bez profilu), obraz przypięty do aktualnej
  wersji (sprawdź `docker pull`, musi ładować Bielik v3), GPU:
  `deploy.resources.reservations.devices: [{driver: nvidia, count: all, capabilities: [gpu]}]`.
  Env: `OLLAMA_NUM_PARALLEL=4`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`,
  `OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_CONTEXT_LENGTH=4096`, `OLLAMA_MAX_LOADED_MODELS=2`.
  Healthcheck `ollama list`.
- Serwis jednorazowy `ollama-pull` (Bielik 4.5B Q8, bge-m3, Bielik 1.5B Q8), analyzer czeka na
  `service_completed_successfully`. `OLLAMA_BASE_URL=http://ollama:11434` domyślnie.
- Profil `ollama-cpu` dla kolegów bez NVIDIA. Ollama natywna = nadpisanie w `.env`.
- Limity `cpus`/`mem_limit` dla wszystkich serwisów, `shm_size: 1g` dla workerów Playwright.
- ⚠️ Na tym laptopie natywna Ollama zajmuje port 11434 i VRAM — zatrzymaj ją przed testem.

**B2 (02:00–03:30) — szybkość Bielika**
- `llm.py`: jeden współdzielony `httpx.Client`, `options.num_ctx=4096`, `num_predict≈300`,
  `format=<schemat JSON pydantic>`, `keep_alive`. Przycinanie materiału do ~2,5k tokenów.
- 4 wsady **równolegle** (`ThreadPoolExecutor` w `pipeline.analyze` / `registry.module2_runners`).
- Podsumowanie: `SUMMARY_LLM=0` na demo (szablon) albo 1 próba bez ponowień. Dziś daje +5–10 s.
- Filtr wstępny zakresu: regex finansowy → Bielik 1.5B „czy to reklama instrumentu finansowego? tak/nie”
  → dopiero 4.5B. Wycina kupony, kancelarie frankowe, karty — **jednocześnie szybciej i mniej FP**.
- Pomiar: 20 dokumentów sekwencyjnie vs równolegle → liczby do README i PDF.

**B3 (03:30–05:30) — jakość (naprawy z §3)**
- `router.py:77`: zysk ≠ dowolny `%`. Wyklucz kontekst straty („traci”, „strat”), rabatu
  („zniżk”, „rabat”, „taniej”), spraw sądowych. Wymagaj słowa zysku/zwrotu/stopy w oknie.
- `router.py:32,50`: maskowanie negacji („nie stanowi/nie jest/nie są … rekomendac/porad”).
- `pipeline.py:179`: moduł 2 dla **każdego** materiału in-scope (nie tylko R1/R2 z zyskiem).
- **Podpiąć Moduł 3**: `3 in decision.modules` → `module3.assess_shadow_advisory` → `RuleResult`
  `M3` w `Finding` + wpływ na score.
- Reguła 2: oznaczenie platformy („Sponsorowane”, „Reklama”, `is_paid_ad`) = PASS w kodzie.
- Reguła 3 dla długich opisów YT: dystans względny / sekcja, nie 300 znaków.
- Spójność `risk_level` ↔ `score`: severity 5 FAIL podnosi score do min. 70 (albo dolna granica
  przedziału HIGH), żeby lista sortowała się sensownie.
- Ponowna analiza po `tools/reresolve.py` (12 nieaktualnych routingów).

**B4 (05:30–07:30) — autoskaler (zgodny z kontraktem B↔C)**
- Napraw `scaling.py`: nazwy `q:*`, podpięty `make_valkey_state_provider`, prawdziwe `idle_s`,
  limit `gpu.max ≤ OLLAMA_NUM_PARALLEL` (nie liczba endpointów).
- Nowy serwis `autoscaler` (`services/analyzer`, osobny entrypoint): pętla co 10 s →
  `decide()` → executor `compose` przez Docker SDK za **`tecnativa/docker-socket-proxy`**
  (tylko `CONTAINERS`, `POST`). Skalowanie `analyzer` z `cpus`/`mem_limit` z konfiguracji.
  Konfiguracja operatora w Valkey (`ops:scaling`), walidacja `validate_scaling_config`.
- HTTP `GET/PUT /scaling` (kontrakt §6). Histereza: w dół po 60 s pustej kolejki.
- Demo: wrzuć 40 zadań → widać 1 → 4 kontenery w panelu → przepustowość rośnie.

**B5 (07:30–08:30) — zbiór złoty + dokument**
- Razem z C: oznaczyć ≥ 30 żywych findingów w UI (TP/FP). `GET /calibration` liczony ze złotego
  zbioru **plus** ocen analityka. Uruchomić `tools/eval_rules.py`, nowe liczby do PDF.
- `docs/AI_PROCESS.md`: jak pracowaliśmy z Claude Code (superpowers: brainstorming → spec → plan →
  TDD → review, worktree na osobę, graphify, zbiory holdout zamrożone przed strojeniem). To 20% oceny.

---

## 9. Osoba C — Moduł 3 aplikacji (UI) + API dla UI — w pełni

Cel: **jeden prosty, profesjonalny panel nadzorcy**, który spełnia każdy punkt wymagań dashboardu
i przechodzi demo bez jednej pustej sekcji. Zasada: **mniej, gęściej, po polsku.**

**Kierunek wizualny**
- Jasny motyw, tło `#F5F6F8`, powierzchnie `#FFFFFF`, tekst `#1A1F2B`, drugorzędny `#5B6472`,
  ramki `#DDE1E6`, akcent granat `#0B3D91`. Ryzyko: wysokie `#B42318`, średnie `#B54708`,
  niskie `#475467` (szare, bo „niskie” ≠ „dobre"). Kolor zawsze z etykietą tekstową.
- Inter/system-ui, 13 px w tabelach, 14 px tekst, nagłówki ≤ 20 px. Promień 4 px, ramki 1 px, bez cieni
  (poza szufladą), wiersze 32 px, cyfry tabelaryczne.
- **Usuń:** kafelki KPI z zerami, 5 wykresów słupkowych, ikony z Unicode, osobny suwak „pewności LLM”
  na liście, karty „nie oceniono”, żargon (`scope_gate`, `RenderProbe`, `R3`, `DET/LLM/HYBRID`
  → „pomiar z renderu” / „ocena modelu”). Emoji z tytułów scrapowanych wyciszone.

**Strony (5)**

```
[InvestWatch · UKNF]  Wyniki  Alerty (3)  Kalibracja  Raporty  Operator        ● na żywo
```

1. **Wyniki** (start): zakres dat, źródło, ryzyko, moduł, status, szukaj, CSV.
   Trend (pas 120 px: incydenty/dzień wg ryzyka). Gęsta tabela z paginacją po stronie serwera.
   Szuflada (sticky 480 px): podsumowanie (`summary`), **naruszenia na górze** z cytatem i podstawą prawną,
   „nie oceniono (12)” zwinięte, podmiot vs rejestr KNF, zrzut reklamy z S3, decyzja analityka
   (etykieta + notatka + status + przypisanie), historia.
2. **Alerty**: strumień WebSocket jako tabela (czas, score, tytuł, naruszone reguły), „przejmij”/„otwórz”.
   Powiadomienia Mantine znikają po 8 s, licznik nieprzeczytanych w nawigacji.
3. **Kalibracja**: suwak progu (domyślnie najlepsze F1), macierz 2×2, wykres FP/FN vs próg ze
   znacznikiem, precyzja/pełność/F1, ostrzeżenie o małej próbie, tabela zbioru złotego.
   „Zapisz jako próg alertów” (`PUT /settings/threshold`, alerty WS respektują go po stronie serwera).
4. **Raporty**: zakładki Moduł 1 (podmioty trzecie: firma, reklamujący, treść, URL, platformy, ostatnio
   widziane) i **Moduł 3** (podmiot, treść oferty, URL, status w rejestrze KNF). CSV.
5. **Operator**: tabela kolejek (backlog, działające, min, **max**, CPU, RAM, próg skalowania),
   lista workerów, przepustowość/min, „Zastosuj” z błędami 422 w linii. Kontrakt w §6.

**C1 (01:00–02:30)** Mantine + mantine-react-table + router (hash), tokeny, szkielet i nawigacja,
usunięcie starego CSS. API: `from`/`to`/`reviewed` w `/findings` i `/stats`, `GET /stats/trend?bucket=day`,
`GET /documents/{id}/screenshot` (presigned S3 albo proxy).

**C2 (02:30–05:00)** Strona Wyniki kompletna (najważniejsza dla jury), przeniesienie z `services/dashboard`
etykiet przeglądu, przypisania i historii.

**C3 (05:00–06:30)** Alerty + Kalibracja (`PUT /settings/threshold`, ostrzeżenie „próbka 8” znika po B5).

**C4 (06:30–07:30)** Raporty M1/M3 (`GET /reports/module3` w API z findingów z `M3`), Operator na atrapie →
przepięcie na `autoscaler` od B.

**C5 (07:30–08:30)** `dashboard` + `dashboard-mock` pod profil `legacy` (zgłoś B do compose),
`npm audit` (Vite 5.4.11 ma znane zgłoszenia — podbij), `docs/LICENSES.md` (licencje npm + pip
z `pip-licenses` / `license-checker`), README: jeden adres UI, odchudzenie. Zrzuty ekranu do PDF.

Jeśli zabraknie czasu: Operator tylko do odczytu, potem Raport M3 jako filtr na Wynikach.

---

## 10. Wspólny finał (08:30–10:15)

| Godz. | Kto | Co |
|---|---|---|
| 08:30 | wszyscy | **feature freeze**, ostatnie PR-y do `main` |
| 08:30–09:00 | B | czysty start `docker compose -p iwverify up -d --build` na pustym wolumenie (porty przesunięte), lista błędów |
| 09:00–09:30 | A, C | poprawki z czystego startu; scenariusz demo na żywo (scrape → alert w UI ≤ 2 min) |
| 08:30–09:45 | C (+A) | PDF: problem → architektura (diagram) → 4 źródła live → 18 reguł (tabela §4) → liczby (trafność, szybkość, skalowanie) → zrzuty UI → bezpieczeństwo → proces AI |
| 09:45–10:15 | wszyscy | próba demo 3 min, nagranie filmu (opcjonalnie), **submit 10:15** |

Scenariusz demo (3 min): uruchomienie jedną komendą → `scheduler --once` → panel operatora pokazuje
backlog i dokłada kontenery analyzera → alert WebSocket o reklamie HIGH → szuflada z naruszeniem
art. 44 i cytatem → zmiana statusu → suwak kalibracji zmienia FP/FN → raport M1 i M3 do CSV.

---

## 11. Ryzyka, które mogą położyć demo

1. Ollama w kontenerze nie widzi GPU (Docker Desktop/WSL2) → fallback: natywna Ollama + `OLLAMA_BASE_URL`, te same parametry przez zmienne środowiskowe Windows.
2. Meta/TikTok zablokują w trakcie demo → nagraj przebieg wcześniej; tryb `auto` przełącza na replay i **UI musi pokazywać „replay”** (uczciwie).
3. 8 GB VRAM: Bielik 4.5B Q8 (5 GB) + 1.5B (1,7 GB) + KV ×4 może się nie zmieścić → zmniejsz `NUM_PARALLEL` do 2 albo zrezygnuj z 1.5B na GPU.
4. Merge w ostatniej godzinie → PR co etap, nie na końcu.
5. `down -v` kasuje bazę zespołu → tylko na projekcie `-p iwverify`.
