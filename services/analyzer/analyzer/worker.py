"""Worker kolejki q:gpu — cala logika zadania analizy.

`handle_job` jest czysta funkcja bez zaleznosci od RQ i Ollamy, wiec daje sie
w pelni testowac. RQ i redis importujemy LENIWIE w main(): modul musi sie
importowac takze bez tych bibliotek.
"""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import fields

from analyzer.api_client import ApiClient, ApiError
from pydantic import ValidationError

from analyzer.contracts import AdDocument, Finding, Relation, RuleResult
from analyzer.pipeline import AnalyzerConfig, EntityResolution, analyze

log = logging.getLogger("analyzer.worker")

QUEUE_NAME = "q:gpu"
DEFAULT_VALKEY_URL = "redis://valkey:6379/0"


def _build_resolution(raw: object) -> EntityResolution:
    """EntityResolution z opcjonalnego slownika; nieznane klucze ignorujemy."""
    if not isinstance(raw, dict):
        return EntityResolution()
    known = {f.name for f in fields(EntityResolution)}
    kwargs = {k: v for k, v in raw.items() if k in known and v is not None}
    if "publisher_relation" in kwargs:
        try:
            kwargs["publisher_relation"] = Relation(kwargs["publisher_relation"])
        except ValueError:
            del kwargs["publisher_relation"]  # nieznana relacja -> unknown
    try:
        return EntityResolution(**kwargs)
    except TypeError:
        return EntityResolution()


def _build_det_results(raw: object) -> list[RuleResult]:
    """Wyniki regul deterministycznych (4-8) policzone przez SCRAPER.

    Scraper ma RenderProbe i geometrie renderu, my nie — wiec nie powtarzamy
    tych pomiarow, tylko przyjmujemy gotowe wyniki w zadaniu kolejki.

    Pozycja, ktora nie przechodzi walidacji kontraktu, jest POMIJANA
    z ostrzezeniem, a nie wywraca calego zadania: lepiej ocenic dokument
    niepelnym zestawem regul (`coverage` to pokaze) niz nie ocenic go wcale.
    """
    if not isinstance(raw, list):
        return []
    out: list[RuleResult] = []
    for item in raw:
        try:
            out.append(RuleResult.model_validate(item))
        except ValidationError as exc:
            log.warning("Pomijam niepoprawny RuleResult ze scrapera: %s", exc)
    return out


def _resolve_document(payload: dict, api: ApiClient) -> tuple[AdDocument | None, str]:
    """Zwroc (dokument, rozpoznany ksztalt payloadu).

    Ksztalty: "document_id" (pobranie z API), "document" (zagniezdzony
    AdDocument), "flat" (plaski AdDocument — tak enqueuje scraper).
    Zly dokument -> (None, ksztalt) z ostrzezeniem, bez wyjatku.
    """
    raw_doc, shape = None, ""
    if isinstance(payload.get("document"), dict):
        raw_doc, shape = payload["document"], "document"
    elif "id" in payload and ("url" in payload or "text" in payload):
        raw_doc, shape = payload, "flat"
    if raw_doc is not None:
        try:
            return AdDocument.model_validate(raw_doc), shape
        except ValidationError as exc:
            log.warning("Niepoprawny AdDocument w payloadzie (%s): %s", shape, exc)
            return None, shape

    document_id = payload.get("document_id")
    if not document_id or not isinstance(document_id, str):
        log.warning("Zadanie bez document_id ani dokumentu - pomijam")
        return None, ""
    try:
        return api.get_document(document_id), "document_id"
    except ApiError as exc:
        log.error("Pobranie dokumentu %s nieudane: %s", document_id, exc)
        return None, "document_id"


def _save_finding(finding: Finding) -> None:
    """Fallback dla demo bez API: gdy FINDINGS_OUT_DIR, zapisz Finding do JSON."""
    out_dir = os.environ.get("FINDINGS_OUT_DIR")
    if not out_dir:
        return
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{finding.document_id}.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(finding.model_dump_json(indent=2))
    except OSError as exc:
        log.warning("Zapis findingu do %s nieudany: %s", out_dir, exc)


def handle_job(
    payload: dict, *, api: ApiClient, config: AnalyzerConfig | None = None
) -> Finding | None:
    """Obsluz jedno zadanie. Zwraca Finding albo None (brak dokumentu / blad API).

    Nigdy nie rzuca ApiError w gore: None oznacza zadanie do ponowienia.
    Akceptuje trzy ksztalty payloadu: {"document_id"}, {"document": {...}}
    oraz plaski AdDocument; kazdy moze miec "det_results".
    """
    if not isinstance(payload, dict):
        log.warning("Payload zadania nie jest slownikiem - pomijam")
        return None

    doc, shape = _resolve_document(payload, api)
    if doc is None:
        return None
    log.info("Payload rozpoznany jako %r (dokument %s)", shape, doc.id)

    entities = _build_resolution(payload.get("entity_resolution"))
    det_results = _build_det_results(payload.get("det_results"))
    finding = analyze(doc, entities, config, det_results=det_results)

    _save_finding(finding)
    try:
        api.post_finding(finding)
    except ApiError as exc:
        log.error("Wyslanie findingu dla %s nieudane: %s", doc.id, exc)
        return None
    return finding


def analyze_document(payload: dict) -> bool:
    """Punkt wejscia zadania RQ (nazwa zadania: analyze_document)."""
    return handle_job(payload, api=ApiClient()) is not None


def parse_args(argv: list[str] | None = None) -> str:
    """Nazwa kolejki z argumentow wiersza polecen.

    Flaga `--queue` istnieje, bo `pool.PoolExecutor` startuje workery wlasnie
    tak: `python -m analyzer.worker --queue <nazwa>`. Bez niej autoskaler mogl
    uruchomic wylacznie workery q:gpu, czyli nie dalby sie uzyc do kolejek
    q:ingest i q:render.
    """
    parser = argparse.ArgumentParser(prog="analyzer.worker")
    parser.add_argument(
        "--queue",
        default=QUEUE_NAME,
        help=f"nazwa kolejki RQ do obslugi (domyslnie {QUEUE_NAME})",
    )
    return parser.parse_args(argv).queue


def main(argv: list[str] | None = None) -> None:
    """Uruchom worker RQ na wskazanej kolejce (domyslnie q:gpu).

    Dlaczego na q:gpu dokladnie JEDEN worker: karta ma 8 GB VRAM, a Bielik
    i Whisper nie mieszcza sie w niej jednoczesnie. Pojedynczy worker szereguje
    zadania i gwarantuje, ze modele nigdy nie walcza o pamiec. Drugi worker
    na TEJ kolejce reaktywowalby dokladnie ten konflikt — dlatego
    `scaling.decide` przycina `gpu` do liczby endpointow Ollamy.
    Kolejki CPU (q:ingest, q:render) skaluja sie swobodnie.
    """
    # Importy leniwe: rq i redis nie sa potrzebne do testow ani do importu modulu.
    from redis import Redis
    from rq import Queue, Worker

    queue_name = parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    # Serwer /health w watku-demonie, ZANIM wejdziemy w blokujaca petle workera.
    # Bez tego HEALTHCHECK z Dockerfile puka w pustke i kontener jest unhealthy,
    # mimo ze worker dziala poprawnie.
    _start_health_server()

    conn = Redis.from_url(os.getenv("VALKEY_URL", DEFAULT_VALKEY_URL))
    queue = Queue(queue_name, connection=conn)
    logging.info("Worker wystartowal na kolejce %s", queue_name)
    Worker([queue], connection=conn).work()


def _start_health_server() -> None:
    """Wystaw /health obok petli workera. Awaria serwera health NIE moze
    przewrocic workera — analiza jest wazniejsza niz healthcheck."""
    import threading

    from analyzer.health import HEALTH_PORT, serve

    def run() -> None:
        try:
            serve(HEALTH_PORT)
        except OSError as exc:
            logging.warning("Nie udalo sie wystawic /health na %s: %s", HEALTH_PORT, exc)

    threading.Thread(target=run, name="health", daemon=True).start()
    logging.info("Endpoint /health nasluchuje na porcie %s", HEALTH_PORT)


if __name__ == "__main__":
    main()
