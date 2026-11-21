# InvestWatch — stan projektu

**Aktualizacja:** 2026-11-21, wieczór · **Deadline oddania:** 2026-11-22, 11:00

Dokument dla całego zespołu. Opisuje stan **faktyczny**, nie zamierzony — jeśli coś
jest niezweryfikowane, jest to napisane wprost.

---

## 1. Co działa i jest zweryfikowane

### Osoba A — `services/scraper` (zmergowane, PR #2)

| Element | Stan |
|---|---|
| `FacebookAdsSource` z trybem replay | ✅ |
| `RenderProbe` (geometria renderu, 3 viewporty) | ✅ |
| Reguły DET 4–8, z nadpisaniami typografii Meta | ✅ |
| Korpus 8 reklam z Meta Ad Library (`page.html` + `node.json.gz`) | ✅ |
| Złoty `AdDocument` + `RuleResult` jako przykłady kontraktowe | ✅ |

### Osoba B — `services/analyzer` (gałąź `worktree-investwatch-plan`)

**414 testów przechodzi**, kontrola zgodności czysta, zweryfikowane na żywym Bieliku.

| Element | Stan |
|---|---|
| Kontrakty danych (pydantic) | ✅ pola **identyczne** z kopią scrapera, pilnuje test |
| Brama zakresu (kryterium instrumentowe) | ✅ CFD/ETP na krypto **zostaje** w zakresie |
| Router R1–R4 | ✅ |
| 12 reguł LLM w 4 wsadach wsadowych | ✅ |
| Reguła 3 (hybrydowa: geometria / czas / tekst) | ✅ |
| Reguła 10 (hybrydowa: spójność językowa) | ✅ |
| Moduł 3 — shadow advisory | ✅ |
| Scoring + eskalacja po najcięższym naruszeniu | ✅ |
| Embeddingi bge-m3 (1024) + simhash + dedup kampanii | ✅ |
| Worker kolejki `q:gpu` + klient API + `/health` | ✅ |
| Transkrypcja wpięta jako etap ① potoku | ✅ kod gotowy, **brak plików do przerobienia** |
| Metryki: macierz pomyłek, F1, przemiatanie progów | ✅ |
| Dockerfile analyzera | ✅ napisany, **nieprzetestowany** (brak Dockera) |

### Osoba C — `services/api`, `services/web`

**Zero commitów.** Serwisy nie istnieją. Przygotowany punkt startowy: `infra/`
z compose, `init.sql` pokrywającym 100% pól obu kontraktów, i README pisanym pod nią.

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

## 3. Metryki na zbiorze złotym — słabe, i wiemy dlaczego

```
8 pozycji, wszystkie ze realnym score
F1 maksymalne:            0,545
Przy progu domyślnym 50:  TP=0  FP=0  FN=3  TN=5
```

**Przyczyną nie jest klasyfikator, a pokrycie.** `coverage` wynosi 0,00–0,46, czyli
oceniamy mniej niż połowę reguł:

- **5 z 8 reklam to wideo bez transkrypcji** — obietnice zysku są prawdopodobnie
  w narracji, której nie słyszymy
- **7 z 8 nie ma `RenderProbe`** — odpadają reguły DET 4–8 i oś geometrii reguły 3
- 8 pozycji to mało; zmiana jednej etykiety przesuwa F1 o kilka dziesiątych

Etykiety `is_violation` nadane z treści reklam, **bez patrzenia na score** — inaczej
metryki wyszłyby sztucznie idealne i bezwartościowe. Nic nie było podkręcane.

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
3. Reguła 13 (dominacja wyników historycznych) — hybrydowa, wymaga porównania
   rozmiaru czcionki z największą na stronie.

### Osoba C
1. `services/api` — FastAPI, `POST /findings`, `GET /findings` z filtrami, WebSocket.
2. `services/web` — tabela findingów, widok szczegółów z `evidence`, wykresy,
   **panel kalibracji**.
3. Usunąć `profiles: ["full"]` z `infra/docker-compose.yml`, gdy serwisy powstaną.

### Wspólne, blok dokumentacyjny
`README.md` (Quick Start ≤ 1 ekran), `docs/AI_PROCESS.md` (**20% oceny**),
`docs/LICENSES.md`, prezentacja PDF, opcjonalny film ≤ 3 min.

---

## 6. Do udoskonalenia — uszeregowane po wpływie na demo

1. **Transkrypcje korpusu.** Podniosą pokrycie z ~0,4 do ~0,8 i dopiero wtedy metryki
   będą coś znaczyć. Największy zwrot z pracy w całym projekcie.
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
6. Reguła 13 i wycinki screenshotów przy `evidence` (mocny wizualnie dowód).

---

## 7. Znane ograniczenia — mówimy je wprost

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
| 13 | HYBRID (dominacja wyników hist.) | A | ⬜ |
| M3 | LLM + rejestr | B | ✅ |
