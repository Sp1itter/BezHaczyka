# Demo INVESTWATCH

Szuka maksymalnie 5 filmów z **konkretną firmą, agentem lub domeną ze słownika oraz sygnałem promocji w pobliskim tekście**. Samo „inwestowanie”, „ETF”, nazwa firmy bez promocji czy dowolny link nie wystarczą. To selekcja materiałów do sprawdzenia pod kątem scamu, nie automatyczny werdykt.

Przykładowy filtr wymaga afiliacji, sponsoringu, kodu/bonusu lub obietnicy zysku. Samo „otwórz konto” jest za słabe i nie kwalifikuje filmu. Film edukacyjny zawierający konkretny segment promocyjny może zostać zwrócony — do analizy trafia fragment promocji, nie cały poradnik.

```powershell
python -m pip install -r requirements.txt
python demo.py --limit 5
```

Polecenia uruchamiaj w `services/scraper/youtube`, najlepiej we własnym środowisku wirtualnym. Ten scraper działa obok Facebookowego; nie wymaga Playwrighta ani brokera. Integracja ze wspólnymi kontraktami i kolejkami jest odłożona.

**Wejście i wyjście:** domyślnie wejście to `DEFAULT_CONFIG` i `DEFAULT_DICTIONARY` w `demo.py`. Pliki JSON pozostają alternatywą, wybieraną przez `--config`.

```powershell
python demo.py --limit 5 --stdout
python demo.py --config config.json --output wynik.json
python demo.py --config config.json --stdout
```

`--stdout` wypisuje wyłącznie JSON i nie zapisuje pliku. Postęp trafia na stderr. Bez tej flagi zapisujemy `wynik.json` (albo ścieżkę z konfiguracji/`--output`). Flagi `--stdout` i `--output` są rozłączne.

Wywołanie z programu, bez plików, w tle:

```python
import json
from copy import deepcopy
from demo import DEFAULT_CONFIG, DEFAULT_DICTIONARY, start_background

config = deepcopy(DEFAULT_CONFIG)
config['limit'] = 5
config['exclude']['title'] = ['poradnik']
job = start_background(config, DEFAULT_DICTIONARY, as_json=True)
# Program może teraz robić inne rzeczy; job.done() sprawdza zakończenie.
videos = json.loads(job.result())  # blokuje dopiero tutaj, do zakończenia skanu
```

`scan(config, dictionary, as_json=True)` robi to samo synchronicznie. Bez `as_json` otrzymujesz gotową listę Pythona. Opcjonalne `output_path="wynik.json"` dodatkowo zapisuje plik. Wejście jest kopiowane; zmiany konfiguracji po starcie nie zmienią działającego zadania. Błędy zadania są zgłaszane przez `job.result()`. To wątek wewnątrz programu, nie niezależna usługa; proces musi pozostać uruchomiony. Wątek nie jest daemonem, więc normalne zakończenie Pythona poczeka na jego pracę.

**Alternatywne wejście plikowe (`--config config.json`):**

Filtry wykluczające ustawisz w `config.json`, np. `"exclude": {"title": ["poradnik", "kryptowaluty"], "description": [], "transcript": []}`. Trafienie dowolnej frazy w wskazanym polu usuwa cały film z wyniku, także jeśli zawiera promocję. Wielkość liter i odstępy są normalizowane; dopasowanie respektuje granice słów, bez odmiany wyrazów. Puste listy niczego nie wykluczają. Brak transkrypcji oznacza, że jej wykluczeń nie da się sprawdzić. Uważaj na szerokie frazy w transkrypcji — wystarczy pojedyncza wzmianka, żeby odrzucić cały materiał.

- `config.json`: język `pl`, zapytania, sygnały promocji, `limit`, `max_candidates` i `results_per_query`. Ogólne hasła są usunięte. `max_comments: 10` domyślnie przegląda pierwsze 10 wpisów zwróconych przez yt-dlp (sortowanie `top`, łącznie z odpowiedziami). `0` wyłącza pobieranie. Eksportuje pełne komentarze autora filmu z tej puli, także bez trafień słownika; zgodność po ID kanału. Nie gwarantuje odnalezienia wszystkich odpowiedzi autora.
- `dictionary.json`: konkretne firmy (`organization`), osoby/agenci (`agent`) i domeny (`domain`). Aliasy opcjonalne. Przykład zawiera XTB i DM BOŚ z odnośnikami do wykazu KNF — **nie jest to lista podejrzanych firm**. Wstaw własne podmioty/domeny i dostosuj zapytania. Nie dopisujemy fikcyjnych agentów do demo live.

`wynik.json` to zwykła lista: URL, tytuł, kanał, język, pełny `description`, pełne `author_comments`, krótkie dowody tekstowe i `clips`. Bez hashy, pełnych transkrypcji i rozbudowanego kontraktu. Komentarze innych osób nie są eksportowane. Pusta lista komentarzy autora nie dowodzi, że autor nigdy nie komentował — sprawdzana jest tylko ograniczona pula.

Każdy `clip` ma `start`/`end` w sekundach, tekst, konkretne cele ze słownika, sygnały promocji i link do momentu filmu. Maksymalnie **2 fragmenty po 30 sekund**; bez scalania kolejnych trafień w cały film. W jednym fragmencie muszą wystąpić zarówno konkretny cel, jak i sygnał promocji. Niepotrzebne segmenty z początku są usuwane; wokół trafienia pozostaje tylko krótki kontekst. Czasy pochodzą z napisów, nie są precyzyjnymi granicami słów.

Trafienie w opisie/tytule/komentarzu może zostać bez klipu: `clips: []` i krótka informacja o braku timestampu. Linkowi z opisu nie przypisujemy wymyślonego czasu. Materiały bez dostatecznych przesłanek wybranego języka są pomijane; język sprawdzamy lokalnie w próbkach z całej transkrypcji, a przy jej braku w metadanych. To heurystyka, nie ustalenie kraju widowni.

Limit oznacza **do 5**, nie dopisywanie słabych wyników dla zapełnienia listy. Film znaleziony kilka razy jest sprawdzany raz w danym uruchomieniu. Brak trwałego cache. Wywołania są sekwencyjne; bez mediów, ASR, AI, bazy, serwisów i Dockera. Proxy/User-Agent opcjonalnie przez `INVESTWATCH_PROXY`/`INVESTWATCH_USER_AGENT` w środowisku.

Testy offline: `python -m unittest -v` z tego katalogu lub `python -m unittest discover -s services/scraper/youtube -p test_demo.py -v` z katalogu głównego repozytorium.
