import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def conn():
    """Wymaga DATABASE_URL do pustej bazy testowej (tabele sa czyszczone)."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("brak TEST_DATABASE_URL")
    from casedb import db

    c = db.connect(url)
    c.execute("DROP TABLE IF EXISTS ai_results, case_assets, case_content, cases, casedb_migrations")
    c.commit()
    db.migrate(c)
    yield c
    c.close()
