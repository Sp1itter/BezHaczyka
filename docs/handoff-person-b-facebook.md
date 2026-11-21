# Handoff FacebookAdsSource: osoba B (analyzer) i osoba C (API/UI)

Stan na 21.11.2026, branch `feat/facebook-ads-source`.

## Pliki

| Co | Ścieżka |
|---|---|
| Złoty `AdDocument` (przykład kontraktowy po sanityzacji) | `fixtures/contract-examples/facebook_ad_document.json` |
| Niesanityzowane źródło złotego dokumentu | `fixtures/demo-ads/facebook/912810501476495/` |
| `RuleResult` reguł 4–8 dla tej reklamy (§6.3) | `fixtures/contract-examples/rule_result_facebook.json` |
| Korpus offline | `fixtures/demo-ads/facebook/<ad_archive_id>/page.html` i `node.json.gz` |
| Generator obu JSON-ów | `services/scraper/tools/gen_facebook_examples.py` |
| Reguły 4–8 dla źródła facebook | `services/scraper/sources/facebook_rules.py`, funkcja `facebook_det_results(doc)` |

Złoty dokument powstaje z replayu reklamy 912810501476495 (Virtune). Generator zamienia host każdego adresu `http(s)` na `example.invalid` i zostawia ścieżkę oraz parametry, więc `url` ma postać `https://example.invalid/ads/library/?id=912810501476495`, a link w `text` zachowuje `utm_*`. Wymaga tego `tools/check_compliance.py`. Kształt i pozostałe wartości są takie jak w nagraniu. Ponowne uruchomienie generatora też zapisze wersję zsanityzowaną.

## Osoba B (analyzer)

- Przy `source == "facebook"` reguły R4, R5 i R8 mają `not_applicable` z powodem „typografia platformy (Meta Ad Library)”. Tekst w DOM Ad Library składa Meta, nie reklamodawca. Reguły `not_applicable` nie wchodzą do mianownika scoringu §9; `analyzer/scoring.py::risk_score` już je pomija.
- R7 dostaje `engine: "HYBRID"`, gdy ostrzeżenie stoi w treści głównej:
  - `risk_offset_chars > 125` (za progiem „Zobacz więcej” w feedzie) daje `fail` z `confidence: 0.6`, bo to heurystyka feedu;
  - ostrzeżenie w pierwszych 125 znakach daje `pass`;
  - węzeł z ostrzeżeniem i `behind_interaction != null` daje DET `fail` z `confidence: 1.0`.
- Bez żadnego ostrzeżenia w treści R6 i R7 mają `not_applicable`. Brak ostrzeżenia ocenia reguła 3 (HYBRID, po stronie analyzera).
- `text` zaczyna się od treści głównej reklamy. Po niej idą tytuły, opisy, karty DCO, a na końcu rozwinięte linki docelowe z `utm_*`, `ref` i `aff` dla Modułu 3.
- `publisher.is_official_firm_channel` ma zawsze wartość `false`. Nadpisuje ją resolver KNF w analyzerze.
- `simhash`, `embedding`, `transcript` i `scope` zostają `null` albo domyślne. Liczy je analyzer (§6.5).
- `media[]` zawiera mp4 (`s3://media/<id>.mp4`, `duration_s` z ffprobe), gdy reklama ma wideo. To wejście dla faster-whisper.

Smoke test jednej reklamy offline:

```bash
cd services/scraper
FB_MODE=replay .venv/Scripts/python.exe -c "from sources.facebook import FacebookAdsSource; from sources.meta_json import canonical_ad_url; d=FacebookAdsSource().fetch(canonical_ad_url('<ad_archive_id>')); print(d.model_dump_json(indent=1)[:1500])"
.venv/Scripts/python.exe tools/gen_facebook_examples.py   # odświeża oba JSON-y w contract-examples
```

## Osoba C (API/UI)

- `publisher.display_name` i `publisher.handle` (np. `@skarbiecpl`), link do profilu w `publisher.profile_url`.
- `url` to kanoniczny `…/ads/library/?id=<ad_archive_id>`; można go otworzyć w nowej karcie.
- W `text` pierwsza linia to treść główna, linki są na końcu.
- `screenshots.desktop` (`s3://shots/<id>-1920.png`) i `screenshots.mobile` (`-390.png`). Kontrakt nie przewiduje tabletu.
- Z `render_probe` dla FB wystarczy `render_probe.viewports.desktop.nodes[].text`, czyli tekst kreacji. Geometria pokazuje typografię Meta i dlatego R4, R5 i R8 mają `not_applicable`.
- `rule_results[].evidence.summary` jest po polsku i można je pokazać nadzorcy bez zmian.

## Korpus (nagrany 21.11.2026, Meta Ad Library, PL, reklamy aktywne)

| Fraza | Nagrane | Reklamy (`fixtures/demo-ads/facebook/<id>/`) |
|---|---|---|
| inwestycje | 6/6 | 912810501476495 (Virtune, krypto ETP, ostrzeżenie za progiem 125 znaków), 675484101807418 (wideo), 986443020999266 (wideo), 1685589429005115 (wideo), 1416188807395560, 28815441858041693 |
| sygnały inwestycyjne | 2/4 | 1700487841682444 (wideo), 1688659872622573 (wideo); dwie reklamy padły z błędem „brak kreacji w widoku ?id=” |
| zarządzanie majątkiem | 0 | discover zwrócił 0 reklam, bez sygnału blokady |
| CFD | 0 | discover zwrócił 0 reklam, bez sygnału blokady |

Git przechowuje tylko `page.html` i `node.json.gz`, razem ok. 29 MB. Pliki `video.mp4` są w `.gitignore` i leżą lokalnie w tych samych katalogach. Replay potrzebuje ich tylko do `media[]`, więc na innej maszynie zwróci `media: []`.

## Otwarte

- `duration_s` ma wartość `null`, bo lokalnie brakuje `ffprobe`. W kontenerze z ffmpeg pole się wypełni.
- Dla fraz „zarządzanie majątkiem” i „CFD” discover zwrócił 0 reklam. Nie sprawdziłem, czy w PL nie ma aktywnych reklam, czy Meta pokazała inny wariant strony wyników; kolejne zapytania obciążałyby Meta.
