# Integracja serwisów — kto wywołuje kogo

Dokument dla **całego zespołu**. Doprecyzowuje §6.5 design doca.
Jeśli coś tu się zmieni, trzeba ogłosić całej trójce.

## Kształt przepływu

```
  scraper (A)                 Valkey                 analyzer (B)              api (C)
      │                          │                        │                       │
      │ 1. zapis AdDocument      │                        │                       │
      ├──────────────── POST /documents ─────────────────────────────────────────>│
      │                          │                        │                       │
      │ 2. enqueue zadania       │                        │                       │
      ├─────────────────────────>│                        │                       │
      │                       q:gpu (n=1)                 │                       │
      │                          ├───── 3. pobranie ─────>│                       │
      │                          │                        │ 4. analiza            │
      │                          │                        │    (scope → router    │
      │                          │                        │     → reguły → score) │
      │                          │                        │                       │
      │                          │                        │ 5. POST /findings     │
      │                          │                        ├──────────────────────>│
      │                          │                        │                       │ 6. zapis
      │                          │                        │                       │    + WebSocket
```

## Dlaczego kolejka, a nie endpoint HTTP u analyzera

Pytanie padło wprost, więc odpowiedź na piśmie. Analyzer **nie jest** serwisem
żądanie-odpowiedź. Trzy powody, z których pierwszy jest rozstrzygający:

1. **Ochrona VRAM.** Mamy 8 GB i jeden worker na `q:gpu` — to nasza gwarancja,
   że Bielik i Whisper nigdy nie walczą o pamięć. Synchroniczny endpoint HTTP
   pozwoliłby N równoległym żądaniom uderzyć w model naraz i reaktywowałby
   dokładnie ten konflikt, przed którym się zabezpieczyliśmy.
2. **Czas inferencji.** Jedno wywołanie wsadowe Bielika to sekundy do
   dziesiątek sekund, a na dokument idą 4 takie wywołania plus ewentualnie
   transkrypcja. Scraper nie może na to czekać, a HTTP by się rozłączył.
3. **Ponowienia i przeciążenie** dostajemy z kolejki za darmo. Padnięty worker
   nie gubi zadania.

## Co A wrzuca do kolejki

Zadanie jest **minimalne** — sam identyfikator. Treść analyzer czyta z API,
żeby nie dublować dużych obiektów w Valkey.

```json
{
  "document_id": "11111111-1111-4111-8111-111111111111",
  "enqueued_at": "2026-11-21T14:03:05Z",
  "entity_resolution": {
    "publisher_relation": "third_party",
    "publisher_is_authorized": false,
    "mentions_authorized_firm": true,
    "publisher_name": "@finfluencer_pl",
    "firm_name_in_ad": "XYZ Dom Maklerski",
    "registry_knf_id": "DM-123",
    "registry_official_name": "XYZ DM S.A.",
    "registry_score": 0.94,
    "disclosure_found": false,
    "affiliate_link": "https://xyz.pl/?ref=finflu123"
  }
}
```

**`entity_resolution` liczy osoba A**, nie my. To wynik fuzzy matchingu do
rejestru KNF. My go tylko konsumujemy — dzięki temu logika dopasowania jest
w jednym miejscu, a nasz potok testuje się bez rejestru.

Pole jest **opcjonalne**: jeśli A jeszcze go nie produkuje, analyzer przyjmuje
wartości domyślne (`relation: unknown`, `is_authorized: false`) i dokument
trafia do `triage` (reguła R4). Nic się nie wywraca — po prostu routing jest
mniej precyzyjny. Dzięki temu **GATE 1 o 15:00 nie zależy od gotowości rejestru**.

Kolejka: `q:gpu`, nazwa zadania `analyze_document`.

## Co analyzer zwraca do API

`POST /findings` z obiektem `Finding` dokładnie w kształcie
`fixtures/contract-examples/finding.json`. Nic więcej.

Dla C istotne trzy rzeczy:

- **`rule_results` zapisz w całości jako `JSONB`.** Na tym stoi panel
  kalibracji: front przelicza flagi przy przesuwaniu suwaka **bez** requestu
  do modelu. Jeśli to okroisz, suwak przestanie być natychmiastowy.
- **`risk_level == "high"` to sygnał do broadcastu WebSocket.** Progi liczy
  analyzer, API ich nie przelicza.
- **`routing.reason` pokaż w UI.** To zdanie po polsku wyjaśniające, dlaczego
  dokument trafił do danego modułu. Nadzorca musi móc tę decyzję zakwestionować.

## Dodatkowo u analyzera: `/health`

Jedyny endpoint HTTP, jaki wystawiamy. Do healthchecka w `docker-compose`
i do pokazania stanu modelu w panelu kalibracji.

```json
{
  "status": "ok",
  "ollama": true,
  "models": ["SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0", "bge-m3"],
  "profile": "gpu8"
}
```

Gdy `ollama: false`, analyzer **nadal działa**: reguły LLM zwracają
`not_applicable` z powodem, a reguły DET od A liczą się normalnie. Demo nie
pada, tylko traci część ocen — i jawnie to pokazuje.

## Zasada wspólna: brak danych nie jest naruszeniem

Dotyczy wszystkich trzech serwisów i jest najważniejszą regułą tego projektu.

Gdy czegoś nie dało się ocenić — model padł, tło jest graficzne, brakuje
`RenderProbe` — wynikiem jest `not_applicable` **z powodem**, nigdy `fail`.
Narzędzie nadzorcze, które zgłasza fałszywe naruszenia, jest gorsze niż
narzędzie, które przyznaje się do niewiedzy. `coverage()` w `scoring.py`
pokazuje, jaki odsetek reguł udało się ocenić — wyświetlajcie to obok score'u.
