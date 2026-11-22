# Obraz serwisu scraper: worker RQ (q:ingest, q:render) i scheduler (ten sam obraz, inna komenda).
#
# Kontekst budowania to katalog services/ (potrzebny pakiet casedb obok scrapera):
#   docker build -f scraper/Dockerfile -t investwatch-scraper services/
# (w docker-compose: build.context ../services, dockerfile scraper/Dockerfile)
#
# Tag bazowy MUSI odpowiadac wersji playwright w requirements.txt (1.65.2): przegladarki
# w obrazie sa zbudowane pod ta wersje biblioteki. Obraz zawiera Chromium i zaleznosci systemowe.
FROM mcr.microsoft.com/playwright/python:v1.65.2-noble

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1

# ffmpeg: konwersja/probkowanie mediow (media.py). --no-install-recommends i czyszczenie
# indeksu apt ograniczaja rozmiar warstwy.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Obraz jest jednozadaniowy, wiec zaleznosci ida do Pythona systemowego (PIP_BREAK_SYSTEM_PACKAGES:
# Ubuntu noble oznacza go jako "externally managed"; obraz Playwrighta nie ma python3-venv).
# Zaleznosci jako osobna warstwa: zmiana kodu nie wymusza ponownej instalacji.
COPY scraper/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Wspolna warstwa danych (pakiet casedb) z kontekstu services/.
COPY casedb /tmp/casedb
RUN pip install /tmp/casedb && rm -rf /tmp/casedb /tmp/requirements.txt

# Sciezka kodu ma znaczenie: sources/facebook.py liczy domyslny korpus offline wzgledem
# katalogu repo (parents[3]/fixtures/demo-ads/facebook), wiec kod laduje w <repo>/services/scraper.
# Korpus montuje compose (volume ../fixtures/demo-ads), FB_FIXTURES_DIR wskazuje go jawnie.
WORKDIR /opt/iw/services/scraper
COPY scraper/contracts.py scraper/jobs.py scraper/media.py scraper/net.py scraper/resolver.py \
     scraper/scheduler.py scraper/schedule.yaml scraper/state.py scraper/storage.py scraper/worker.py \
     scraper/worker_main.py scraper/scheduler_main.py ./
COPY scraper/sources/ ./sources/
COPY scraper/render/ ./render/
# rules_det: reguly DET 4-8 liczone przed wyslaniem do analyzera (jobs._enqueue_analysis).
# Bez tej linii kazdy nowy/zmieniony przypadek konczyl sie ModuleNotFoundError i nie trafial do q:gpu.
COPY scraper/rules_det/ ./rules_det/
# reresolve: ponowne rozwiazanie przypadkow po zmianie resolvera/rejestru (python tools/reresolve.py).
COPY scraper/tools/reresolve.py scraper/tools/bench_render.py scraper/tools/requalify.py \
     scraper/tools/seen_cleanup.py scraper/tools/measure_ingest.py ./tools/

# Uzytkownik nie-root (pwuser z obrazu Playwrighta); katalog roboczy na dane lokalne trybu bez S3.
RUN mkdir -p /opt/iw/services/scraper/data && chown -R pwuser:pwuser /opt/iw/services/scraper/data
USER pwuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "worker.py", "--ping"]

CMD ["python", "worker.py"]
