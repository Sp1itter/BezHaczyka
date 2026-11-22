# Po pobraniu zmian z repozytorium

Komendy z katalogu `infra/`.

| Zmieniło się | Komenda |
|---|---|
| `services/<x>/**` | `docker compose up -d --build <x>` (scraper = `scraper-worker scheduler`) |
| `infra/docker-compose.yml` | `docker compose up -d --build --remove-orphans` |
| `infra/.env.example` | porównaj ze swoim `.env`, dopisz nowe zmienne, potem `docker compose up -d`. Ollama: w `.env` ustaw `OLLAMA_BASE_URL=http://ollama:11434` albo dopisz `COMPOSE_FILE=docker-compose.yml:docker-compose.native.yml` (Ollama natywna) / `COMPOSE_FILE=docker-compose.yml:docker-compose.cpu.yml` (bez NVIDIA). Maszyna bez GPU bez nakładki cpu nie uruchomi `ollama` |
| `services/casedb/casedb/migrations/**` | `docker compose up -d --build casedb` (migracje przyrostowe, dane zostają) |
| `infra/init.sql` | dotyczy tylko pustego wolumenu; schemat zmieniają migracje casedb, `down -v` niepotrzebne |
| nie wiesz | `docker compose up -d --build --remove-orphans` (przebuduje tylko zmienione) |

Praca nad UI z hot reload: `cd services/web && npm ci && npm run dev` (Vite :5173, API z Dockera :8000, CORS ustawiony).
