# Handoff: FacebookAdsSource → osoba B (analyzer) i osoba C (API/UI)

Stan na 21.11.2026, branch `feat/facebook-ads-source`.

## Pliki

| Co | Ścieżka |
|---|---|
| Złoty `AdDocument` z prawdziwego nagrania (replay, nie atrapa) | `fixtures/contract-examples/facebook_ad_document.json`: **lokalnie, NIE w gicie** (patrz „Otwarte”); odtworzysz go komendą `tools/gen_facebook_examples.py` |
| `RuleResult` dla reguł 4–8 tego dokumentu (§6.3) | `fixtures/contract-examples/rule_result_facebook.json` |
| Korpus offline (zamrożone snapshoty) | `fixtures/demo-ads/facebook/<ad_archive_id>/page.html` (+ `node.json.gz`) |
| Generator obu JSON-ów | `services/scraper/tools/gen_facebook_examples.py` |
| Reguły 4–8 dla źródła facebook | `services/scraper/sources/facebook_rules.py` → `facebook_det_results(doc)` |

## Dla osoby B (analyzer)

- `source == "facebook"`: **R4, R5 i R8 mają `not_applicable`** z powodem „typografia platformy (Meta Ad Library)”. Tekst w DOM Ad Library składa Meta, nie reklamodawca. Te reguły **nie wchodzą do mianownika** scoringu §9. `analyzer/scoring.py::risk_score` już pomija `not_applicable`, więc nic nie trzeba zmieniać.
- **R7** przy FB ma `engine: "HYBRID"`, gdy ostrzeżenie leży w treści głównej:
  - `risk_offset_chars > 125` (za progiem „Zobacz więcej” w feedzie) daje `fail` z `confidence: 0.6`, bo to heurystyka feedu, a nie pomiar;
  - ostrzeżenie w pierwszych 125 znakach daje `pass`;
  - `behind_interaction != null` na węźle z ostrzeżeniem daje twardy DET `fail`.
- **R6 i R7 mają `not_applicable`, gdy w treści nie ma żadnego ostrzeżenia.** Brak ostrzeżenia ocenia reguła 3 (HYBRID, po Twojej stronie), a nie reguły położenia.
- **`text` zaczyna się od treści głównej reklamy.** Dalej są tytuły, opisy, karty DCO i na końcu rozwinięte linki docelowe z `utm_*`/`ref`/`aff`, przydatne w Module 3.
- **`publisher.is_official_firm_channel` jest zawsze `false`.** Nadpisuje go Twój resolver KNF.
- **`simhash`, `embedding`, `transcript` i `scope` są `null`/domyślne.** Liczy je analyzer (§6.5).
- **`media[]`** zawiera mp4 (`s3://media/<id>.mp4`, `duration_s` z ffprobe), gdy reklama ma wideo. To wejście dla faster-whisper.

Smoke test jednej reklamy offline (bez sieci):

```bash
cd services/scraper
FB_MODE=replay .venv/Scripts/python.exe -c "from sources.facebook import FacebookAdsSource; from sources.meta_json import canonical_ad_url; d=FacebookAdsSource().fetch(canonical_ad_url('<ad_archive_id>')); print(d.model_dump_json(indent=1)[:1500])"
.venv/Scripts/python.exe tools/gen_facebook_examples.py   # odświeża oba JSON-y w contract-examples
```

## Dla osoby C (API/UI)

Pola gotowe do wyświetlenia:
- `publisher.display_name` i `publisher.handle` (np. `@skarbiecpl`), link w `publisher.profile_url`;
- `url`, czyli kanoniczny `…/ads/library/?id=<ad_archive_id>`, do otwarcia w nowej karcie;
- `text`: pierwsza linia to treść główna, linki są na końcu;
- `screenshots.desktop` (`s3://shots/<id>-1920.png`) i `screenshots.mobile` (`-390.png`). Tabletu w JSON nie ma, zgodnie z kontraktem;
- skrót `render_probe`: dla FB pokazuj tylko `render_probe.viewports.desktop.nodes[].text` (tekst kreacji). Geometria jest tu typografią Meta, stąd R4/5/8 `not_applicable`;
- `rule_results[].evidence.summary` jest po polsku i gotowe do pokazania nadzorcy.

## Korpus (nagrany 21.11.2026, Meta Ad Library, PL, aktywne)

| Fraza | Nagrane | Reklamy (`fixtures/demo-ads/facebook/<id>/`) |
|---|---|---|
| inwestycje | 6/6 | 912810501476495 (Virtune, krypto ETP, ostrzeżenie za progiem 125 zn.), 675484101807418 (wideo), 986443020999266 (wideo), 1685589429005115 (wideo), 1416188807395560, 28815441858041693 |
| sygnały inwestycyjne | 2/4 | 1700487841682444 (wideo), 1688659872622573 (wideo); 2 reklamy: „brak kreacji w widoku ?id=” |
| zarządzanie majątkiem | 0 | discover zwrócił 0 reklam, bez sygnału blokady |
| CFD | 0 | discover zwrócił 0 reklam, bez sygnału blokady |

W gicie są tylko `page.html` i `node.json.gz`, łącznie ok. 29 MB. Pliki `video.mp4` są w `.gitignore`: zostają lokalnie w tych samych katalogach i są potrzebne tylko do `media[]` w replay. Na innej maszynie replay da `media: []`.

## Otwarte

- **Złoty `AdDocument` nie jest w commicie.** `tools/check_compliance.py` zgłasza w nim 3 adresy: URL reklamy, profil i link docelowy reklamodawcy. To treść nagranego materiału, nie wywołania sieciowe, ale checker jej nie rozróżnia, a JSON nie przyjmuje markera `compliance:allow`. Decyzja należy do właściciela checkera (B).
- **`duration_s: null`**: lokalnie nie ma `ffprobe`. W kontenerze z ffmpeg zostanie wypełnione.
- **„Zarządzanie majątkiem” i „CFD” dały 0 reklam** w discover. Nie weryfikowałem, czy to faktyczny brak aktywnych reklam w PL, czy inny wariant strony wyników, bo nie chciałem dokładać ruchu do Meta.
