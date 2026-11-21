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
FORBIDDEN_PATTERNS = {
    r"\bopenai\b": "zewnetrzne API modelu",
    r"\banthropic\b": "zewnetrzne API modelu",
    r"api\.openai\.com": "zewnetrzne API modelu",
    r"generativelanguage\.googleapis": "zewnetrzne API modelu",
    r"\breplicate\b": "hostowana inferencja",
    r"\bgroq\b": "hostowana inferencja",
    r"api-inference\.huggingface": "hostowana inferencja",
    r"\bcolab\b": "hostowane srodowisko — lamie on-premise",
    r"\bngrok\b": "tunel do internetu — lamie on-premise",
}

SECRET_FILES = {".env", "credentials.json", "secrets.json"}
SECRET_PATTERNS = {
    r"sk-[A-Za-z0-9]{20,}": "klucz API w kodzie",
    r"ghp_[A-Za-z0-9]{20,}": "token GitHub w kodzie",
}

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".yml", ".yaml", ".json", ".txt"}
SKIP_DIRS = {".venv", "node_modules", "graphify-out", "DocsTaskINWESTWATCH"}


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


def check_external_hosts(files: list[Path]) -> list[str]:
    problems: list[str] = []
    url_re = re.compile(r"https?://([A-Za-z0-9_.\-]+)")
    for f in files:
        if f.suffix not in SOURCE_SUFFIXES or not f.exists():
            continue
        for lineno, line in enumerate(
            f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            for host in url_re.findall(line):
                if host in ALLOWED_HOSTS:
                    continue
                problems.append(
                    f"{_rel(f)}:{lineno} zewnetrzny adres: {host}"
                )
    return problems


def check_forbidden_patterns(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        if f.suffix not in SOURCE_SUFFIXES or not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore").lower()
        for pattern, why in FORBIDDEN_PATTERNS.items():
            if re.search(pattern, text):
                problems.append(f"{_rel(f)}: {pattern} — {why}")
    return problems


def check_forbidden_deps(files: list[Path]) -> list[str]:
    problems: list[str] = []
    targets = [
        f
        for f in files
        if f.name in {"requirements.txt", "requirements-dev.txt", "package.json"}
        or f.name.startswith("docker-compose")
    ]
    for f in targets:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore").lower()
        for dep, why in FORBIDDEN_DEPS.items():
            if dep in text:
                problems.append(f"{_rel(f)}: {dep} — {why}")
    return problems


def check_secrets(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        if f.name in SECRET_FILES:
            problems.append(f"{_rel(f)}: plik z sekretami w repozytorium")
        if f.suffix not in SOURCE_SUFFIXES or not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for pattern, why in SECRET_PATTERNS.items():
            if re.search(pattern, text):
                problems.append(f"{_rel(f)}: {why}")
    return problems


def check_pinned_versions(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        if f.name not in {"requirements.txt", "requirements-dev.txt"} or not f.exists():
            continue
        for lineno, line in enumerate(
            f.read_text(encoding="utf-8").splitlines(), 1
        ):
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
    print(f"Sprawdzam {len(files)} plikow sledzonych w gicie.\n")

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
