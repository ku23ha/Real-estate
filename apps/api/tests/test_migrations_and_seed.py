from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed


API_ROOT = Path(__file__).resolve().parents[1]


def test_migration_can_be_rolled_back(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'rollback.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(API_ROOT / "alembic.ini"))

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert {
            "deals", "properties", "organizations", "users", "developers",
            "locations", "micro_markets", "projects", "evidence_sources", "evidence",
        } <= tables
    finally:
        engine.dispose()

    command.downgrade(config, "base")

    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert not {
            "deals", "properties", "organizations", "users", "developers",
            "locations", "micro_markets", "projects",
            "evidence_sources", "evidence",
        } & tables
    finally:
        engine.dispose()


def test_evidence_migration_downgrade_and_reupgrade(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'evidence-migration.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(API_ROOT / "alembic.ini"))
    engine = create_engine(database_url)
    try:
        command.upgrade(config, "head")
        command.downgrade(config, "20260930_0002")
        tables = set(inspect(engine).get_table_names())
        assert {"deals", "properties", "projects"} <= tables
        assert not {"evidence", "evidence_sources"} & tables

        command.upgrade(config, "head")
        tables = set(inspect(engine).get_table_names())
        assert {"deals", "properties", "projects", "evidence", "evidence_sources"} <= tables
    finally:
        engine.dispose()


def test_seed_is_synthetic_and_idempotent(client: TestClient) -> None:
    assert seed() is True
    assert seed() is False

    response = client.get("/api/v1/deals")
    fixture = next(
        deal for deal in response.json() if deal["name"] == "Synthetic local development fixture"
    )
    assert fixture["property"]["address"] == "Synthetic example address"
    assert fixture["property"]["city"] is None
