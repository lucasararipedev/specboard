import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def make_client(tmp_path):
    def _make(**overrides) -> TestClient:
        settings = Settings(database_url=f"sqlite:///{tmp_path}/test.db", **overrides)
        return TestClient(create_app(settings), headers={"X-Actor": "claude"})

    return _make


@pytest.fixture
def client(make_client) -> TestClient:
    return make_client()


@pytest.fixture
def project(client) -> dict:
    res = client.post("/api/projects", json={"name": "Meu SaaS", "summary": "Agenda para barbearias"})
    assert res.status_code == 201
    return res.json()
