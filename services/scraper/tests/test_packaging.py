"""Obraz scrapera zawiera wszystkie moduly, ktore worker importuje; worker czyta SCRAPER_QUEUES."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import worker

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = ("worker.py", "jobs.py", "scheduler.py")


def _local_imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    return {n for n in names if (ROOT / f"{n}.py").is_file() or (ROOT / n / "__init__.py").is_file()}


def _reachable() -> set[str]:
    todo, seen = [p.removesuffix(".py") for p in ENTRYPOINTS], set()
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        pkg = ROOT / name
        files = sorted(pkg.glob("*.py")) if pkg.is_dir() else [ROOT / f"{name}.py"]
        for f in files:
            todo += list(_local_imports(f))
    return seen


def _copied() -> set[str]:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8").replace("\\\n", " ")
    out: set[str] = set()
    for line in text.splitlines():
        if line.startswith("COPY "):
            out |= {m.rstrip("/").removesuffix(".py") for m in re.findall(r"scraper/([\w./]+)", line)}
    return out


def test_dockerfile_copies_every_module_reachable_from_worker():
    missing = _reachable() - _copied()
    assert not missing, f"Dockerfile nie kopiuje: {sorted(missing)}"
    assert "rules_det" in _reachable()  # regresja: ModuleNotFoundError w _enqueue_analysis


@pytest.mark.parametrize(("value", "expected"), [
    (None, ("q:ingest", "q:render")),
    ("", ("q:ingest", "q:render")),
    ("q:render", ("q:render",)),
    (" q:ingest , q:render ", ("q:ingest", "q:render")),
])
def test_queues_from_env(value, expected):
    assert worker.queues_from_env(value) == expected


def test_queues_from_env_rejects_unknown_queue():
    with pytest.raises(ValueError):
        worker.queues_from_env("q:gpu")
