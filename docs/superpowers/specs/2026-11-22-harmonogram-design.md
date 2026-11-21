# Harmonogram i orkiestracja — dokument projektowy

**Data:** 2026-11-21 · **Właściciel:** Osoba B · **Zakres:** Moduł 1, część „Harmonogram"

---

## 1. Co wymaga specyfikacja

Opis wyzwania, sekcja „Backend & Scraping Engine":

> **Harmonogram:** CronJob jako mechanizm uruchamiania scrapperów lub system orchestratora.

A Moduł 1 wymaga w opisie rezultatu:

> Automatyczny raport/baza zestawiająca: dane firmy inwestycyjnej, dane podmiotu
> reklamującego, treść reklamy oraz jej dokładną lokalizację (URL) **wraz
> z mechanizmem okresowej aktualizacji**.

## 2. Przeramowanie: nie „odświeżanie", a wykrywanie zmian

Oczywiste czytanie „mechanizmu okresowej aktualizacji" to: *odpalaj scraper co jakiś
czas, żeby raport był świeży*. To spełnia literę wymogu i jest nudne.

Czytanie wartościowe dla nadzorcy: **wykrywaj, KIEDY reklama się zmienia.**

Nadzorcy rynku nie interesuje to, że reklama istnieje — to widzi sam. Interesuje go
**zdarzenie**: że reklamodawca usunął ostrzeżenie o ryzyku, że podmienił treść po
kontroli, że ta sama kampania wraca pod nowym wariantem, że materiał zniknął.
Pojedynczy przebieg scrapera tego nie widzi. Widzi to dopiero **porównanie przebiegów**.

I to jest po naszej stronie tanie, bo infrastruktura już istnieje:
`simhash`, `embedding` (bge-m3, cosine), oraz `rule_results` zapisywane w całości.

**Przykład, który chcemy pokazać jury:**

```
Reklama 912810501476495 (Virtune Staked Solana ETP)
  21.11 14:03  ostrzezenie o ryzyku OBECNE (regula 6: pass)
  22.11 03:17  OSTRZEZENIE USUNIETE      (regula 6: pass -> fail)
               ryzyko: low -> high
               zmiana tekstu: simhash 7 bitow, cosine 0.961 (ten sam material)
```

Jedno zdanie, które mówi nadzorcy dokładnie to, czego nie dowiedziałby się sam.

## 3. Architektura

```
  rq-scheduler (orchestrator)          schedule.yaml
        │                              deklaratywnie: zrodlo × fraza × interwal
        │ co interwal
        ▼
   q:ingest  ──> scraper (A): discover + fetch  ──> AdDocument + det_results
        │                                                   │
        │                                            POST /documents
        │                                                   │
        ▼                                                   ▼
   q:gpu (n=1) ──> analyzer (B): analyze() ──> Finding ──> api (C)
        │                                                   │
        └──> DETEKTOR ZMIAN: porownanie z poprzednim ──> ChangeEvent
```

**Dlaczego `rq-scheduler`, a nie systemowy cron:** cron systemowy jest poza
aplikacją, nie widzi stanu kolejki i potrafi nawarstwić zadania, gdy poprzedni
przebieg jeszcze trwa. `rq-scheduler` dokłada harmonogram do kolejki, której już
używamy, respektuje przeciążenie (`q:gpu` ma jeden worker, więc harmonogram nie
zdoła zalać modelu) i daje się podejrzeć z kodu. Specyfikacja dopuszcza oba —
wybieramy orkiestrator.

## 4. Deklaratywny harmonogram

`services/analyzer/analyzer/config/schedule.yaml`:

```yaml
jobs:
  - name: fb-inwestycje
    source: facebook
    query: "inwestycje"
    interval_minutes: 30
    max_items: 10
    enabled: true

  - name: fb-sygnaly
    source: facebook
    query: "sygnaly inwestycyjne"
    interval_minutes: 60
    max_items: 10
    enabled: true

  - name: recheck-znane
    kind: recheck          # ponowne sprawdzenie JUZ ZNANYCH reklam
    interval_minutes: 15
    max_items: 20
    enabled: true
```

Zadanie typu `recheck` jest sercem wykrywania zmian: bierze najdawniej sprawdzone
znane URL-e i wysyła je do ponownego pobrania.

## 5. Typy zdarzeń

Każde zdarzenie to wiersz, który dashboard pokazuje jako **os czasu reklamy**.

| Zdarzenie | Warunek | Dlaczego istotne dla nadzorcy |
|---|---|---|
| `OSTRZEZENIE_USUNIETE` | reguła 3, 6 albo 14 przeszła `pass` → `fail` | Najmocniejszy sygnał. Reklamodawca pogorszył informację o ryzyku. |
| `OSTRZEZENIE_DODANE` | ta sama reguła `fail` → `pass` | Dowód naprawy; pozwala zamknąć sprawę. |
| `ESKALACJA_RYZYKA` | `risk_level` wzrósł | Priorytetyzacja kolejki nadzorczej. |
| `NOWY_WARIANT_KAMPANII` | cosine ≥ 0,88, simhash różny | Ta sama kampania przeredagowana — zwijamy w jeden wiersz z licznikiem. |
| `TRESC_ZMIENIONA` | simhash różni się > próg, cosine < 0,88 | Istotna zmiana treści, wymaga ponownej oceny ręcznej. |
| `REKLAMA_ZNIKNELA` | pobranie zwraca 404 / brak kreacji | Zapisujemy `last_seen`; materiał mógł zostać wycofany. |
| `BEZ_ZMIAN` | simhash identyczny | Nie tworzymy nowego `Finding`, tylko podbijamy `last_seen`. |

## 6. Idempotencja — warunek, żeby to nie było śmietnikiem

Bez tego harmonogram po dwóch godzinach wyprodukuje dwadzieścia identycznych
`Finding` na tę samą reklamę i raport stanie się bezużyteczny.

Zasada: **nowy `Finding` powstaje tylko wtedy, gdy coś się zmieniło.**

```
pobierz dokument
  ├─ simhash identyczny z poprzednim  -> podbij last_seen, KONIEC (brak Findingu)
  ├─ simhash rozny, cosine >= 0.95    -> duplikat, podbij last_seen + licznik
  ├─ cosine >= 0.88                   -> NOWY_WARIANT_KAMPANII, Finding + zdarzenie
  └─ inaczej                          -> pelna analiza, Finding + diff regul
```

Dzięki temu `q:gpu` nie marnuje 23 sekund na materiał, który się nie zmienił — co
przy jednym workerze GPU jest różnicą między działającym a zakorkowanym systemem.

## 7. Odporność na blokady źródła

Meta blokuje agresywne odpytywanie, a sala hackathonowa to nieprzewidywalna sieć.

- **Backoff wykładniczy** na poziomie zadania: 1, 2, 4, 8 minut, maks. 3 próby.
- **Wyłącznik bezpieczeństwa:** po 3 nieudanych przebiegach z rzędu zadanie przechodzi
  w stan `paused` z zapisanym powodem i **nie jest ponawiane**, dopóki człowiek go nie
  wznowi. To jednocześnie kwestia techniczna i przyzwoitości wobec Meta — nie dobijamy
  serwisu, który nas odrzucił.
- Stan zadań w Valkeyu, widoczny w `/schedule`.

## 8. Obserwowalność

Rozszerzamy istniejący endpoint o `/schedule`:

```json
{
  "jobs": [
    {"name": "fb-inwestycje", "state": "ok", "last_run": "...",
     "next_run": "...", "found": 6, "new_findings": 2, "events": 1},
    {"name": "fb-sygnaly", "state": "paused",
     "reason": "3 nieudane przebiegi: brak kreacji w widoku ?id=", "last_run": "..."}
  ]
}
```

To jest też materiał na slajd: harmonogram, który **jawnie przyznaje się do porażki
źródła**, wygląda poważniej niż taki, który milczy.

## 9. Podział pracy

| Element | Kto |
|---|---|
`schedule.yaml` + loader | B
Orkiestrator na `rq-scheduler` | B
Detektor zmian (diff `rule_results`, simhash, cosine) | B
Kontrakt `ChangeEvent` | B, do kontraktów
Backoff i wyłącznik bezpieczeństwa | B
`/schedule` | B
Funkcja `discover`/`fetch` wołana z zadania | A (istnieje)
Tabela `change_events` + os czasu w UI | C

## 10. Kontrakt `ChangeEvent` (propozycja do zamrożenia)

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "ad_archive_id": "912810501476495",
  "kind": "OSTRZEZENIE_USUNIETE",
  "detected_at": "2026-11-22T03:17:00Z",
  "previous_finding_id": "uuid",
  "current_finding_id": "uuid",
  "rule_diff": [
    {"rule_id": "6", "from": "pass", "to": "fail"}
  ],
  "similarity": {"simhash_distance": 7, "cosine": 0.961},
  "risk_level_from": "low",
  "risk_level_to": "high",
  "summary": "Ostrzezenie o ryzyku zostalo usuniete z tresci glownej reklamy."
}
```

`summary` jest zdaniem po polsku, pokazywanym nadzorcy — ta sama zasada co
`routing.reason`.

## 11. Kolejność wdrożenia

Tak, żeby po każdym kroku było co pokazać:

1. `schedule.yaml` + loader + `/schedule` zwracające stan z konfiguracji (bez pętli).
2. Detektor zmian jako **czysta funkcja** `diff_findings(poprzedni, aktualny)`
   plus kontrakt `ChangeEvent`. Testowalne bez kolejki i bez modelu.
3. Idempotencja: brama „czy się zmieniło" przed wejściem na `q:gpu`.
4. Orkiestrator `rq-scheduler` spinający to w pętlę.
5. Backoff i wyłącznik bezpieczeństwa.
6. Scenariusz demo: korpus w dwóch wersjach — jedna z ostrzeżeniem, druga bez —
   żeby `OSTRZEZENIE_USUNIETE` dało się pokazać **offline i deterministycznie**,
   bez czekania, aż reklamodawca naprawdę coś zmieni.

Punkt 6 jest nieoczywisty i ważny: bez przygotowanej pary wersji nie da się pokazać
wykrywania zmian na demie, bo nie zdążymy zaobserwować prawdziwej zmiany w ciągu
kilkunastu godzin.

## 12. Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Harmonogram zakorkuje `q:gpu` | Brama idempotencji przed kolejką GPU; bez zmiany nie ma analizy |
| Meta zablokuje po serii zapytań | Backoff + wyłącznik bezpieczeństwa; interwały ≥ 15 min |
| Nie zaobserwujemy prawdziwej zmiany przed demem | Para wersji w korpusie demo (punkt 11.6) |
| `rq-scheduler` wymaga `rq>=2` | Wersje wyrównane: oba serwisy na `rq==2.9.1` |
| Zdarzenia zasypią dashboard | `BEZ_ZMIAN` nie tworzy zdarzenia ani `Findingu` |
