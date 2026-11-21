## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## casedb (wspolna baza przypadkow)

Znacznik: `casedb-handoff v1`. Przed praca nad modulem jobow, orkiestracja albo baza
przypadkow przeczytaj `services/casedb/AGENTS.md` (kontrakt, API dla jobow, stan testow).
Instrukcja dla czlowieka: `services/casedb/README.md`.

## Docker (instrukcja dla czatów)

Po `git pull` albo własnej zmianie w `services/<x>` uruchom komendę z tabeli (z katalogu `infra/`):

| Zmieniło się | Komenda |
|---|---|
| `services/<x>/**` | `docker compose up -d --build <x>` (scraper = `scraper-worker scheduler`) |
| zmiana resolvera / rejestru KNF | `docker compose exec scraper-worker python tools/reresolve.py` (przelicza `cases.entity_resolution`) |
| `infra/docker-compose.yml` | `docker compose up -d --build --remove-orphans` |
| `infra/.env.example` | dopisz nowe zmienne do `.env`, potem `docker compose up -d` |
| `infra/init.sql` | `docker compose down -v`, potem `docker compose up -d --build` (**UWAGA: kasuje dane**, NIGDY bez zgody człowieka) |
| `services/casedb/casedb/migrations/**` | `docker compose up -d --build casedb` (migracje przyrostowe, dane zostają) |
| nie wiesz | `docker compose up -d --build` |

- Potem `docker compose ps`: wszystkie długotrwałe serwisy `running`/`healthy`.
- Błąd: `docker compose logs --tail 100 <serwis>`.
- NIGDY `down -v` bez zgody człowieka (kasuje bazę).
- W Git Bash przed komendami ze ścieżkami `/data/...` ustaw `MSYS_NO_PATHCONV=1`.
