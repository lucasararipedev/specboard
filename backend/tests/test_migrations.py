import sqlite3

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

# Esquema criado pelo create_all antes do Alembic (v1), com um card ligado a pergunta e atividade.
OLD_SCHEMA = """
CREATE TABLE projects (id INTEGER PRIMARY KEY, slug VARCHAR(64) NOT NULL, name VARCHAR(200) NOT NULL,
  summary TEXT NOT NULL, spec TEXT NOT NULL, repo VARCHAR(500) NOT NULL, archived BOOLEAN NOT NULL,
  created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL);
CREATE UNIQUE INDEX ix_projects_slug ON projects (slug);
CREATE TABLE cards (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(300) NOT NULL, description TEXT NOT NULL, status VARCHAR(16) NOT NULL, priority INTEGER NOT NULL,
  position FLOAT NOT NULL, labels JSON NOT NULL, spec_ref VARCHAR(200) NOT NULL, due_date DATE,
  created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, started_at DATETIME, done_at DATETIME);
CREATE TABLE questions (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL, question TEXT NOT NULL, context TEXT NOT NULL,
  options JSON NOT NULL, answer TEXT NOT NULL, status VARCHAR(16) NOT NULL, asked_by VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL, answered_at DATETIME);
CREATE TABLE activities (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL, actor VARCHAR(64) NOT NULL, kind VARCHAR(32) NOT NULL,
  message TEXT NOT NULL, created_at DATETIME NOT NULL);
INSERT INTO projects VALUES (1, 'antigo', 'Antigo', '', '# Spec', '', 0, '2026-10-01 10:00:00', '2026-10-01 10:00:00');
INSERT INTO cards VALUES (7, 1, 'Login', '', 'todo', 1, 1.0, '[]', '', NULL,
  '2026-10-01 10:00:00', '2026-10-01 10:00:00', NULL, NULL);
INSERT INTO questions VALUES (1, 1, 7, 'Google ou e-mail?', '', '[]', '', 'open', 'claude', '2026-10-01 10:00:00', NULL);
INSERT INTO activities VALUES (1, 1, 7, 'claude', 'created', 'Criou #7', '2026-10-01 10:00:00');
"""


def test_database_from_before_alembic_is_upgraded_without_losing_data(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(OLD_SCHEMA)

    app = create_app(Settings(database_url=f"sqlite:///{path}"))
    client = TestClient(app, base_url="http://localhost", headers={"X-Actor": "claude"})

    card = client.get("/api/cards/7").json()
    assert card["title"] == "Login" and card["labels"] == []
    assert client.get("/api/projects/antigo/questions").json()[0]["card_id"] == 7
    assert client.get("/api/projects/antigo/activity?card_id=7").json()[0]["message"] == "Criou #7"

    assert client.patch("/api/cards/7", json={"labels": ["v1"]}).json()["labels"] == ["v1"]
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0003"

    # Subir de novo não reaplica nada.
    create_app(Settings(database_url=f"sqlite:///{path}"))


def test_versions_from_0002_become_labels_and_links_survive(tmp_path):
    """0003 recria a tabela cards: perguntas e atividades continuam apontando para os cards."""
    from alembic import command
    from alembic.config import Config

    from app.db import MIGRATIONS, make_engine

    path = tmp_path / "v2.db"
    engine = make_engine(f"sqlite:///{path}")
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    with engine.begin() as conn:
        config.attributes["connection"] = conn
        command.upgrade(config, "0002")
    engine.dispose()
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
INSERT INTO projects VALUES (1, 'antigo', 'Antigo', '', '', '', 0, '2026-10-01 10:00:00', '2026-10-01 10:00:00');
INSERT INTO releases VALUES (1, 1, 'v0.2', '', 'active', NULL, NULL, 1.0, '2026-10-01 10:00:00', '2026-10-01 10:00:00');
INSERT INTO cards (id, project_id, title, description, status, priority, position, labels, spec_ref, created_at,
  updated_at, release_id)
  VALUES (7, 1, 'Login', '', 'todo', 1, 1.0, '["bug"]', '', '2026-10-01 10:00:00', '2026-10-01 10:00:00', 1);
INSERT INTO questions VALUES (1, 1, 7, 'Google ou e-mail?', '', '[]', '', 'open', 'claude', '2026-10-01 10:00:00', NULL);
INSERT INTO activities VALUES (1, 1, 7, 'claude', 'created', 'Criou #7', '2026-10-01 10:00:00');
"""
        )

    client = TestClient(create_app(Settings(database_url=f"sqlite:///{path}")), base_url="http://localhost")
    assert client.get("/api/cards/7").json()["labels"] == ["bug", "v0.2"]
    assert client.get("/api/projects/antigo/questions").json()[0]["card_id"] == 7
    assert client.get("/api/projects/antigo/activity?card_id=7").json()[0]["message"] == "Criou #7"
    with sqlite3.connect(path) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        columns = {r[1] for r in conn.execute("PRAGMA table_info(cards)")}
        assert "releases" not in tables and "release_id" not in columns
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
