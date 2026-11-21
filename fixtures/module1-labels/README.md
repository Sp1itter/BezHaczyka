# Zbiór z etykietami Modułu 1

40 przypadków z bazy demo (14 facebook, 23 youtube, 3 www) w `cases.jsonl`, po jednym obiekcie:
`case_id`, `source`, `url`, `publisher_*`, `title`, `text` (1500 znaków), `doc` (pełny AdDocument), `labels`.
Wybór: wszystkie facebook i www, youtube losowo (14 z dopasowaniem do rejestru, 9 bez).

## Rubryka etykiet

- `firm`: oficjalna nazwa firmy inwestycyjnej (wg nazw z rejestru), którą materiał reklamuje/promuje, albo `null`.
  Gdy wymieniono kilka firm, wpisano główną (pierwszą).
- `relation`: `official` gdy publikuje sama firma (nazwa strony/handle/domena profilu), `third_party` gdy publikuje
  ktoś inny o firmie, `unknown` gdy materiał nie dotyczy firmy inwestycyjnej.
- `disclosure`: `true` gdy tekst jawnie ujawnia współpracę/reklamę (#reklama/#hirdetés, „link partnerski”,
  „affiliate link”, „Współpraca Reklamowa”, „fizetett reklám”), także gdy dotyczy to produktu spoza finansów.
- `affiliate`: `true` gdy w tekście jest link z kodem/parametrem polecającym do firmy inwestycyjnej.
- `note`: jedno zdanie uzasadnienia.

## Uczciwość pomiaru

Etykiety nadano wyłącznie z treści (pola publikującego, tytuł, tekst), **przed** jakąkolwiek zmianą resolvera
i bez wglądu w jego logikę ani w `cases.entity_resolution`. Data: 2026-11-21, commit bazowy `22c851c`.
Nazwy firm w `firm` sprawdzono tylko względem tabeli `authorized_entities` (rejestr, nie wynik resolvera).
Przypadki graniczne: emitent ETP Virtune (nie jest w rejestrze).

Etykiety nadał subagent AI według rubryki, nie człowiek. Wzorce ujawnień EN/HU dopisano po obejrzeniu pominięć
na tym samym zbiorze, więc precyzja i czułość ujawnień na nim są „in-sample” i optymistyczne. Wyrywkowa kontrola
15 przypadków w bazie dała precyzję 14/15; jedno fałszywe trafienie to negacja „not sponsored by” (poprawione
w kolejnej poprawce: `sponsored` / `paid promotion` po zaprzeczeniu nie liczą się jako ujawnienie).

## Użycie

    python services/scraper/tools/eval_module1.py --db postgresql://... --out wynik.json

`baseline.json` to wynik „przed” (resolver w stanie bazowym).
