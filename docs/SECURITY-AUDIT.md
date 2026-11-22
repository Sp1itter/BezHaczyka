# Skan zależności

Narzędzie: `pip-audit 2.10.1` (baza podatności PyPA/OSV). Ponowny skan: `sh tools/audit.sh`.
Wersje wszystkich zależności są przypięte `==`. Sekrety są tylko w `infra/.env`, który jest w `.gitignore`.
`tools/check_compliance.py` pilnuje braku sekretów, zewnętrznych API modeli i licencji AGPL/SSPL.

| Data | Zakres | Wynik |
|---|---|---|
| 2026-11-21 | `requirements.txt` serwisów analyzer, casedb, scraper (zależności bezpośrednie) | brak znanych podatności |
| 2026-11-21 | pełne środowiska obrazów `analyzer` (43 pakiety), `scraper` (44), `casedb` (4), z `pip freeze` | brak znanych podatności |

## services/web — npm audit (2026-11-22)

Narzędzie: `npm audit` (npm 11.12.0, Node v24.14.1), na kopii `package.json` i `package-lock.json` po `npm ci` (189 pakietów w drzewie). Baza: GitHub Advisory Database.

| Data | Polecenie | Wynik |
|---|---|---|
| 2026-11-22 | `npm audit --omit=dev` | 0 podatności (critical 0, high 0, moderate 0, low 0) |
| 2026-11-22 | `npm audit` (z devDependencies) | 0 podatności (critical 0, high 0, moderate 0, low 0) |

Poprawki nie są potrzebne; `package.json` bez zmian.

