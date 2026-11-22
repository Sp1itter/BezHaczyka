# Dane demonstracyjne

Repozytorium startuje z pustą bazą. Tutaj są gotowe stany do wgrania, żeby zobaczyć system
z danymi bez czekania na zbieranie i analizę.

| Katalog | Co zawiera | Media w wydaniu `demo-2026-11-22` |
|---|---|---|
| `test-20min/` | 20 minut zbierania z internetu i pełna analiza, wyniki i przebieg: [POMIAR.md](test-20min/POMIAR.md) | `media-test-20min.tar` |
| `backup-przed-testem/` | stan z nocy 21/22.11 (wcześniejsze przebiegi) | `media-przed-testem.tar` |

`baza.dump` to zrzut PostgreSQL. Zrzuty reklam, strony i nagrania (`media.tar`) są ze względu
na rozmiar w wydaniu na GitHubie, nie w repozytorium.

## Wgranie stanu z testu

Przy działającym stosie (`cd infra && docker compose up -d`), z katalogu głównego repozytorium:

```
gh release download demo-2026-11-22 -p media-test-20min.tar -O demo/test-20min/media.tar --repo Sp1itter/BezHaczyka
bash tools/demo_snapshot.sh import demo/test-20min
```

Plik można też pobrać ręcznie ze strony Releases i zapisać jako `demo/test-20min/media.tar`.
Skrypt zatrzymuje zbieranie i analizę, nadpisuje bazę i pliki, a potem uruchamia panel
(http://localhost:7090). Powrót do normalnej pracy: `cd infra && docker compose up -d`.

Zapis własnego stanu: `bash tools/demo_snapshot.sh export demo/<nazwa>`.
