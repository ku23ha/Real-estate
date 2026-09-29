import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.postgresql
def test_postgresql_deal_and_property_survive_restart(monkeypatch) -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated disposable PostgreSQL test database.")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
        pytest.fail("TEST_DATABASE_URL must use a PostgreSQL URL.")

    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")

    with TestClient(app) as first_client:
        created = first_client.post(
            "/api/v1/deals",
            json={"name": "PostgreSQL restart case", "property": {"address": "Test address"}},
        ).json()

    with TestClient(app) as restarted_client:
        retrieved = restarted_client.get(f"/api/v1/deals/{created['id']}")

    assert retrieved.status_code == 200
    assert retrieved.json()["name"] == "PostgreSQL restart case"
    assert retrieved.json()["property"]["address"] == "Test address"
