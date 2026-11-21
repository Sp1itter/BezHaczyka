# InvestWatch — plan wykonawczy 23 h

**Start:** 2026-11-21, 11:50 · **Hard deadline oddania:** 2026-11-22, **11:00**
**Submit o:** 10:15 (45 min buforu — po 11:00 regulamin nie dopuszcza oceny)
**Zespół:** 3 osoby · Design: `2026-11-21-investwatch-design.md`

---

## Podział roli

| Osoba | Rola | Odpowiada za |
|---|---|---|
| **A** | Dane i scraping | `services/scraper`, `RenderProbe`, źródła, MinIO, kolejka RQ, scheduler, korpus demo |
| **B** | AI i reguły | `services/analyzer`, Bielik/Ollama, faster-whisper, 18 reguł, scoring, zbiór złoty, metryki |
| **C** | API i dashboard | `services/api`, Postgres, WebSocket, `services/web`, panel kalibracji, wykresy, docker-compose |

**Zasada integracji:** nikt nie czeka na nikogo. Kontrakty z sekcji 6 design doca są zamrożone
o 12:30, a do czasu gotowości serwisów każdy pracuje na własnym pliku-przykładzie
(`fixtures/contract-examples/*.json`) zgodnym z kontraktem.

---

## T-0 — 11:50–12:30 · KICKOFF (wszyscy razem, 40 min)

Najważniejsze 40 minut całego hackathonu. Nie kodujemy jeszcze — ustawiamy tory.

**Natychmiast, w pierwszych 5 minutach, w tle (to są największe pobrania, blokują wszystko):**
```bash
# Osoba B, uruchom OD RAZU i zostaw w tle:
ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0     # ~5.1 GB
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M    # ~7 GB, zapas
python -c "from faster_whisper import WhisperModel; WhisperModel('medium')"   # ~1.5 GB

# Osoba A, uruchom OD RAZU:
playwright install chromium
docker pull postgres:16 redis:7 minio/minio nginx:alpine
```

**Równolegle, w tych samych 40 minutach:**
- [ ] **A:** idzie na stoisko UKNF i **odbiera pendrive z próbkami danych** (§7 opisu wyzwania).
      To jedyne zadanie poza budynkiem — zrobić teraz, nie o 3 w nocy.
- [ ] **C:** tworzy repo, strukturę katalogów z design doca, pusty `docker-compose.yml`
      ze wszystkimi serwisami (puste Dockerfile), `.env.example`, `.gitignore`, pusha `main`.
- [ ] **B:** zapisuje `fixtures/contract-examples/` — po jednym ręcznie napisanym JSON-ie
      dla `AdDocument`, `RenderProbe`, `RuleResult`, `Finding`. **To jest kontrakt.**
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

### A — scraper
- [ ] `Source` protocol + `LocalCorpusSource` (czyta `fixtures/demo-ads/*.html`).
- [ ] Playwright: otwórz stronę → **`RenderProbe` dla viewportu `mobile`** (tylko jeden na razie).
      Zbierz: `text`, `font_px`, `color`, `background`, `bbox`, `visible`, `dom_path`.
- [ ] `dominant_font_px` = mediana `font_px` ważona długością tekstu.
- [ ] Zapis `AdDocument` jako JSON do pliku. Postgres podłączamy później.
- [ ] 3 pierwsze pliki w `fixtures/demo-ads/`: jedna reklama czysta, jedna z ostrzeżeniem 7 px,
      jedna z ryzykiem w `<details>`.

### B — analyzer
- [ ] Rejestr reguł: `Rule` z `id`, `engine`, `severity`, `legal_basis`, `evaluate(doc) -> RuleResult`.
- [ ] **Pierwsze 3 reguły DET: 4 (czcionka), 5 (kontrast), 7 (za kliknięciem).**
      Kontrast licz wzorem WCAG na podstawie `color` i `background` z `RenderProbe`.
- [ ] Klient Ollamy + **jedna** reguła LLM: 18 (nadzór jako argument bezpieczeństwa) —
      najefektowniejsza na demo i najłatwiejsza do promptowania.
- [ ] Funkcja `score(rule_results) -> risk_score` wg wzoru z sekcji 9.
- [ ] Prompty w `analyzer/prompts/rule_NN.txt`, nie w kodzie.

### C — api + web
- [ ] Postgres: `documents`, `findings`, `authorized_entities`. `rule_results` jako `JSONB`.
- [ ] FastAPI: `POST /documents`, `GET /findings` (z filtrami: data, źródło, poziom, moduł),
      `PATCH /findings/{id}/status`, `WS /ws/alerts`.
- [ ] React + Vite: tabela findingów z filtrami, zaciągana z API.
- [ ] `docker compose up` stawia postgres + redis + minio + api + web.
- [ ] ESLint z `no-console: error` **od początku** (potem nikt tego nie posprząta).

**GATE 1 — 15:00, 20 min, wszyscy razem**
Jeden plik HTML z `fixtures/demo-ads/` → scraper → analyzer → API → **wiersz widoczny
w przeglądarce z oceną 4 reguł i risk_score**. Jeśli to nie działa o 15:20, przerywamy
wszystko inne i naprawiamy integrację. Przepływ przez wszystkie 4 serwisy jest ważniejszy
niż jakakolwiek funkcja.

---

## T+3.5 — 15:20–19:00 · Szerokość (3,5 h, równolegle)

### A — scraper
- [ ] `RenderProbe` na **3 viewportach** (1920 / 768 / 390) → odblokowuje regułę 8.
- [ ] `behind_interaction`: detekcja `<details>`, akordeonów (klik zmienia wysokość),
      `display:none`, `visibility:hidden`, linków, modali.
- [ ] `in_footer` + pozycja względna `bbox.y / page_height_px` → odblokowuje regułę 6.
- [ ] Screenshoty pełnej strony + **wycinki `bbox` dla ostrzeżenia o ryzyku** → MinIO.
      Te wycinki są tym, co jury zobaczy obok liczb. Nie pomijać.
- [ ] Kolejka RQ + worker. `WebPageSource` dla prawdziwych stron.
- [ ] Rotacja User-Agent z listy w `.env`.
- [ ] Korpus demo rośnie do **12 plików**, każdy łamie inny zestaw reguł.

### B — analyzer
- [ ] **Wszystkie reguły DET: 4, 5, 6, 7, 8.**
- [ ] **Reguły LLM: 1, 2, 9, 10, 11, 12a, 12b, 14, 15, 16, 17, 18.**
      Grupuj po 3–4 reguły w jednym wywołaniu Bielika z wymuszonym JSON-em — 18 osobnych
      requestów na dokument zabije przepustowość.
- [ ] **Reguły HYBRID: 3 i 13.** Reguła 3: LLM zwraca cytaty twierdzeń o zyskach → DET
      sprawdza odległość `bbox` najbliższego ostrzeżenia. Reguła 13: LLM znajduje wyniki
      historyczne → DET porównuje ich `font_px` z największym na stronie.
- [ ] Filtr wykluczający krypto (słownik: `krypto`, `bitcoin`, `token`, `NFT`, `staking`,
      `DeFi`, `altcoin`, `blockchain`) → `excluded.reason = "crypto_out_of_scope"`.
- [ ] Każda reguła ma test na przykładzie z korpusu. Reguły DET są deterministyczne,
      więc testy są tanie i warto je mieć.

### C — api + web
- [ ] Widok szczegółów findingu: lista 18 reguł, verdict, **evidence (cytat lub pomiar)**,
      podstawa prawna, wycinek screenshota. To jest ekran, na którym jury spędzi najwięcej czasu.
- [ ] Wykresy trendów (Recharts): liczba incydentów w czasie, rozkład po modułach,
      najczęściej łamane reguły.
- [ ] Zmiana statusu findingu (`new` → `in_review` → `confirmed` / `dismissed`).
- [ ] WebSocket: broadcast przy `risk_level == "high"`, toast w UI.
- [ ] Filtr „wykluczone z zakresu (krypto)" jako widoczna zakładka.

**GATE 2 — 19:00, 30 min, wszyscy razem**
Wszystkie 18 reguł zwraca `RuleResult` dla całego korpusu demo. Dashboard pokazuje
szczegóły z dowodami. Robimy **pierwszy przejazd próbny demo** — na głos, z zegarkiem.
Co się sypie, trafia na listę do naprawy.

---

## T+7.5 — 19:00–22:00 · Moduły 1 i 3, wideo, zbiór złoty (3 h)

### A — scraper
- [ ] **Rejestr KNF:** scrape 5 adresów z Załącznika 1/2 → `authorized_entities`.
      Normalizacja nazw (usuń „S.A.", „sp. z o.o.", małe litery, bez ogonków) pod fuzzy match.
- [ ] `YouTubeSource` przez yt-dlp: pobierz wideo → `ffmpeg -vn -ar 16000 -ac 1` → wav → MinIO.
- [ ] Import z pendrive'a organizatora (`PendriveImportSource`).
- [ ] Scheduler (`rq-scheduler`): cykliczne odświeżanie źródeł — „mechanizm okresowej
      aktualizacji" wymagany przez Moduł 1.

### B — analyzer
- [ ] **faster-whisper, `language="pl"`** → `transcript` z segmentami czasowymi.
- [ ] Reguła 3 na osi czasu: pozycja ostrzeżenia względem twierdzenia o zyskach w sekundach.
- [ ] Tempo ostrzeżenia: `len(text) / (end - start)` vs. mediana dla reszty materiału.
- [ ] **Moduł 1:** fuzzy match nazwy firmy z reklamy do rejestru (rapidfuzz, próg 0.85),
      `relation_to_firm`, detekcja ujawnienia współpracy, detekcja linku afiliacyjnego.
- [ ] **Moduł 3:** słownik fraz doradczych + warunek podwójny (rekomendacja ORAZ brak
      w rejestrze). Instrumenty finansowe wg listy z Załącznika 3.
- [ ] **Zbiór złoty: 50 pozycji oznaczonych** w `fixtures/gold/labels.json`.
      Robi to osoba B, ale jeśli jest w tyle — przejmuje to osoba A po skończeniu rejestru.
      **Bez tego panel kalibracji nie ma czego pokazać.**
- [ ] Skrypt `evaluate.py`: precision / recall / F1 / macierz pomyłek dla danego thresholdu.

### C — api + web
- [ ] **Panel kalibracji:** suwak thresholdu → przeliczanie flag **po stronie klienta**
      z `rule_results` już obecnych w odpowiedzi API. Zero requestów do modelu.
- [ ] Pod suwakiem: macierz pomyłek, precision, recall, F1 na zbiorze złotym.
- [ ] Wykres FP vs. FN w funkcji thresholdu.
- [ ] Odtwarzacz wideo z transkryptem i zaznaczonym segmentem ostrzeżenia na osi czasu.
- [ ] Widok Moduł 1: firma ↔ reklamujący ↔ relacja ↔ link afiliacyjny.

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

**Prezentacja PDF, maks. 10 slajdów, w tej kolejności:**
1. Problem — skala treści inwestycyjnych w polskim internecie, czego UKNF nie przejrzy ręcznie.
2. Co zbudowaliśmy — architektura, jeden diagram.
3. **Moduł 2 i mały druczek** — zrzut z liczbami: 7 px vs. 16 px, kontrast 1.9:1. To slajd,
   który zapamiętają.
4. Moduł 1 — finfluencer bez ujawnionego związku z firmą + link afiliacyjny.
5. Moduł 3 — doradztwo bez zezwolenia, z podstawą prawną (art. 76 ustawy o obrocie).
6. Speech-to-text — ostrzeżenie w sekundzie 33.8 z 34.2.
7. **Metryki** — precision / recall / F1 + krzywa thresholdu. Prawdziwe liczby ze zbioru złotego.
8. Proces wytwarzania z asystentami AI (streszczenie `AI_PROCESS.md`).
9. Stack: wyłącznie open source, on-premise, zero płatnych API, polski model Bielik.
10. Co dalej — droga do pilotażu w UKNF.

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

| Priorytet | Element | Ciąć? |
|---|---|---|
| 1 | Moduł 2: reguły DET (4,5,6,7,8) + dashboard | **Nigdy.** To rdzeń i wyróżnik. |
| 2 | Panel kalibracji + metryki na zbiorze złotym | **Nigdy.** Jury testuje to wprost. |
| 3 | `docker compose up` jednym poleceniem | **Nigdy.** Twardy wymóg specyfikacji. |
| 4 | Moduł 2: reguły LLM | Zredukuj do 6 najefektowniejszych (1, 2, 3, 15, 17, 18) |
| 5 | Moduł 1 (rejestr KNF + finfluencerzy) | Zredukuj do statycznego rejestru z pliku JSON |
| 6 | Moduł 3 (shadow advisory) | Zredukuj do słownika fraz + sprawdzenia rejestru |
| 7 | Speech-to-text | Zredukuj: 2 wideo przetranskrybowane offline wcześniej |
| 8 | WebSocket alerty | Zamień na polling co 5 s (wizualnie nie do odróżnienia na demo) |
| 9 | Wykresy trendów | Zostaw jeden |
| 10 | pgvector / dedup / MinIO | Zrzuć na dysk lokalny |
| 11 | Film 3 min | Pomiń, jest opcjonalny |

---

## Rejestr ryzyk

| Ryzyko | Prawdopodob. | Mitygacja | Kto pilnuje |
|---|---|---|---|
| Social media blokują scraping | **wysokie** | Korpus demo offline w compose; demo nie zależy od sieci | A |
| Bielik za wolny na naszym sprzęcie | średnie | Zacznij od 4.5B Q8_0; grupowanie reguł w jedno wywołanie; fallback na mniejszy quant | B |
| Pobranie modeli nie zdąży | średnie | **Uruchomione w minucie 0**, nie o 15:00 | B |
| Integracja sypie się o 19:00 | średnie | Kontrakty zamrożone o 12:30 + GATE 1 już o 15:00 | wszyscy |
| Zbiór złoty nie powstanie | **wysokie** | Osobny blok czasowy; jeśli B w tyle, przejmuje A | B → A |
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
