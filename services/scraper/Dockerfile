# Obraz scrapera: workery RQ (q:ingest, q:render) i harmonogram — ten sam obraz, rozne CMD.
FROM python:3.12.7-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Uklad jak w repo (services/scraper) — sources/facebook.py liczy fixtures przez parents[3] => /app/fixtures
WORKDIR /app/services/scraper

COPY requirements.txt .
# libatomic1 — node z playwrighta wymaga go w wariancie slim
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 \
    && pip install -r requirements.txt \
    && python -m playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright \
    && rm -rf /var/lib/apt/lists/*

# Caly kontekst (wyjatki w .dockerignore: tests, youtube, tools...)
COPY . .

# Uzytkownik bez shella, uid/gid 10003
RUN groupadd --gid 10003 scraper \
    && useradd --uid 10003 --gid 10003 --no-create-home --shell /usr/sbin/nologin scraper \
    && mkdir -p /app/services/scraper/data && chown scraper:scraper /app/services/scraper/data

USER scraper
CMD ["python", "worker_main.py", "q:ingest"]
