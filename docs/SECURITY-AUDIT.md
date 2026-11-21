# Skan zależności

Narzędzie: `pip-audit 2.10.1` (baza podatności PyPA/OSV). Ponowny skan: `sh tools/audit.sh`.
Wersje wszystkich zależności są przypięte `==`. Sekrety są tylko w `infra/.env`, który jest w `.gitignore`.
`tools/check_compliance.py` pilnuje braku sekretów, zewnętrznych API modeli i licencji AGPL/SSPL.

| Data | Zakres | Wynik |
|---|---|---|
| 2026-11-21 | `requirements.txt` serwisów analyzer, casedb, scraper (zależności bezpośrednie) | brak znanych podatności |
| 2026-11-21 | pełne środowiska obrazów `analyzer` (43 pakiety), `scraper` (44), `casedb` (4), z `pip freeze` | brak znanych podatności |
