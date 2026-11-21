# InvestWatch — dokument projektowy (design doc)

**Data:** 2026-11-21 · **Zespół:** 3 osoby · **Deadline oddania:** 2026-11-22, 11:00
**Zadanie:** HackNation 2026, wyzwanie UKNF „#InvestWatch — na straży inwestorów!"

---

## 1. Intencja i uzasadnienie

UKNF nie jest w stanie ręcznie przeglądać treści promocyjnych dotyczących instrumentów
finansowych publikowanych w polskim internecie i social mediach. Budujemy prototyp (MVP),
który automatycznie zbiera takie materiały i odpowiada na trzy pytania nadzorcze:

1. **Czy reklama jest rzetelna i nie manipuluje?** (ryzyko vs. zysk, mały druczek, prognozy)
2. **Czy reklama pochodzi z legitnego źródła?** (czy reklamujący jest powiązany z firmą inwestycyjną)
3. **Czy ktoś świadczy doradztwo inwestycyjne bez zezwolenia?** (shadow advisory)

Punkty 1–3 to wprost zagadnienia wyróżnione przez mentorów UKNF, uzupełnione o
speech-to-text z reklam wideo oraz świadome wyłączenie kryptoaktywów z zakresu.

**Dlaczego teraz:** 23 godziny na MVP, nagroda 30 000 zł, a najlepsze rozwiązania mają
szansę na pilotaż produkcyjny w strukturach UKNF.

---

## 2. Cele, nie-cele, anty-cele

### Cele (musi być)
- Działający silnik zbierania danych z pluginowalnymi źródłami (web + social + wideo).
- Trzy moduły analityczne produkujące wspólny typ wyniku (`Finding`).
- 18 reguł oceny informacji o ryzyku z **dowodem** (evidence) dla każdej decyzji.
- Dashboard: filtrowanie, wykresy trendów, zmiana statusu, alerty realtime, panel kalibracji.
- `docker compose up` stawia cały stos jedną komendą, offline, bez płatnych API.
- Transkrypcja reklam wideo (polski) i przepuszczenie jej przez ten sam silnik reguł.

### Nie-cele (świadomie pomijamy)
- Kryptoaktywa — zakres to instrumenty finansowe wg ustawy o obrocie. Krypto trafia do
  jawnego koszyka „wykluczone z zakresu", widocznego w UI (dowód, że przeczytaliśmy zakres).
- Produkcyjne obejście antybotów Facebooka/Instagrama/TikToka na skalę.
- Uwierzytelnione sesje social media, logowanie, scraping treści prywatnych.
- Automatyczne wysyłanie zawiadomień/pism nadzorczych. System tylko flaguje i uzasadnia.
- Fine-tuning własnego modelu. Używamy gotowych open-source'owych.

### Anty-cele (to by oznaczało porażkę, nawet gdyby „działało")
- Demo zależne od wifi na sali albo od tego, czy TikTok dziś nie zbanuje IP.
- Czarna skrzynka: „ryzyko 87%" bez wskazania, która reguła i dlaczego.
- Threshold, który przy przesuwaniu suwaka wymaga ponownej inferencji (zacina demo).
- Monorepo-moloch zamiast rozdzielonych serwisów (specyfikacja wprost tego zakazuje).
- Śmieci w konsoli przeglądarki — jury sprawdza to **wprost** („Console.log").

---

## 3. Ograniczenia narzucone z zewnątrz

| Ograniczenie | Źródło | Konsekwencja dla designu |
|---|---|---|
| Oddanie do 22.11 godz. 11:00, po terminie nie ocenia się | Regulamin §4 | Feature freeze o 01:30, submit 10:15 |
| Zespół max 6 osób | Regulamin §4 | Mamy 3 → 3 strumienie równoległe |
| Wyłącznie open source, on-premise, **zero płatnych API** | Opis, §5 | Ollama + Bielik, faster-whisper, Postgres+pgvector, SeaweedFS, Valkey — patrz §3.1 |
| Docker + Docker Compose, start jedną komendą | Opis, §5 | `infra/docker-compose.yml` jest artefaktem pierwszej klasy |
| Modułowa architektura lekkich serwisów, separacja FE/BE/AI | Opis, §5 | 4 osobne serwisy, własne Dockerfile, komunikacja po HTTP i kolejce Valkey |
| Skanowanie zależności (pip/npm), sekrety tylko w `.env` | Opis, §5 | `pip-audit`, `npm audit`, `.env.example`, brak sekretów w repo |
| README minimum, Quick Start, bez „AI slop" | Opis, §5 | README ≤ 1 ekran: wymagania, 1 komenda, konfiguracja |
| Oddajemy: tytuł+opis, prezentacja PDF, README, repo (+film ≤3 min) | Opis, §4 | Osobny blok 08:00–09:30 w harmonogramie |

### 3.1 Licencje — twarde kryterium wdrożeniowe

Mentorzy UKNF wprost zaznaczyli, że stos ma być **czystym open source pod późniejsze wdrożenie
w Urzędzie**. To nie jest kwestia estetyki: licencje silnie copyleft (AGPLv3) i licencje
source-available (SSPL, RSALv2, „gemma") regularnie blokują wdrożenia w administracji publicznej,
bo wymagają albo udostępnienia kodu usługi, albo nie są licencjami OSI.

Dlatego **każda zależność infrastrukturalna ma jawnie zapisaną licencję** i dobieramy wyłącznie
permisywne (MIT / BSD / Apache-2.0 / PostgreSQL).

| Komponent | Licencja | Status |
|---|---|---|
| Valkey 8 (kolejka, cache) | **BSD-3-Clause** | ✅ fork Redisa 7.2.4 pod Linux Foundation, drop-in |
| PostgreSQL 16 | **PostgreSQL License** | ✅ permisywna |
| pgvector | **PostgreSQL License** | ✅ |
| SeaweedFS (object storage, S3 API) | **Apache-2.0** | ✅ |
| FastAPI / Starlette / Uvicorn | **MIT** | ✅ |
| SQLAlchemy | **MIT** | ✅ |
| Playwright (Python) | **Apache-2.0** | ✅ |
| Ollama | **MIT** | ✅ |
| Bielik-4.5B-v3.0-Instruct | **Apache-2.0** | ✅ polski model |
| bge-m3 (embeddingi) | **MIT** | ✅ 1024 wymiary, 8192 tokenów kontekstu |
| faster-whisper + CTranslate2 | **MIT** | ✅ |
| modele Whisper | **MIT** | ✅ |
| yt-dlp | **Unlicense** | ✅ |
| React / Vite / Recharts | **MIT** | ✅ |
| nginx (serwowanie korpusu demo) | **BSD-2-Clause** | ✅ |
| RQ (kolejka zadań) | **BSD-3-Clause** | ✅ |
| rapidfuzz | **MIT** | ✅ |

**Odrzucone świadomie, z powodem:**

| Odrzucone | Licencja | Dlaczego nie |
|---|---|---|
| `redis:7.4` | SSPLv1 / RSALv2 | Nie są licencjami OSI. Redis zmienił licencję w marcu 2024 — to właśnie dlatego powstał Valkey. |
| `redis:8.x` | AGPLv3 | Technicznie OSI, ale silne copyleft sieciowe — ten sam problem wdrożeniowy co MinIO. |
| MinIO | AGPLv3 | Silne copyleft; dodatkowo projekt wszedł w tryb maintenance (grudzień 2025). |
| Garage | AGPLv3 | To samo copyleft co MinIO. |
| `mmlw-retrieval-roberta-large-v2` | **gemma** | Najlepszy polski model retrieval, ale licencja gemma nie jest czystym OSS. **Nie używać.** |

Wariant `redis:7.2-alpine` jest formalnie jeszcze BSD-3, ale nie budujemy na końcówce
ścieżki, z której upstream już zszedł. Valkey jest API-kompatybilny, więc koszt zmiany
to jedna linia w `docker-compose.yml`.

Dla embeddingów polskich jako **upgrade jakościowy** dopuszczamy `sdadas/mmlw-retrieval-e5-base`
(Apache-2.0) — wariant `-base` i `-small` mają czystą licencję, w przeciwieństwie do `roberta-large-v2`.

Wynik: `docs/LICENSES.md` generowany z `pip-licenses` i `license-checker`, dołączony do
oddania. Dla urzędu to realna wartość — dostają stos, który da się wdrożyć bez działu prawnego.

### Jak wagi jury przekładają się na decyzje projektowe

| Kryterium | Waga | Co konkretnie pod to robimy |
|---|---|---|
| Aspekt technologiczny / gotowość demo | **30%** | Deterministyczny korpus demo offline; 3× próba demo przed oddaniem |
| Innowacyjność + **opisany ustandaryzowany proces z asystentami AI** | **20%** | `docs/AI_PROCESS.md`: CLAUDE.md jako kontrakt agenta, graf wiedzy graphify, skills, ADR-y, TDD |
| Architektura: kompozycja modułów, skalowalność, otwartość | **20%** | Kolejka + pluginowalne źródła (`Source` protocol) + pluginowalny rejestr reguł |
| Zgodność ze specyfikacją i preferowanymi technologiami | **20%** | Wszystkie 3 moduły + dokładnie wymienione technologie (Playwright, Ollama, Recharts, WebSocket, CronJob) |
| Atrakcyjność / zaskoczenie | **10%** | `RenderProbe` (pomiar małego druczku w pikselach) + polski Bielik + speech-to-text wideo |

Jury testuje też wprost: skuteczność scrapera, **trafność klasyfikacji i wpływ thresholdu**,
stabilność UI i powiadomień realtime, bezpieczeństwo bibliotek, czystość konsoli.
Każdy z tych punktów ma w planie dedykowany gate.

---

## 4. Rozważone podejścia

Decyzja dotyczy rdzenia Modułu 2 — jak oceniać 18 reguł informacji o ryzyku.

### Podejście A — „wszystko do LLM-a"
Zrzucamy tekst reklamy do Bielika z promptem zawierającym 18 reguł, prosimy o JSON.

- **Za:** najszybsze w implementacji (~2 h), elastyczne.
- **Przeciw:** **fizycznie nie umie** ocenić reguł 4, 5, 6, 8 — rozmiaru czcionki, kontrastu,
  przesłonięcia, responsywności, bo nie widzi geometrii renderu. Niedeterministyczne,
  więc demo może zachować się inaczej niż na próbie. Brak twardego dowodu dla nadzorcy.
- **Odrzucone:** traci 5 z 18 reguł i uderza w anty-cel „czarna skrzynka".

### Podejście B — „wszystko na regułach deterministycznych"
Regexy, słowniki fraz, parsowanie DOM, zero LLM.

- **Za:** szybkie, w pełni powtarzalne, tanie.
- **Przeciw:** nie wychwyci manipulacji i parafraz („nasza inwestycja jest w pełni bezpieczna,
  spełniamy rygorystyczne wymogi KNF" to reguła 18, ale sformułowana na tysiąc sposobów).
  Zrozumiałość dla grupy docelowej (reguła 9) jest nieredukowalnie semantyczna.
- **Odrzucone:** nie realizuje punktu 1 mentorów (rzetelność, manipulacja) i nie wykorzystuje
  wymaganego przez specyfikację silnika inferencji.

### Podejście C — hybryda warstwowa **[WYBRANE]**
Klasyfikujemy 18 reguł według **typu dowodu**, jakiego wymagają, i każdą kierujemy do
właściwego silnika. Jeden wspólny format wyniku.

- **DET (deterministyczne, z geometrii renderu):** reguły 4, 5, 6, 7, 8
- **LLM (semantyczne, Bielik):** reguły 1, 2, 9, 10, 11, 12a, 12b, 14, 15, 16, 17, 18
- **HYBRID:** reguły 3 i 13 łączą wykrycie semantyczne („są twierdzenia o zyskach")
  z pomiarem wizualnym („czy ostrzeżenie jest obok i równie wyeksponowane")

- **Za:** pokrywa wszystkie 18 reguł; każda decyzja ma dowód — albo cytat, albo liczbę
  („7 px vs. mediana 16 px, kontrast 1.9:1"); część deterministyczna jest powtarzalna,
  więc demo jest przewidywalne; mocny wyróżnik wobec innych zespołów.
- **Przeciw:** droższe (~2× czas Modułu 2), wymaga `RenderProbe` w scraperze, czyli
  zależności między strumieniem A i B. Mitygacja: kontrakt `RenderProbe` zamrożony o 12:30.
- **Dlaczego mimo to:** reguła 4 i 5 to dosłownie punkt 5 mentorów („czy małym druczkiem
  nie jest coś ukryte"). Zespół, który to zmierzy w pikselach, wygrywa to porównanie.

**Wybór zespołu:** Podejście C. Stack oddany prowadzącemu: Python + FastAPI + React +
Postgres + Ollama (zgodnie z preferencjami ze specyfikacji), polski model Bielik.

---

## 5. Architektura

```
                       ┌──────────────────────────────┐
                       │  web  (React + Vite)         │
                       │  filtry · wykresy · alerty   │
                       │  PANEL KALIBRACJI (threshold)│
                       └──────────┬───────────────────┘
                            HTTP  │  WebSocket
                       ┌──────────▼───────────────────┐
                       │  api  (FastAPI)              │
                       │  REST · WS broadcast         │
                       └────┬─────────────┬───────────┘
                            │             │
             ┌──────────────▼──┐      ┌───▼──────────────────────┐
             │ Postgres 16     │      │ Valkey  (BSD-3)          │
             │ + pgvector      │      │ RQ + rq-scheduler        │
             │ embeddingi 1024 │      │ ┌──────────────────────┐ │
             └──────────────▲──┘      │ │ q:ingest   (n=4)     │ │
                            │         │ │ q:render   (n=2)     │ │
                            │         │ │ q:gpu      (n=1) ★   │ │
                            │         │ └──────────────────────┘ │
                            │         └───┬──────────────────────┘
         ┌──────────────────┴─────┐       │
         │ analyzer  (Python)     │   ┌───▼────────────────────────┐
         │ ① brama zakresu        │   │ scraper  (Python)          │
         │ ② resolver podmiotów   │   │ · Source plugins           │
         │ ③ ROUTER modułów       │   │ · Playwright + RenderProbe │
         │ ④ rejestr 18 reguł     │   │ · reguły DET 4,5,6,7,8     │
         │    · LLM: Bielik       │   │ · yt-dlp + ffmpeg          │
         │    · HYBRID: 3, 13     │   │ · rotacja UA / proxy       │
         │ ⑤ STT: faster-whisper  │   └───┬────────────────────────┘
         │ ⑥ scoring + agregacja  │       │
         └──────────────────▲─────┘       │
                            │         ┌───▼──────────────────────┐
                 ┌──────────┴───────┐ │ SeaweedFS  (Apache-2.0)  │
                 │ Ollama (MIT)     │ │ S3 API: screenshoty,     │
                 │ · Bielik 4.5B    │ │ wycinki bbox, audio,     │
                 │ · bge-m3 (embed) │ │ wideo, surowy HTML       │
                 └──────────────────┘ └──────────────────────────┘

★ q:gpu ma dokładnie JEDEN worker — to gwarantuje, że Bielik i faster-whisper
  nigdy nie walczą o VRAM. Patrz §9.1.
```

### Układ repozytorium

```
investwatch/
├── services/
│   ├── scraper/          # Playwright, RenderProbe, reguły DET, źródła, worker RQ
│   ├── analyzer/         # scope_gate, resolver, router, silnik reguł, Bielik, whisper, scoring
│   ├── api/              # FastAPI, modele SQLAlchemy, WebSocket
│   └── web/              # React + Vite + Recharts
├── infra/
│   ├── docker-compose.yml
│   └── init.sql
├── fixtures/
│   ├── demo-ads/         # deterministyczny korpus HTML (serwowany przez nginx)
│   └── gold/labels.json  # zbiór złoty do metryk
├── docs/
│   ├── AI_PROCESS.md     # ← 20% oceny
│   ├── LICENSES.md       # ← historia wdrożeniowa dla UKNF (§3.1)
│   ├── ADR/
│   └── superpowers/specs/
└── README.md             # ≤ 1 ekran
```

Każdy serwis ma własny `Dockerfile`, własne zależności i da się go uruchomić osobno.
Komunikacja wyłącznie przez Valkey (kolejka zadań) i Postgres (stan) — brak importów
między serwisami. Reguły DET żyją w `scraper/rules_det/`, reguły LLM w `analyzer/rules_llm/`,
a wspólny jest tylko interfejs `Rule` — dzięki temu dwie osoby nie edytują tych samych plików.

---

## 6. Kontrakty danych (ZAMROŻONE o 12:30)

To najważniejsza sekcja dokumentu. Trzy osoby pracują równolegle na tych strukturach
i **nikt ich nie zmienia bez ogłoszenia całemu zespołowi**. Do czasu gotowości serwisów
każdy pracuje na ręcznie napisanym przykładzie zgodnym z tym kontraktem.

### 6.1 `AdDocument` — to, co produkuje scraper

```json
{
  "id": "uuid",
  "source": "web | facebook | instagram | tiktok | youtube | import",
  "url": "https://...",
  "fetched_at": "2026-11-21T14:03:00Z",
  "publisher": {
    "handle": "@finfluencer_pl",
    "display_name": "Jan Inwestor",
    "profile_url": "https://...",
    "is_official_firm_channel": false
  },
  "lang": "pl",
  "title": "...",
  "text": "pełny znormalizowany tekst widoczny dla użytkownika",
  "html_path": "s3://raw/<id>.html",
  "screenshots": { "desktop": "s3://shots/<id>-1920.png", "mobile": "..." },
  "media": [
    { "kind": "video", "path": "s3://media/<id>.mp4", "duration_s": 34.2 }
  ],
  "transcript": {
    "engine": "faster-whisper-large-v3",
    "lang": "pl",
    "text": "...",
    "segments": [ { "start": 31.8, "end": 34.0, "text": "inwestowanie wiąże się z ryzykiem" } ]
  },
  "render_probe": { "...": "patrz 6.2" },
  "embedding": { "model": "bge-m3", "dim": 1024, "vector": "[...]" },
  "simhash": "a3f1c09e...",
  "scope": { "...": "patrz 6.6" }
}
```

`embedding` i `simhash` są obowiązkowe — specyfikacja wprost wymaga reprezentacji wektorowej
(patrz §6.7). `scope` zastąpiło dawne pole `excluded`, bo wykluczanie zakresu okazało się
problemem instrumentowym, nie słownikowym (patrz §6.6).

### 6.2 `RenderProbe` — geometria renderu, podstawa reguł DET

Zbierane przez Playwright dla **każdego widocznego węzła tekstowego**, na 3 viewportach:
`desktop 1920×1080`, `tablet 768×1024`, `mobile 390×844`.

```json
{
  "viewports": {
    "mobile": {
      "dominant_font_px": 16.0,
      "page_height_px": 4210,
      "nodes": [
        {
          "text": "Zyski do 18% rocznie!",
          "font_px": 34.0,
          "font_weight": 700,
          "color": "#111111",
          "background_effective": "#ffffff",
          "background_source": "ancestor:main>section",
          "background_confidence": "resolved",
          "contrast_ratio": 18.9,
          "bbox": { "x": 24, "y": 310, "w": 342, "h": 44 },
          "visible": true,
          "clipped": false,
          "behind_interaction": null,
          "dom_path": "main>section:nth-of-type(1)>h2",
          "in_footer": false
        },
        {
          "text": "Inwestowanie wiąże się z ryzykiem utraty kapitału.",
          "font_px": 7.0,
          "font_weight": 400,
          "color": "#c9c9c9",
          "background_effective": "#ffffff",
          "background_source": "ancestor:body",
          "background_confidence": "resolved",
          "contrast_ratio": 1.9,
          "bbox": { "x": 24, "y": 4080, "w": 342, "h": 9 },
          "visible": true,
          "clipped": false,
          "behind_interaction": "details",
          "collapsed_evidence": "details[not(@open)]",
          "dom_path": "footer>details>p",
          "in_footer": true
        }
      ]
    }
  }
}
```

`behind_interaction` ∈ `null | "details" | "accordion" | "modal" | "link" | "hidden"`.
To pojedyncze pole realizuje regułę 7 (dostępność za 1 kliknięciem).

### 6.2.1 Hartowanie `RenderProbe` — dwie pułapki, które trzeba obejść

To nie są detale. Obie pułapki dawałyby **fałszywe naruszenia na oczach jury**, czyli
dokładnie najgorszy możliwy rodzaj błędu w narzędziu nadzorczym.

**Pułapka 1: `getComputedStyle().backgroundColor` prawie zawsze zwraca `rgba(0, 0, 0, 0)`.**

Tło jest dziedziczone wizualnie, ale nie w CSS — węzeł tekstowy w 95% przypadków nie ma
własnego tła. Naiwne wyliczenie kontrastu wobec `rgba(0,0,0,0)` potraktowałoby przezroczystość
jako czarne tło i dałoby *wysoki* kontrast dla ciemnego tekstu na białym tle — czyli reguła 5
przepuszczałaby naruszenia, a dla jasnego tekstu zgłaszałaby je bez powodu.

Algorytm wyznaczania tła efektywnego:
1. Idź w górę drzewa od węzła tekstowego, aż znajdziesz przodka z `backgroundColor`
   o `alpha > 0`. Zapisz go w `background_source`.
2. Jeśli po drodze są warstwy częściowo przezroczyste, **komponuj alfa** po kolei
   (`result = over(child, parent)`), a nie bierz pierwszej napotkanej.
3. Jeśli którykolwiek przodek ma `background-image`, gradient lub `backdrop-filter` —
   koloru nie da się wyznaczyć analitycznie. Ustaw `background_confidence: "unknown"`.
4. Jeśli dojdziesz do `html`/`body` bez trafienia, przyjmij tło kanwy (zwykle `#ffffff`)
   i ustaw `background_confidence: "assumed_canvas"`.

`background_confidence` ∈ `resolved | assumed_canvas | unknown`.

**Konsekwencja dla reguły 5, zapisana wprost:** przy `background_confidence == "unknown"`
reguła 5 zwraca **`not_applicable` z powodem**, nigdy `fail`. Nadzorca dostaje informację
„nie dało się zmierzyć kontrastu — tło graficzne, wymaga oceny ręcznej", co jest uczciwe
i obronne. Fałszywy alarm na demo jest znacznie droższy niż przyznanie się do niepewności.

*Stretch (jeśli będzie czas):* fallback przez próbkowanie pikseli ze screenshota —
pobierz kilka pikseli w obrębie `bbox` poza glifami i wyznacz tło empirycznie.
Działa też dla tła graficznego. Realizować tylko po GATE 3.

**Pułapka 2: klikanie akordeonów psuje DOM albo wywołuje nawigację.**

Klik w element, który okazuje się `<a href>` albo ma handler z `window.location`,
przenosi nas na inną stronę i cała sonda leci w kosmos. Dodatkowo klik może zmienić
layout tak, że wcześniej zebrane `bbox` przestają się zgadzać.

**Decyzja: w MVP nie klikamy niczego.** Stan zwinięty rozpoznajemy statycznie:

| Sygnał | Co ustawia |
|---|---|
| `<details>` bez atrybutu `open` | `details` |
| `display:none`, `visibility:hidden`, `opacity:0` | `hidden` |
| `height:0` lub `max-height:0` + `overflow:hidden` | `accordion` |
| `clip-path: inset(100%)`, `clip: rect(0,0,0,0)` | `hidden` |
| `aria-expanded="false"` na przodku-kontrolce | `accordion` |
| `aria-hidden="true"`, atrybut `hidden` | `hidden` |
| tekst ryzyka jest treścią `<a href>` prowadzącego dalej | `link` |
| przodek z `role="dialog"` / `<dialog>` bez `open` | `modal` |

To pokrywa praktycznie wszystkie realne implementacje i zapisujemy, który sygnał zadziałał,
w `collapsed_evidence` — czyli mamy dowód także dla reguły 7.

Jeśli mimo wszystko musimy rozwinąć sekcję, żeby przeczytać treść ryzyka, robimy to
**bez kliknięcia**: `page.evaluate(el => el.open = true)` dla `<details>`, co nie odpala
handlerów nawigacji. Dodatkowo na czas sondowania blokujemy nawigację:
`page.route("**/*", route => route.request().isNavigationRequest() && depth > 0 ? route.abort() : route.continue())`.
Sondę powtarzamy na świeżym `page`, nigdy na tym samym po modyfikacji.

**Dodatkowo:** przed sondowaniem przewijamy stronę do końca (z limitem ~10 kroków),
żeby wymusić doładowanie treści lazy-loaded. Bez tego stopka z ryzykiem może w ogóle
nie istnieć w DOM.

### 6.3 `RuleResult` — wynik jednej reguły

```json
{
  "rule_id": "4",
  "rule_name": "Rozmiar czcionki ryzyka",
  "engine": "DET",
  "verdict": "fail",
  "confidence": 1.0,
  "severity": 4,
  "legal_basis": "art. 44 ust. 2 lit. c rozporządzenia del. 2017/565",
  "evidence": {
    "kind": "measurement",
    "summary": "Ostrzeżenie o ryzyku ma 7.0 px przy dominującej czcionce 16.0 px (44%).",
    "measured": { "risk_font_px": 7.0, "dominant_font_px": 16.0, "ratio": 0.44 },
    "viewport": "mobile",
    "screenshot_crop": "s3://crops/<id>-rule4.png"
  }
}
```

`verdict` ∈ `pass | fail | not_applicable`. `severity` 1–5 (waga w scoringu).
`evidence.kind` ∈ `measurement | quote | absence`. Dla reguł LLM `evidence` zawiera
dosłowny cytat z materiału — **nigdy parafrazę** (nadzorca musi móc zweryfikować).

### 6.4 `Finding` — ujednolicony obiekt wyjściowy wszystkich 3 modułów

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "primary_module": 1,
  "modules": [1, 2],
  "routing": {
    "rule": "R2",
    "reason": "Publikujący @finfluencer_pl nie jest oficjalnym kanałem XYZ DM S.A.; materiał zawiera twierdzenia o zyskach, więc dodatkowo oceniany regułami Modułu 2.",
    "scope_gate": "in_scope"
  },
  "risk_score": 78.5,
  "risk_level": "high | medium | low",
  "rule_results": [ "... RuleResult[] ..." ],
  "entities": {
    "investment_firm": {
      "name_in_ad": "XYZ Dom Maklerski",
      "registry_match": { "knf_id": "DM-123", "official_name": "XYZ DM S.A.", "score": 0.94 },
      "is_authorized": true
    },
    "advertiser": {
      "name": "@finfluencer_pl",
      "relation_to_firm": "third_party | official | unknown",
      "disclosure_found": false,
      "affiliate_link": "https://xyz.pl/?ref=finflu123"
    }
  },
  "status": "new | in_review | confirmed | dismissed",
  "created_at": "2026-11-21T14:05:00Z"
}
```

Kluczowe: **`rule_results` jest zapisywane w całości w bazie**. Dzięki temu panel kalibracji
przelicza flagi bez ponownej inferencji — patrz sekcja 9.

### 6.5 Potok przetwarzania i ROUTER modułów

W pierwotnej wersji designu brakowało jawnego mechanizmu decydującego, do którego modułu
trafia dokument. To była realna luka: bez niej każdy moduł musiałby sam filtrować wszystko,
a trzy osoby pisałyby trzy różne, niespójne heurystyki.

Kolejność etapów w `analyzer` jest sztywna:

```
① ingest → normalizacja (strip HTML, unicode NFC, kolapsowanie spacji)
② tokenizacja → embedding (bge-m3) + simhash → DEDUP
③ BRAMA ZAKRESU            (§6.6)  → in_scope / out_of_scope
④ RESOLVER PODMIOTÓW       (kto publikuje? kogo wymienia? vs rejestr KNF)
⑤ ROUTER                   (§6.5)  → modules[] + primary_module
⑥ EWALUACJA REGUŁ          (DET z RenderProbe · LLM wsadowo · HYBRID)
⑦ SCORING + agregacja      (§9)
⑧ zapis do Postgresa → alert WebSocket przy risk_level == "high"
```

Dokument wypadający w etapie ③ **nie jest kasowany** — trafia do widoku „poza zakresem"
z zapisanym powodem. Nadzorca musi móc zweryfikować, czego narzędzie nie oceniało.

#### Tablica decyzyjna routera

Router jest deterministyczny i ma dokładnie cztery reguły. `authorized` oznacza
obecność w `authorized_entities` (rejestr KNF, §8).

| Reguła | Warunek | `modules` | Uzasadnienie |
|---|---|---|---|
| **R1** | publikujący **jest** oficjalnym kanałem autoryzowanej firmy (zgodna domena lub handle) | `[2]` | materiał własny firmy inwestycyjnej → pełna ocena informacji o ryzyku |
| **R2** | publikujący **nie jest** oficjalnym kanałem, ale materiał wymienia autoryzowaną firmę lub jej produkty | `[1]` + `[2]` jeśli są twierdzenia o zyskach | podmiot trzeci / finfluencer reklamuje coś nieswojego |
| **R3** | publikujący **nie jest** autoryzowany **i** treść zawiera rekomendację dotyczącą instrumentów finansowych | `[3]` + `[2]` jeśli są twierdzenia o zyskach | możliwe doradztwo inwestycyjne bez zezwolenia |
| **R4** | żadne z powyższych | `[]`, status `triage` | do przeglądu ręcznego; zasila listę braków w rejestrze |

**Dwie rzeczy, które wynikają z tej tablicy i są celowe:**

1. **`modules` to zbiór, nie jedna liczba.** Reklama finfluencera, która obiecuje zyski,
   jest jednocześnie przypadkiem Modułu 1 (brak powiązania) i Modułu 2 (jakość informacji
   o ryzyku). Dawny kontrakt z polem `module: int` to uniemożliwiał — dlatego go zmieniliśmy
   przed zamrożeniem.
2. **Pierwszeństwo przy `primary_module`: R3 > R2 > R1.** Świadczenie usług bez zezwolenia
   jest naruszeniem poważniejszym niż brak ujawnienia współpracy, a ten z kolei poważniejszym
   niż uchybienie w ekspozycji ostrzeżenia we własnym materiale licencjonowanej firmy.

`routing.reason` jest **zdaniem po polsku, pokazywanym w dashboardzie**. Nadzorca widzi,
dlaczego dokument wylądował w danym module, i może to zakwestionować. To ten sam wymóg
wyjaśnialności, co `evidence` przy regułach.

### 6.6 Brama zakresu — dlaczego „nie dotykamy krypto" NIE znaczy „filtruj słowo bitcoin"

Pierwotny design miał słownikowy filtr wykluczający materiały ze słowami `krypto`, `bitcoin`,
`token`, `staking`. **To był błąd domenowy i trzeba go opisać wprost, bo jest pouczający.**

Kontrakt na różnicę (CFD) jest instrumentem finansowym na mocy **art. 2 ust. 1 pkt 2 lit. h
ustawy o obrocie instrumentami finansowymi**, niezależnie od tego, co jest jego instrumentem
bazowym. CFD na bitcoina jest więc instrumentem finansowym pod nadzorem KNF — i to akurat
jeden z najagresywniej reklamowanych, najbardziej ryzykownych produktów detalicznych na rynku.
Słownikowy filtr wyciąłby dokładnie te materiały, na których UKNF zależy najbardziej.
Byłby to false negative w najgorszym możliwym miejscu.

**Poprawne kryterium jest instrumentowe, nie aktywowe.** Klasyfikujemy dwuwymiarowo:

- **Opakowanie (instrument):** CFD, kontrakt terminowy, opcja, swap, ETF, ETN, certyfikat
  inwestycyjny, tytuł uczestnictwa w funduszu, akcje, obligacje, prawa pochodne — pełna lista
  wg art. 2 i art. 3 ustawy o obrocie (Załącznik 3 do tematu).
- **Aktywo bazowe:** akcje, indeksy, waluty, towary, stopy procentowe, **kryptoaktywa**,
  nieruchomości, dzieła sztuki.

```
in_scope  ⟺  rozpoznano OPAKOWANIE będące instrumentem finansowym wg art. 2 ustawy o obrocie
             (bez względu na aktywo bazowe)
```

| Materiał reklamowy | Opakowanie | Decyzja |
|---|---|---|
| „CFD na BTC, dźwignia 1:2" | CFD → art. 2 ust. 1 pkt 2 lit. h | **in_scope**, znacznik `crypto_derivative`, **podwyższony priorytet** |
| „ETN na ethereum na GPW" | ETN → zbywalny papier wartościowy, art. 3 | **in_scope** |
| „Fundusz z ekspozycją na kryptoaktywa" | tytuł uczestnictwa → art. 2 ust. 1 pkt 2 lit. a | **in_scope** |
| „Akcje spółki zajmującej się miningiem" | akcje → art. 3 | **in_scope** |
| „Kup bitcoina w naszym kantorze, portfel, staking" | brak opakowania — zakup spot | **out_of_scope**, `reason: spot_crypto_mica` |
| „Zainwestuj w nasz apartament w Zakopanem" | brak opakowania | **out_of_scope**, `reason: not_financial_instrument` |

Zakup spot kryptoaktywów jest poza zakresem **nie dlatego, że zawiera słowo „krypto"**,
ale dlatego, że nie jest instrumentem finansowym w rozumieniu ustawy o obrocie — podlega
odrębnemu reżimowi (MiCA), a nie reżimowi MiFID II, na którym opierają się nasze 18 reguł.
Taka jest właściwa interpretacja wskazania mentorów „nie dotykamy krypto": nie wchodzimy
w domenę kryptoaktywów jako taką, a nie „ślepo odfiltrowujemy słowa kluczowe".

Kontrakt `scope` w `AdDocument`:

```json
{
  "status": "in_scope | out_of_scope | uncertain",
  "instrument_wrapper": "cfd",
  "underlying": "crypto",
  "legal_basis": "art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie instrumentami finansowymi",
  "tags": ["crypto_derivative", "leveraged"],
  "reason": null
}
```

Przy `status: "uncertain"` dokument idzie do `triage`, nie do kosza. Tę decyzję podejmuje
LLM z listą instrumentów z Załącznika 3 w promptcie, a nie regex — bo „kontrakt na różnicę
kursu" i „CFD" i „różnice kursowe z dźwignią" to to samo opakowanie opisane trzema sposobami.

**Kandydat na regułę 19 (do potwierdzenia z mentorami):** reklamy CFD podlegają dodatkowym
wymogom ostrzeżeń o odsetku rachunków detalicznych tracących pieniądze. Jeśli mentorzy
potwierdzą, że to w zakresie, dochodzi reguła sprawdzająca obecność i ekspozycję tego
ostrzeżenia. Rejestr reguł jest otwarty, więc to dopisanie jednej klasy.

### 6.7 Warstwa wektorowa — wymóg specyfikacji, nie ozdoba

Specyfikacja w części „Moduły Analityczne / AI → Preprocessing" wymaga wprost
**„reprezentacji wektorowej w postaci tokenów i embeddingów"**. W pierwotnej drabince
cięcia zakresu `pgvector` był na liście do wyrzucenia — to był błąd, bo ścinałby punkty
w kryterium „zgodność ze specyfikacją" (waga 20%). **Warstwa wektorowa jest nieusuwalna.**

Żeby nie była atrapą, ma trzy konkretne zadania:

1. **Deduplikacja i rozpoznawanie kampanii.** `simhash` łapie warianty niemal identyczne,
   cosine na embeddingach > 0.95 łapie przeredagowane warianty tej samej kampanii.
   W dashboardzie: „ta reklama to 7. wariant kampanii widzianej od 3 dni" — zamiast
   siedmiu osobnych wierszy nadzorca widzi jedną kampanię. To realna oszczędność pracy UKNF.
2. **kNN jako druga opinia, niezależna od LLM.** Dla dokumentu bierzemy k=5 najbliższych
   sąsiadów ze zbioru złotego i liczymy `knn_score` z ich etykiet. W panelu kalibracji
   pokazujemy obie krzywe: scoring regułowy i kNN. Gdzie się rozchodzą, tam jest
   najciekawszy materiał do przeglądu — i to jest ładny, nieoczywisty element demo.
3. **Wyszukiwanie semantyczne w dashboardzie.** „Znajdź podobne" na dowolnym findingu.

**Model:** `bge-m3` przez Ollamę (**MIT**, 1024 wymiary, 8192 tokenów kontekstu,
wielojęzyczny z polskim). Wybrany świadomie zamiast `sentence-transformers`, bo
reużywa runtime, który i tak mamy — zero dodatkowego `torch` w obrazie i zero
dodatkowego zużycia VRAM-u ponad ~1,2 GB.

**Przechowywanie:** kolumna `vector(1024)` w Postgresie z pgvector, indeks `ivfflat`
z `vector_cosine_ops`.

**Upgrade jakościowy, jeśli będzie czas:** `sdadas/mmlw-retrieval-e5-base` (Apache-2.0) —
model trenowany specjalnie pod polski retrieval, lepszy na polskich tekstach niż
wielojęzyczny bge-m3. **Uwaga licencyjna: NIE bierzcie `mmlw-retrieval-roberta-large-v2`** —
mimo najlepszych wyników ma licencję `gemma`, która nie jest czystym open source
i przeczy całej naszej historii wdrożeniowej z §3.1.

---

## 7. Mapowanie 18 reguł na silniki

Źródło reguł: `DocsTaskINWESTWATCH/ZASÓB DLA UCZESTNIKÓW - InvestWatch - kryteria oceny
informacji o ryzyku.docx`. Każda reguła to osobna klasa w rejestrze reguł analizatora,
dzięki czemu dodanie reguły 19 nie wymaga ruszania silnika (kryterium „otwartość na rozbudowę").

| # | Reguła | Silnik | Jak dokładnie | Podstawa prawna (rozp. 2017/565) |
|---|---|---|---|---|
| 1 | Identyfikacja firmy | LLM + registry | NER nazwy firmy + fuzzy match do rejestru KNF | art. 44 ust. 2 lit. a |
| 2 | Oznaczenie reklamy | LLM + regex | szukaj „reklama", „materiał promocyjny", „#ad", „współpraca" | art. 24 ust. 3 MiFID II |
| 3 | Informacja o ryzyku | **HYBRID** | LLM wykrywa twierdzenia o zyskach → DET sprawdza, czy ostrzeżenie jest w pobliżu (bbox) | art. 44 ust. 2 lit. b |
| 4 | Rozmiar czcionki ryzyka | **DET** | `risk_font_px / dominant_font_px`; fail < 0.9 | art. 44 ust. 2 lit. c |
| 5 | Ekspozycja i kontrast | **DET** | `contrast_ratio` WCAG < 4.5 → fail; przy `background_confidence == "unknown"` → `not_applicable`, nigdy `fail` (§6.2.1) | art. 44 ust. 2 lit. c, e |
| 6 | Zakrywanie / ukrywanie | **DET** | `in_footer` + `dom_path` zawiera `footer`/`legal`/`disclaimer` + pozycja y > 85% strony | art. 44 ust. 2 lit. e |
| 7 | Dostępność za 1 klik. | **DET** | `behind_interaction != null` → fail | art. 44 ust. 2 lit. b, e |
| 8 | Responsywność | **DET** | porównaj 3 viewporty: `clipped == true` lub `font_px < 9` na mobile → fail | art. 44 ust. 2 lit. g |
| 9 | Zrozumiałość | LLM | ocena języka ostrzeżenia dla przeciętnego odbiorcy + indeks czytelności | art. 44 ust. 2 lit. d |
| 10 | Spójność językowa | LLM + langdetect | `lang(risk_text) != lang(main_text)` → fail | art. 44 ust. 2 lit. f |
| 11 | Porównania produktów | LLM | wykryj porównanie → sprawdź źródło i założenia | art. 44 ust. 3 |
| 12a | Wyniki hist.: okres i zakres | LLM + regex dat | czy 5 lat, pełne okresy 12-mies., wskazany okres referencyjny i źródło | art. 44 ust. 4 |
| 12b | Wyniki hist.: warunki i waluta | LLM | ostrzeżenie o kursach walut + wpływ prowizji, opłat i obciążeń | art. 44 ust. 4 |
| 13 | Dominacja wyników hist. | **HYBRID** | LLM znajduje wyniki hist. → DET sprawdza, czy to największa czcionka / najwyższy bbox | art. 44 ust. 4 lit. a |
| 14 | Ostrzeżenie przy wynikach | LLM | obecność zastrzeżenia „wyniki historyczne nie są wiarygodnym wskaźnikiem" | art. 44 ust. 4 lit. d |
| 15 | Prognozy przyszłych wyn. | LLM | rozpoznaj prognozę → wymagane wyraźne ostrzeżenie; flaguj w raporcie | art. 44 ust. 6 |
| 16 | Informacja podatkowa | LLM | jeśli mowa o podatkach → czy jest zastrzeżenie o indywidualnej sytuacji klienta | art. 44 ust. 7 |
| 17 | Sugerowanie aprobaty organu | LLM | odwołania do KNF użyte jako zatwierdzenie produktu/usługi | art. 44 ust. 8 |
| 18 | Nadzór jako argument bezp. | LLM | „w pełni bezpieczne — spełniamy rygorystyczne wymogi KNF" | art. 44 ust. 8 |

Progi liczbowe (0.9 dla czcionki, 4.5 dla kontrastu, 9 px dla mobile) są **konfigurowalne
w `analyzer/config/thresholds.yaml`**, nie zahardkodowane. To osobna oś kalibracji
obok globalnego thresholdu scoringu.

---

## 8. Logika modułów

### Moduł 1 — Monitoring ekosystemu zewnętrznego (finfluencerzy)
Realizuje punkt 2 mentorów: *czy osoba reklamująca jest rzeczywiście powiązana z inwestycją*.

1. **Rejestr podmiotów (budowany raz, cache'owany).** Scrapujemy 5 adresów KNF z Załącznika 1/2:
   rejestr firm inwestycyjnych, banki z działalnością maklerską, domy maklerskie, oddziały
   zagranicznych firm inwestycyjnych, zagraniczne firmy bez oddziału. Wynik: tabela
   `authorized_entities(name, normalized_name, knf_id, type, country)`.
2. **Wyszukiwanie reklam** wzmiankujących te firmy lub ich produkty, publikowanych przez
   konta inne niż oficjalne kanały firmy.
3. **Rozpoznanie relacji:** `official` (domena/handle należy do firmy) · `third_party`
   (ktoś inny reklamuje) · `unknown`.
4. **Sygnały finfluencerskie:** brak ujawnienia współpracy (`#reklama`, `współpraca`,
   `materiał promocyjny`), obecność linku afiliacyjnego (`?ref=`, `?aff=`, `utm_campaign`),
   call-to-action do rejestracji rachunku.
5. **Wynik:** `Finding` z `entities.advertiser.relation_to_firm == "third_party"` i
   `disclosure_found == false` → wysoki priorytet. Raport zestawia: dane firmy inwestycyjnej,
   dane reklamującego, treść reklamy, dokładny URL, data — plus mechanizm okresowej
   aktualizacji (scheduler, patrz sekcja 10).

Obejmuje też polskojęzyczne reklamy zagranicznych firm działających w Polsce transgranicznie
— dlatego rejestr zawiera notyfikowane firmy bez oddziału.

### Moduł 2 — Weryfikacja zgodności i informacji o ryzyku ★ gwiazda demo
Realizuje punkty 1 i 5 mentorów. Zakres: materiały publikowane **bezpośrednio przez**
zarejestrowane w Polsce firmy inwestycyjne (w tym polskie oddziały firm zagranicznych).

Pełny silnik 18 reguł z sekcji 7, scoring z sekcji 9. To tutaj idzie najwięcej czasu
i to ten moduł pokazujemy jury najdłużej.

### Moduł 3 — Identyfikacja usług nieautoryzowanych (shadow advisory)
Podstawa prawna z Załącznika 3: art. 76 ustawy o obrocie — doradztwo inwestycyjne to
przekazywanie klientowi **rekomendacji** nabycia, zbycia lub powstrzymania się, dotyczącej
instrumentów finansowych (lista instrumentów: art. 2, papiery wartościowe: art. 3).

1. Szukamy ofert: `wealth management`, `investment consulting`, `family office`,
   `zarządzanie majątkiem`, `doradztwo inwestycyjne`, `portfel`, `sygnały inwestycyjne`.
2. **Dwa warunki muszą zajść jednocześnie** (to chroni przed falą false positives):
   - treść wskazuje na rekomendację konkretnych instrumentów finansowych
     („polecamy akcje X", „nasz portfel", „sygnały kupna", „powiemy, co kupić"), ORAZ
   - podmiot **nie występuje** w rejestrze autoryzowanych firm inwestycyjnych.
3. Zakres rozstrzyga **brama zakresu z §6.6**, czyli kryterium instrumentowe: rekomendacja
   dotycząca CFD na kryptoaktywo **jest** w zakresie (art. 2 ust. 1 pkt 2 lit. h), a doradzanie
   przy zakupie spot bitcoina lub nieruchomości — nie. Wykluczenie jest jawne, z podaną
   podstawą prawną, i widoczne w UI jako osobna zakładka.
4. **Wynik:** raport: dane podmiotu, treść oferty, URL potencjalnego naruszenia.

### Speech-to-text (w MVP)
Reklamy wideo z TikToka / Reels / YouTube'a:

```
yt-dlp → mp4 → ffmpeg -vn -ar 16000 -ac 1 → wav
       → faster-whisper (language="pl") → transcript + segmenty z czasem
       → transcript.text wchodzi jako AdDocument.text do TEGO SAMEGO silnika reguł
```

Dwie rzeczy, które daje nam oś czasu transkryptu i których nie da tekst:
- **Reguła 3 w czasie:** twierdzenie o zyskach w sekundzie 5, ostrzeżenie o ryzyku w 33.8
  na 34.2 sekundy materiału → ryzyko nie „towarzyszy bezpośrednio" informacji o zysku.
- **Tempo ostrzeżenia:** liczba znaków / czas trwania segmentu. Disclaimer przeczytany
  2× szybciej niż reszta narracji to mierzalny sygnał ukrywania.

Model: `faster-whisper` (CTranslate2, MIT, lokalnie). Na CPU startujemy z `medium`,
na GPU `large-v3`. Rozmiar modelu to parametr w `.env`.

---

## 9. Scoring, threshold i metryki

### Wzór
```
risk_score = 100 × Σ(severity_i × confidence_i × [verdict_i == fail])
                   ────────────────────────────────────────────────────
                            Σ(severity_i × [verdict_i != not_applicable])
```
Reguły `not_applicable` (np. 16 dla reklamy bez wzmianki o podatkach) **nie wchodzą do
mianownika** — inaczej reklama milcząca o podatkach dostawałaby sztucznie niski score.

### Panel kalibracji — decyzja, która ratuje demo
`rule_results` są w bazie w całości. Front dostaje je razem z `Finding`, więc przesunięcie
suwaka thresholdu **przelicza flagi natychmiast po stronie klienta, bez requestu do modelu**.
Jury zobaczy płynną reakcję, a nie 20-sekundowe zacięcie.

Pod suwakiem pokazujemy na żywo, liczone na zbiorze złotym:
- macierz pomyłek (TP / FP / FN / TN),
- precision, recall, F1,
- krzywą FP vs. FN w funkcji thresholdu.

To bezpośrednia odpowiedź na kryterium jury „wpływ zmian parametrów progowych na wyniki".

### Zbiór złoty (gold set)
50–60 materiałów ręcznie oznaczonych (`fixtures/gold/labels.json`): etykieta na poziomie
dokumentu (naruszenie / w porządku) oraz, dla ok. 20 z nich, etykiety per reguła.
Bez tego panel kalibracji nie ma co pokazywać, dlatego oznaczanie jest **osobnym zadaniem
w harmonogramie**, a nie czymś „jak zdążymy".

**Skrót, który trzeba wykorzystać:** korpus demo z §10 piszemy sami, celowo łamiąc konkretne
reguły. Dla tych 15–18 materiałów **etykiety znamy z konstrukcji** — zapisujemy je w tym
samym commicie co plik HTML, w `fixtures/demo-ads/<nazwa>.labels.json`. Ręcznego oznaczania
wymaga więc tylko ok. 35 materiałów z danych prawdziwych i z pendrive'a, nie 50. To zmienia
nakład z nierealnego na wykonalny i jest uwzględnione w przebudowanym podziale pracy.

### 9.1 Budżet VRAM i serializacja etapów GPU

Jednoczesne trzymanie w pamięci GPU Bielika 4.5B, faster-whisper `medium` i bge-m3 zapcha
8 GB VRAM-u i zamrozi inferencję w środku demo. Rozwiązujemy to **architekturą, nie
ustawieniami**, bo ustawienie można przypadkiem nadpisać, a kształt kolejki nie.

**Rozwiązanie główne: osobna kolejka `q:gpu` z dokładnie jednym workerem.**

```
q:ingest  (n=4)  normalizacja, simhash, parsowanie — CPU, bezpiecznie równolegle
q:render  (n=2)  Playwright + RenderProbe — CPU/RAM, headless bez GPU
q:gpu     (n=1)  ★ embedding · STT · reguły LLM — JEDEN konsument, zawsze
```

Skoro `q:gpu` ma jeden worker, to z definicji nigdy nie działają równolegle dwa etapy
korzystające z GPU. Nie trzeba niczego zgadywać ani mierzyć — wyklucza to konflikt
konstrukcyjnie. Przy tym etapy i tak następują po sobie logicznie (embedding przy ingescie,
STT po pobraniu wideo, reguły LLM na końcu), więc nic nie tracimy na przepustowości.

**Trzy dodatkowe ustawienia:**

| Ustawienie | Wartość | Dlaczego |
|---|---|---|
| Chromium | `headless` + `--disable-gpu` | headless Chromium bez GPU nie zajmuje VRAM-u w ogóle; tu konflikt znika całkowicie |
| faster-whisper | `device="cpu"`, `compute_type="int8"` | int8 na CPU jest w pełni wystarczające dla 30-sekundowych reklam i **zdejmuje STT z GPU na stałe** |
| Ollama | `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_KEEP_ALIVE=30m` | Bielik 4.5B (~5 GB) + bge-m3 (~1,2 GB) ≈ 6,2 GB — mieści się w 8 GB i nie ma przeładowywania modelu między dokumentami |

**Profile sprzętowe w `.env`** (`PROFILE=cpu | gpu8 | gpu16`):

| Profil | Bielik | Whisper | Embeddingi | Uwagi |
|---|---|---|---|---|
| `cpu` | 4.5B Q8_0 na CPU | `small` int8 CPU | bge-m3 CPU | wolne, ale działa wszędzie; plan B na demo |
| `gpu8` | 4.5B Q8_0 GPU | `medium` int8 **CPU** | bge-m3 GPU | **profil domyślny** |
| `gpu16` | 11B v2.3 Q4_K_M GPU | `large-v3` GPU | bge-m3 GPU | jeśli mamy ≥16 GB VRAM |

Profil `cpu` musi być przetestowany **przed** demo, nie w trakcie. Jeśli maszyna demowa
okaże się inna niż deweloperska, przełączenie jednej zmiennej w `.env` ratuje prezentację.

---

## 10. Pozyskiwanie danych i bezpieczeństwo demo

### Pluginowalne źródła
```python
class Source(Protocol):
    name: str
    def discover(self, query: str) -> Iterable[str]: ...   # → URL-e
    def fetch(self, url: str) -> AdDocument: ...
```
Implementacje: `LocalCorpusSource`, `WebPageSource`, `YouTubeSource`, `FacebookAdsSource`,
`InstagramSource`, `TikTokSource`, `PendriveImportSource`. Dodanie źródła nie rusza rdzenia.

### Kolejka i harmonogram
**Valkey** (BSD-3, patrz §3.1) + RQ (lżejsze od Celery, szybsze do postawienia).
Valkey jest API-kompatybilny z Redisem, więc `rq` i `redis-py` działają bez zmian w kodzie —
różnica to jedna linia obrazu w `docker-compose.yml`.

Trzy kolejki o różnej współbieżności (`q:ingest`, `q:render`, `q:gpu` — patrz §9.1);
`q:gpu` z jednym workerem jest zabezpieczeniem przed konfliktem o VRAM.

`rq-scheduler` jako mechanizm CronJob wymagany przez specyfikację: cykliczne odświeżanie
źródeł co N minut → to jest „mechanizm okresowej aktualizacji" z Modułu 1. Rotacja
User-Agent i opcjonalne proxy w nagłówkach, konfigurowane z `.env`.

### Bezpieczeństwo demo (anty-cel: „demo zależne od wifi")
To najpoważniejsze ryzyko operacyjne całego projektu. FB/IG/TikTok agresywnie blokują,
a sala hackathonowa to nieprzewidywalna sieć.

**Mitygacja dwutorowa:**
1. `fixtures/demo-ads/` — 15–18 ręcznie napisanych stron HTML serwowanych przez nginx
   **wewnątrz docker-compose**. Każda celowo łamie inny zestaw reguł: ostrzeżenie 7 px,
   ryzyko schowane w `<details>`, disclaimer w stopce przy y=98%, „bezpieczne bo KNF",
   dominujące wyniki historyczne, prognoza bez ostrzeżenia, ostrzeżenie po angielsku
   w polskiej reklamie, tekst ucinany na 390 px. Demo działa **całkowicie offline**
   i zawsze identycznie.
2. Prawdziwe scrapery pokazujemy na źródłach, które nie blokują: publiczne strony firm
   inwestycyjnych, YouTube przez yt-dlp, oraz import danych z pendrive'a od organizatora
   (zapowiedziany w §7 opisu wyzwania — **odebrać ze stoiska UKNF jak najwcześniej**).

Na demo pokazujemy jedno prawdziwe pobranie na żywo (dowód, że scraper działa) i resztę
na korpusie deterministycznym (dowód, że analiza działa).

### Cybersec (kryterium oceniane wprost)
- `pip-audit` i `npm audit` uruchamiane i **wynik wklejony do README**.
- Zależności przypięte do wersji (`requirements.txt` z `==`, `package-lock.json` w repo).
- Sekrety wyłącznie w `.env`, w repo tylko `.env.example`; `.env` w `.gitignore`.
- Kontenery z użytkownikiem nie-root, obrazy `-slim`.
- Brak płatnych/zewnętrznych API — weryfikowalne przez przegląd `requirements.txt`.
- **`docs/LICENSES.md`** generowany z `pip-licenses` i `license-checker`: każda zależność
  z licencją, zero AGPL / SSPL / „gemma" (§3.1). To nasza odpowiedź na „czysty open source
  pod wdrożenie w UKNF" i jednocześnie element weryfikowalnego łańcucha dostaw.
- ESLint `no-console` jako error → czysta konsola na demo (jury sprawdza).

---

## 11. Co zostaje do decyzji budującemu

Świadomie nierozstrzygnięte, bo nie zmienia kształtu produktu:
- Wariant Bielika: `SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0` (5.1 GB, 8K ctx, szybki)
  vs. `SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M` (mocniejszy, wolniejszy).
  **Decyzja należy do osoby B po pierwszym pomiarze na sprzęcie, który faktycznie mamy.**
  Zacznij od 4.5B — przy 18 regułach × dziesiątki dokumentów przepustowość wygrywa.
- Biblioteka UI (shadcn/ui vs. Mantine vs. czysty CSS) — wybór osoby C, byle open source
  i architektura oparta o propsy (wymóg ze specyfikacji).
- Dokładne brzmienie promptów dla reguł LLM — iterowane na zbiorze złotym.
- Czy `q:render` dostaje 2 czy 3 workery — zależy od RAM-u maszyny, Chromium zjada ~300 MB
  na instancję. Decyzja osoby A po pomiarze.
- Czy w `fixtures/demo-ads` robimy osobny plik na regułę, czy łączymy po 2–3 naruszenia
  na materiał. Sugestia: łączyć, bo realne reklamy łamią kilka reguł naraz, a demo wygląda
  wtedy wiarygodniej.

Rozstrzygnięte po review zespołu (nie są już otwarte): dedup robimy **i** simhashem **i**
cosine na embeddingach, bo łapią różne klasy duplikatów (§6.7); Valkey zamiast Redisa
i SeaweedFS zamiast MinIO (§3.1); STT na CPU (§9.1).

---

## 12. Definicja sukcesu

O 10:15 dnia 22.11 mamy oddane: repo, README z Quick Startem, prezentację PDF, opis z tytułem,
film ≤3 min. A na demo, z jednego `docker compose up`, w tej kolejności:

1. Scraper pobiera na żywo jedną prawdziwą stronę → wiersz pojawia się w dashboardzie.
2. Moduł 2 pokazuje reklamę z oceną 18 reguł i **dowodem liczbowym** dla małego druczku
   („7 px vs. 16 px, kontrast 1.9:1, schowane w `<details>`") plus wycinek screenshota.
3. Reklama wideo → transkrypcja Whisperem → ostrzeżenie o ryzyku w sekundzie 33.8 z 34.2.
4. Moduł 1 pokazuje finfluencera reklamującego firmę, z którą nie ma ujawnionego związku,
   z linkiem afiliacyjnym.
5. Moduł 3 pokazuje „family office" dające rekomendacje bez wpisu w rejestrze KNF.
6. **Brama zakresu:** dwie reklamy krypto obok siebie — CFD na BTC wchodzi do analizy
   z podstawą prawną art. 2 ust. 1 pkt 2 lit. h, zakup spot zostaje odrzucony jako MiCA.
   To slajd, który pokazuje, że rozumiemy dziedzinę, a nie tylko filtrujemy słowa.
7. **Kampania:** siedem wariantów tej samej reklamy zwinięte w jeden wiersz przez dedup
   na embeddingach, z licznikiem wariantów.
8. Suwak thresholdu → precision/recall i macierz pomyłek zmieniają się natychmiast;
   obok krzywa kNN jako druga, niezależna opinia.
9. Alert realtime wpada po WebSocket w trakcie prezentacji.
10. Konsola przeglądarki pusta.
11. `docs/LICENSES.md` — cały stos na MIT / BSD / Apache-2.0, gotowy do wdrożenia w UKNF
    bez rozmowy z działem prawnym.
