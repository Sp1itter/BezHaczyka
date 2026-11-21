"""Automat sprawdzajacy zgodnosc z wymogami technicznymi specyfikacji UKNF.

Chodzi o REGULY KONKURSU (par. 5 opisu wyzwania), nie o 18 regul oceny reklam.

Sprawdza pieć rzeczy, ktore jury ocenia wprost:
  1. on-premise — brak zewnetrznych adresow sieciowych w kodzie,
  2. brak zewnetrznych/platnych API modeli,
  3. brak zaleznosci na licencjach blokujacych wdrozenie (AGPL / SSPL / gemma),
  4. brak sekretow w repozytorium,
  5. przypiete wersje zaleznosci (weryfikowalny lancuch dostaw).

Uruchomienie z katalogu glownego repozytorium:
    python tools/check_compliance.py

Kod wyjscia 0 = zgodne. Uruchamiac przed kazdym commitem i obowiazkowo
przed oddaniem projektu.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Adresy dozwolone: lokalne, nazwy serwisow z docker-compose, atrapy testowe,
# oraz domeny w komentarzach dokumentacyjnych.
# Domeny zarezerwowane do przykladow i testow (RFC 2606, RFC 6761). Nigdy nie
# wskazuja prawdziwej uslugi, wiec nie moga lamac wymogu on-premise.
RESERVED_TLDS = (".example", ".invalid", ".test", ".localhost")

# CELE SCRAPOWANIA i oficjalne rejestry — dozwolone SWIADOMIE.
#
# "On-premise" z par. 5 specyfikacji znaczy: brak zewnetrznych API modeli
# i brak hostowanych zamiennikow naszych wlasnych komponentow (bazy, kolejki,
# inferencji). NIE znaczy "nigdy nie dotykaj internetu" — produktem jest
# monitor tresci w internecie, wiec scraper MUSI siegac do serwisow, ktore
# monitoruje. Rejestr KNF jest wprost wskazany w zalacznikach do zadania
# jako zrodlo danych o autoryzowanych firmach inwestycyjnych.
#
# Lista jest jawna i audytowalna: to zarazem zbior zrodel, ktore monitorujemy.
# Dowolny INNY zewnetrzny adres nadal jest zglaszany.
SCRAPING_TARGETS = {
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com",
    "instagram.com", "www.instagram.com",
    "tiktok.com", "www.tiktok.com",
    "knf.gov.pl", "www.knf.gov.pl",
}

ALLOWED_HOSTS = {
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "host.docker.internal",
    # nazwy serwisow wewnatrz sieci docker-compose
    "ollama",
    "api",
    "web",
    "postgres",
    "valkey",
    "seaweedfs",
    "nginx",
    "analyzer",
    "scraper",
    # atrapy w testach i przykladach
    "fake",
    "example.invalid",
}

# Pakiety i obrazy, ktorych nie wolno uzyc — licencje blokujace wdrozenie
# w administracji publicznej. Patrz par. 3.1 design doca.
FORBIDDEN_DEPS = {
    "minio": "AGPLv3 — uzyj SeaweedFS (Apache-2.0)",
    "redis:7.4": "SSPLv1/RSALv2 — nie jest licencja OSI; uzyj Valkey (BSD-3)",
    "redis:8": "AGPLv3 — silne copyleft; uzyj Valkey (BSD-3)",
    "garage": "AGPLv3 — uzyj SeaweedFS",
    "mmlw-retrieval-roberta-large-v2": "licencja gemma — nie jest czystym OSS",
}

# Zewnetrzne API modeli i hostowane inferencje — lamia wymog on-premise.
# Markery liniowe, bo te definicje Z KONIECZNOSCI zawieraja zakazane wzorce.
# Celowo marker liniowy, a nie plikowy: reszta tego pliku ma byc skanowana.
FORBIDDEN_PATTERNS = {
    r"\bopenai\b": "zewnetrzne API modelu",  # compliance:allow
    r"\banthropic\b": "zewnetrzne API modelu",  # compliance:allow
    r"api\.openai\.com": "zewnetrzne API modelu",  # compliance:allow
    r"generativelanguage\.googleapis": "zewnetrzne API modelu",  # compliance:allow
    r"\breplicate\b": "hostowana inferencja",  # compliance:allow
    r"\bgroq\b": "hostowana inferencja",  # compliance:allow
    r"api-inference\.huggingface": "hostowana inferencja",  # compliance:allow
    r"\bcolab\b": "hostowane srodowisko — lamie on-premise",  # compliance:allow
    r"\bngrok\b": "tunel do internetu — lamie on-premise",  # compliance:allow
}

SECRET_FILES = {".env", "credentials.json", "secrets.json"}
SECRET_PATTERNS = {
    r"sk-[A-Za-z0-9]{20,}": "klucz API w kodzie",
    r"ghp_[A-Za-z0-9]{20,}": "token GitHub w kodzie",
}

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".yml", ".yaml", ".json", ".txt"}

# Pliki BEZ rozszerzenia albo z nietypowym, ktore mimo to musza byc skanowane.
# Dockerfile moze odwolac sie do zewnetrznego obrazu lub adresu, a .env.example
# to najlatwiejsze miejsce na przypadkowe wklejenie prawdziwego sekretu.
SOURCE_NAMES = {"Dockerfile", ".env.example", ".dockerignore", "Makefile"}
SKIP_DIRS = {".venv", "node_modules", "graphify-out", "DocsTaskINWESTWATCH"}

# Lockfile menedzerow paczek zapisuje adres rejestru, z ktorego pobrano kazda
# paczke (`resolved`, `funding`). To pochodzenie zaleznosci przy budowie, a nie
# wywolanie sieci w dzialajacej aplikacji - pomijamy je TYLKO w kontroli adresow.
# Sekrety, licencje i przypiete wersje dalej obejmuja te pliki.
HOST_CHECK_SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

# Jawne wyjatki. Potrzebne, bo pliki, ktore OPISUJA zakazane wzorce (testy
# tego checkera, dokumentacja licencji), same je zawieraja i checker zglaszalby
# sam siebie.
#
#   # compliance:allow            — pomija JEDNA linie
#   # compliance:allow-file       — pomija caly plik (w pierwszych 30 liniach)
#
# Wyjatki plikowe sa WYPISYWANE w raporcie, zeby nie dalo sie po cichu
# wyciszyc prawdziwego problemu o 4 w nocy.
ALLOW_LINE_MARKER = "compliance:allow"
ALLOW_FILE_MARKER = "compliance:allow-file"


def is_allowlisted_file(path: Path) -> bool:
    if not path.exists():
        return False
    if path.suffix not in SOURCE_SUFFIXES and path.name not in SOURCE_NAMES:
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:30]
    except OSError:
        return False
    return any(ALLOW_FILE_MARKER in line for line in head)


def _scannable(files: list[Path]) -> list[Path]:
    return [
        f
        for f in files
        if (f.suffix in SOURCE_SUFFIXES or f.name in SOURCE_NAMES)
        and f.exists()
        and not is_allowlisted_file(f)
    ]


def _lines(path: Path) -> list[tuple[int, str]]:
    """Linie pliku z numeracja, bez linii oznaczonych markerem."""
    out: list[tuple[int, str]] = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
    ):
        if ALLOW_LINE_MARKER in line:
            continue
        out.append((lineno, line))
    return out


def _rel(p: Path) -> str:
    """Sciezka do wyswietlenia, odporna na pliki spoza repozytorium.

    `Path.relative_to` rzuca ValueError dla sciezki poza ROOT — checker ma
    zglaszac problemy, a nie wywracac sie wyjatkiem.
    """
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def tracked_files() -> list[Path]:
    """Tylko pliki sledzone w gicie — to jest to, co faktycznie oddajemy."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    files = []
    for line in out.stdout.splitlines():
        p = ROOT / line
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        files.append(p)
    return files


def _host_allowed(host: str) -> bool:
    """Czy adres jest dozwolony wobec wymogu on-premise.

    Trzy kategorie dozwolone: lokalne i nazwy serwisow compose (ALLOWED_HOSTS),
    domeny zarezerwowane do przykladow (RESERVED_TLDS) oraz jawnie zadeklarowane
    cele scrapowania i rejestry (SCRAPING_TARGETS). Wszystko inne jest zglaszane.
    """
    h = host.lower().rstrip(".")
    if h in ALLOWED_HOSTS or h in SCRAPING_TARGETS:
        return True
    return h.endswith(RESERVED_TLDS)


def check_external_hosts(files: list[Path]) -> list[str]:
    problems: list[str] = []
    url_re = re.compile(r"https?://([A-Za-z0-9_.\-]+)")
    for f in _scannable(files):
        if f.name in HOST_CHECK_SKIP_NAMES:
            continue
        for lineno, line in _lines(f):
            for host in url_re.findall(line):
                if _host_allowed(host):
                    continue
                problems.append(
                    f"{_rel(f)}:{lineno} zewnetrzny adres: {host}"
                )
    return problems


def check_forbidden_patterns(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in _scannable(files):
        for lineno, line in _lines(f):
            lowered = line.lower()
            for pattern, why in FORBIDDEN_PATTERNS.items():
                if re.search(pattern, lowered):
                    problems.append(f"{_rel(f)}:{lineno} {pattern} — {why}")
    return problems


def check_forbidden_deps(files: list[Path]) -> list[str]:
    problems: list[str] = []
    targets = [
        f
        for f in _scannable(files)
        if f.name in {"requirements.txt", "requirements-dev.txt", "package.json"}
        or f.name.startswith("docker-compose")
    ]
    for f in targets:
        for lineno, line in _lines(f):
            lowered = line.lower()
            for dep, why in FORBIDDEN_DEPS.items():
                if dep in lowered:
                    problems.append(f"{_rel(f)}:{lineno} {dep} — {why}")
    return problems


def check_secrets(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        if f.name in SECRET_FILES:
            problems.append(f"{_rel(f)}: plik z sekretami w repozytorium")
    for f in _scannable(files):
        for lineno, line in _lines(f):
            for pattern, why in SECRET_PATTERNS.items():
                if re.search(pattern, line):
                    problems.append(f"{_rel(f)}:{lineno} {why}")
    return problems


def check_pinned_versions(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in _scannable(files):
        if f.name not in {"requirements.txt", "requirements-dev.txt"}:
            continue
        for lineno, line in _lines(f):
            stripped = line.split("#")[0].strip()
            if not stripped or stripped.startswith("-"):
                continue
            if "==" not in stripped:
                problems.append(
                    f"{_rel(f)}:{lineno} wersja nieprzypieta: {stripped}"
                )
    return problems


CHECKS = [
    ("on-premise: brak zewnetrznych adresow", check_external_hosts),
    ("brak zewnetrznych API modeli", check_forbidden_patterns),
    ("licencje zaleznosci i obrazow", check_forbidden_deps),
    ("brak sekretow w repozytorium", check_secrets),
    ("przypiete wersje zaleznosci", check_pinned_versions),
]


def main() -> int:
    files = tracked_files()
    excluded = [f for f in files if is_allowlisted_file(f)]

    print(f"Sprawdzam {len(files)} plikow sledzonych w gicie.")
    if excluded:
        # Wypisujemy JAWNIE, zeby wyjatek nie byl cichy. Jesli na tej liscie
        # pojawi sie plik produkcyjny — to jest problem, nie wygoda.
        print(f"Pominiete przez {ALLOW_FILE_MARKER} ({len(excluded)}):")
        for f in excluded:
            print(f"  - {_rel(f)}")
    print()

    total = 0
    for name, check in CHECKS:
        problems = check(files)
        total += len(problems)
        mark = "OK  " if not problems else "BLAD"
        print(f"[{mark}] {name}")
        for p in problems:
            print(f"         {p}")

    print()
    if total:
        print(f"ZGODNOSC NARUSZONA: {total} problem(ow). Napraw przed oddaniem.")
        return 1

    print("Zgodne z wymogami technicznymi specyfikacji (par. 5):")
    print("  - caly stos dziala on-premise, bez zewnetrznych adresow,")
    print("  - zero platnych/zewnetrznych API modeli,")
    print("  - brak zaleznosci na AGPL / SSPL / gemma,")
    print("  - brak sekretow w repozytorium,")
    print("  - wersje zaleznosci przypiete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
