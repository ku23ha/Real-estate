from pathlib import Path
import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.main import app


API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_url = f"sqlite:///{(tmp_path / 'rethos-test.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    alembic_config = Config(str(API_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_url = os.environ.get("TEST_DATABASE_URL") or (
        f"sqlite:///{(tmp_path / 'rethos-restart-test.db').as_posix()}"
    )
    monkeypatch.setenv("DATABASE_URL", database_url)

    alembic_config = Config(str(API_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    return database_url
