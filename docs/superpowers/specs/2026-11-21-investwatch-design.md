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
| Wyłącznie open source, on-premise, **zero płatnych API** | Opis, §5 | Ollama + Bielik, faster-whisper, Postgres, MinIO, Redis |
| Docker + Docker Compose, start jedną komendą | Opis, §5 | `infra/docker-compose.yml` jest artefaktem pierwszej klasy |
| Modułowa architektura lekkich serwisów, separacja FE/BE/AI | Opis, §5 | 4 osobne serwisy, własne Dockerfile, komunikacja po HTTP/Redis |
| Skanowanie zależności (pip/npm), sekrety tylko w `.env` | Opis, §5 | `pip-audit`, `npm audit`, `.env.example`, brak sekretów w repo |
| README minimum, Quick Start, bez „AI slop" | Opis, §5 | README ≤ 1 ekran: wymagania, 1 komenda, konfiguracja |
| Oddajemy: tytuł+opis, prezentacja PDF, README, repo (+film ≤3 min) | Opis, §4 | Osobny blok 08:00–09:30 w harmonogramie |

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
             ┌──────────────▼──┐      ┌───▼──────────────┐
             │ Postgres        │      │ Redis (kolejka)  │
             │ + pgvector      │      │ RQ + scheduler   │
             └──────────────▲──┘      └───┬──────────────┘
                            │             │
         ┌──────────────────┴─────┐   ┌───▼────────────────────────┐
         │ analyzer  (Python)     │   │ scraper  (Python)          │
         │ · rejestr 18 reguł     │   │ · Source plugins           │
         │ · DET: geometria       │   │ · Playwright + RenderProbe │
         │ · LLM: Bielik/Ollama   │   │ · yt-dlp + ffmpeg          │
         │ · STT: faster-whisper  │   │ · rotacja UA / proxy       │
         │ · scoring + agregacja  │   └───┬────────────────────────┘
         └──────────────────▲─────┘       │
                            │         ┌───▼──────────────┐
                       ┌────┴─────┐   │ MinIO            │
                       │ Ollama   │   │ screenshoty,     │
                       │ Bielik   │   │ audio, wideo     │
                       └──────────┘   └──────────────────┘
```

### Układ repozytorium

```
investwatch/
├── services/
│   ├── scraper/          # Playwright, RenderProbe, źródła, worker RQ
│   ├── analyzer/         # silnik reguł, Bielik, whisper, scoring
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
│   ├── ADR/
│   └── superpowers/specs/
└── README.md             # ≤ 1 ekran
```

Każdy serwis ma własny `Dockerfile`, własne zależności i da się go uruchomić osobno.
Komunikacja wyłącznie przez Redis (zadania) i Postgres (stan) — brak importów między serwisami.

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
  "html_path": "minio://raw/<id>.html",
  "screenshots": { "desktop": "minio://shots/<id>-1920.png", "mobile": "..." },
  "media": [
    { "kind": "video", "path": "minio://media/<id>.mp4", "duration_s": 34.2 }
  ],
  "transcript": {
    "engine": "faster-whisper-large-v3",
    "lang": "pl",
    "text": "...",
    "segments": [ { "start": 31.8, "end": 34.0, "text": "inwestowanie wiąże się z ryzykiem" } ]
  },
  "render_probe": { "...": "patrz 6.2" },
  "excluded": { "is_excluded": false, "reason": null }
}
```

`excluded` obsługuje wyłączenie krypto: `{"is_excluded": true, "reason": "crypto_out_of_scope"}`.

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
          "background": "#ffffff",
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
          "background": "#ffffff",
          "contrast_ratio": 1.9,
          "bbox": { "x": 24, "y": 4080, "w": 342, "h": 9 },
          "visible": true,
          "clipped": false,
          "behind_interaction": "details",
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
    "screenshot_crop": "minio://crops/<id>-rule4.png"
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
  "module": 1,
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
| 5 | Ekspozycja i kontrast | **DET** | `contrast_ratio` WCAG < 4.5 → fail; sprawdź przesłonięcie i `visible` | art. 44 ust. 2 lit. c, e |
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
3. Krypto, nieruchomości, dzieła sztuki → `excluded`, bo nie są instrumentami finansowymi
   w rozumieniu ustawy. Wyłączenie jest jawne i widoczne w UI.
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
Redis + RQ (lżejsze od Celery, szybsze do postawienia). `rq-scheduler` jako mechanizm
CronJob wymagany przez specyfikację: cykliczne odświeżanie źródeł co N minut → to jest
„mechanizm okresowej aktualizacji" z Modułu 1. Rotacja User-Agent i opcjonalne proxy
w nagłówkach, konfigurowane z `.env`.

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
- Czy dedup robimy przez simhash czy przez pgvector + cosine. Oba akceptowalne.
- Dokładne brzmienie promptów dla reguł LLM — iterowane na zbiorze złotym.

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
6. Suwak thresholdu → precision/recall i macierz pomyłek zmieniają się natychmiast.
7. Alert realtime wpada po WebSocket w trakcie prezentacji.
8. Konsola przeglądarki pusta.
