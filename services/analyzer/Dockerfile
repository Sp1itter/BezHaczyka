# Obraz serwisu analyzer (worker analizy reklam).
#
# Build z katalogu services/analyzer:  docker build -t investwatch-analyzer .

# Tag przypiety do konkretnej wersji poprawki (nie `latest`, nie sam `3.12`),
# zeby build byl powtarzalny i zgodny z wymogiem weryfikowalnego lancucha dostaw.
FROM python:3.12.7-slim-bookworm

# Zmienne srodowiskowe Pythona:
# - PYTHONUNBUFFERED=1: logi trafiaja od razu do `docker logs`, bez buforowania
#   na stdout (inaczej przy awarii ostatnie linie gina).
# - PYTHONDONTWRITEBYTECODE=1: nie generujemy plikow .pyc w kontenerze, bo
#   uzytkownik analyzer nie ma prawa zapisu do /app i bylyby to tylko zbedne proby zapisu.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg jest potrzebny do dekodowania audio przed speech-to-text (faster-whisper).
# --no-install-recommends ogranicza rozmiar obrazu, a rm -rf /var/lib/apt/lists
# usuwa indeks pakietow, ktory zostalby w warstwie i nie jest nam potrzebny w runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Uzytkownik NIE-root - wymog bezpieczenstwa ze specyfikacji konkursu.
# Staly UID/GID (10001) zamiast losowego, zeby latwo bylo to ograniczyc w
# orkiestracji (securityContext, wolumeny). Konto bez shella i bez hasla.
RUN groupadd --system --gid 10001 analyzer \
    && useradd --system --uid 10001 --gid analyzer --no-create-home \
        --shell /usr/sbin/nologin analyzer

WORKDIR /app

# Najpierw sama lista zaleznosci i instalacja pakietow. Warstwa z pip install
# zostaje w cache Dockera tak dlugo, jak dlugo nie zmieni sie requirements.txt,
# wiec zmiana kodu nie wymusza ponownego pobierania ~kilkuset MB wheeli.
# Wersje w requirements.txt sa przypiete przez ==, wiec pip install jest powtarzalny.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kod aplikacji dopiero teraz - czesto sie zmienia, wiec jest na koncu.
# Kopiujemy tylko pakiet `analyzer`, a nie caly katalog: bez tego do obrazu
# trafilyby .venv, tests/ i tools/ (duzo balastu i potencjalnie wrazliwe pliki).
COPY analyzer/ ./analyzer/

# Od tego miejsca wszystko wykonuje sie jako uzytkownik analyzer.
USER analyzer

# Port, na ktorym ma odpowiadac endpoint /health (sonda zdrowia).
EXPOSE 8081

# Sonda zdrowia wola GET /health na porcie 8081. Obraz slim nie ma curl,
# wiec uzywamy stdlib (urllib). Kod wyjscia != 0 (wyjatek, np. polaczenie
# odrzucone albo HTTP 4xx/5xx) oznacza `unhealthy`.
# Worker (`python -m analyzer.worker`) uruchamia serwer /health w watku-demonie
# PRZED wejsciem w blokujaca petle kolejki — patrz worker.py::_start_health_server.
# Zgodnosci tego portu z health.HEALTH_PORT pilnuje test
# tests/test_spojnosc.py::TestPortHealth.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/health', timeout=3)"

# Domyslnie uruchamiamy worker kolejki. Wartosci (OLLAMA_BASE_URL, PROFILE itd.)
# przychodza z .env / docker-compose, nie z obrazu.
CMD ["python", "-m", "analyzer.worker"]
