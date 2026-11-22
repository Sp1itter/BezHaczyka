# Licencje komponentów

Wszystkie komponenty InvestWatch są open source. System nie korzysta z płatnych API ani z zewnętrznych API modeli. Licencje AGPL i SSPL są zakazane; pilnuje tego `tools/check_compliance.py`.

Dane z dnia 2026-11-22. Licencje zależności bezpośrednich odczytano z metadanych zainstalowanych pakietów (świeże środowiska z `requirements.txt`, wersje przypięte; `pip-licenses 5.0.0` i bezpośredni odczyt `METADATA`) oraz z `package.json` pakietów w `node_modules` (`npm ci` z `package-lock.json`).

## Zależności bezpośrednie

### services/analyzer

| Pakiet | Wersja | Licencja |
|---|---|---|
| pydantic | 2.9.2 | MIT |
| httpx | 0.27.2 | BSD-3-Clause |
| PyYAML | 6.0.2 | MIT |
| faster-whisper | 1.0.3 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| huggingface_hub | 0.36.2 | Apache-2.0 |
| langdetect | 1.0.9 | Apache-2.0 (klasyfikator PyPI; pole License w metadanych podaje MIT, upstream: Apache-2.0) |
| rq | 2.9.1 | BSD-2-Clause |
| redis | 8.1.0 | MIT |
| rq-scheduler | 0.14 | MIT |
| psycopg | 3.3.9 | LGPL-3.0-only |
| docker | 7.1.0 | Apache-2.0 |

### services/api

| Pakiet | Wersja | Licencja |
|---|---|---|
| fastapi | 0.115.5 | MIT |
| uvicorn | 0.32.1 | BSD-3-Clause |
| websockets | 13.1 | BSD-3-Clause |
| pydantic | 2.9.2 | MIT |
| psycopg | 3.3.9 | LGPL-3.0-only |
| boto3 | 1.44.9 | Apache-2.0 |

### services/casedb

| Pakiet | Wersja | Licencja |
|---|---|---|
| psycopg | 3.3.9 | LGPL-3.0-only |

### services/scraper

| Pakiet | Wersja | Licencja |
|---|---|---|
| pydantic | 2.14.4 | MIT |
| playwright | 1.65.2 | Apache-2.0 |
| boto3 | 1.44.9 | Apache-2.0 |
| rq | 2.9.1 | BSD-2-Clause |
| redis | 8.1.0 | MIT |
| yt-dlp | 2026.10.26 | Unlicense |
| httpx | 0.28.1 | BSD-3-Clause |
| langdetect | 1.0.9 | Apache-2.0 (klasyfikator PyPI; pole License w metadanych podaje MIT, upstream: Apache-2.0) |
| requests | 2.34.2 | Apache-2.0 |
| rapidfuzz | 3.14.6 | MIT |
| rq-scheduler | 0.14 | MIT |
| PyYAML | 6.0.2 | MIT |
| ddgs | 9.16.1 | MIT |
| curl_cffi | 0.17.0 | MIT |
| trafilatura | 2.3.1 | Apache-2.0 |


### services/web (npm)

Zależności produkcyjne (`dependencies`):

| Pakiet | Wersja | Licencja |
|---|---|---|
| react | 18.3.1 | MIT |
| react-dom | 18.3.1 | MIT |
| recharts | 2.13.3 | MIT |

Zależności deweloperskie (`devDependencies`, tylko build):

| Pakiet | Wersja | Licencja |
|---|---|---|
| @vitejs/plugin-react | 4.3.4 | MIT |
| vite | 6.4.6 | MIT |

## Modele

| Model | Licencja | Źródło weryfikacji |
|---|---|---|
| Bielik 4.5B v3.0 Instruct (SpeakLeash) | Apache-2.0 | karta modelu Hugging Face `speakleash/Bielik-4.5B-v3.0-Instruct`, tag `license:apache-2.0` |
| Bielik 1.5B v3.0 Instruct (SpeakLeash) | Apache-2.0 | karta modelu Hugging Face `speakleash/Bielik-1.5B-v3.0-Instruct`, tag `license:apache-2.0` |
| bge-m3 (BAAI) | MIT | karta modelu Hugging Face `BAAI/bge-m3`, tag `license:mit` |

Uruchamiane są kwantyzacje Q8_0 z biblioteki Ollama (`SpeakLeash/bielik-*-v3.0-instruct:Q8_0`); licencja kwantyzacji jest taka sama jak modelu bazowego (strona Ollama podaje Apache 2.0).

## Obrazy Docker

| Obraz (`infra/docker-compose.yml`, Dockerfile) | Licencja | Weryfikacja |
|---|---|---|
| `pgvector/pgvector:pg16` | PostgreSQL License (PostgreSQL), PostgreSQL License (pgvector) | zweryfikowano: nie. GitHub nie rozpoznaje pliku LICENSE pgvector (NOASSERTION); licencja według dokumentacji projektu |
| `valkey/valkey:8-alpine` | BSD-3-Clause | zweryfikowano w repozytorium upstream |
| `chrislusf/seaweedfs:3.68` | Apache-2.0 | zweryfikowano w repozytorium upstream |
| `nginx:1.27-alpine` | BSD-2-Clause | zweryfikowano w repozytorium upstream |
| `nginxinc/nginx-unprivileged:1.27.3-alpine` | Apache-2.0 (skrypty obrazu); nginx BSD-2-Clause | zweryfikowano w repozytorium upstream (obraz) |
| `ollama/ollama:0.40.17` | MIT | zweryfikowano w repozytorium upstream |
| `tecnativa/docker-socket-proxy:0.3.0` | Apache-2.0 | wrapper zweryfikowano w repozytorium upstream; obraz zawiera HAProxy (GPL-2.0, nie weryfikowano), uruchamiany jako osobny, niezmodyfikowany kontener |
| `mcr.microsoft.com/playwright/python:v1.65.2-noble` | Apache-2.0 (Playwright); Chromium: BSD-3-Clause i licencje składników | Playwright zweryfikowano; Chromium nie |
| `python:3.12*-slim`, `node:20.18.1-bookworm-slim` | PSF License, MIT; Debian: mieszane licencje (w tym GPL w narzędziach systemowych) | nie weryfikowano |

Obrazy bazowe zawierają pakiety systemowe na licencjach GPL/LGPL (Debian, Ubuntu); są uruchamiane jako osobne kontenery i nie są linkowane z kodem projektu.

## Podsumowanie

Zależności bezpośrednie: dominuje MIT, poza tym Apache-2.0, BSD-2/3-Clause i Unlicense (yt-dlp). W Pythonie jedyną licencją copyleft wśród zależności bezpośrednich jest LGPL-3.0 (psycopg). W web (5 pakietów) wszystkie MIT.

Copyleft i licencje słabe znalezione w pełnych środowiskach (także tranzytywnie):

- psycopg 3.3.9 (LGPL-3.0-only; services/analyzer, api, casedb): dołączony jako niezmodyfikowana biblioteka, importowana dynamicznie przez Python (wheel `psycopg[binary]`). Kod projektu nie jest modyfikacją biblioteki.
- python-crontab (`crontab` 1.0.5, LGPL-2.1; tranzytywnie przez rq-scheduler w analyzer i scraper): niezmodyfikowana, importowana dynamicznie.
- certifi (MPL-2.0; tranzytywnie): niezmodyfikowany; MPL dotyczy tylko plików samego pakietu.
- tqdm (MPL-2.0 AND MIT; tranzytywnie w analyzer): jak wyżej.
- caniuse-lite (CC-BY-4.0, dane; tranzytywnie w web, narzędzia build): wymaga atrybucji, nie jest kodem.

Nie znaleziono licencji AGPL, SSPL ani GPL wśród pakietów Pythona i npm. Wszystkie pakiety Pythona w środowiskach miały rozpoznawalną licencję (jeden pakiet, `langdetect`, ma sprzeczne metadane, patrz tabela). Nie znaleziono licencji nieznanych. W npm: 103 pakiety, licencje MIT 81, ISC 16, BSD-3-Clause 3, Apache-2.0 1, CC-BY-4.0 1 (dane caniuse-lite), MIT AND ISC 1.

Do ręcznej weryfikacji pozostają wpisy oznaczone w tabeli obrazów jako niezweryfikowane.
