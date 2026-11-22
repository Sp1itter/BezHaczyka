# Audyt zależności — services/scraper

Data: 2026-11-22. Narzędzie: `pip-audit 2.10.1`, `python -m pip_audit -r services/scraper/requirements.txt`.

Wynik: **No known vulnerabilities found** (wszystkie wersje przypięte w `requirements.txt`,
w tym nowe: `ddgs 9.16.1`, `curl_cffi 0.17.0`, `trafilatura 2.3.1`).

Usunięte: `youtube-transcript-api` (napisy pobiera teraz yt-dlp; endpoint napisów i tak był blokowany).

Licencje nowych zależności: ddgs — MIT, curl_cffi — MIT, trafilatura — Apache-2.0.
