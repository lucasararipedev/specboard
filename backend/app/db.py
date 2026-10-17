from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import DateTime, Engine, create_engine, event, inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class UTCDateTime(TypeDecorator):
    """Grava em UTC sem fuso e devolve sempre com tzinfo=UTC (o SQLite perde o fuso)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None else None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_engine(url: str) -> Engine:
    is_sqlite = url.startswith("sqlite")
    if url.startswith("sqlite:///"):
        path = url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, connect_args={"check_same_thread": False} if is_sqlite else {})

    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(conn, _record):
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.close()

    return engine


MIGRATIONS = Path(__file__).parent / "migrations"


def run_migrations(engine: Engine) -> None:
    """Leva o banco até a última migração. Banco criado antes do Alembic (create_all) é marcado como 0001."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    with engine.connect() as conn:
        # No SQLite, recriar uma tabela (modo batch do Alembic) com foreign_keys=ON dispararia o ON DELETE das
        # tabelas filhas. O PRAGMA só vale fora de transação, por isso vem antes do begin.
        sqlite = conn.dialect.name == "sqlite"
        if sqlite:
            conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
            conn.commit()
        with conn.begin():
            config.attributes["connection"] = conn
            tables = inspect(conn).get_table_names()
            if "projects" in tables and "alembic_version" not in tables:
                command.stamp(config, "0001")
            command.upgrade(config, "head")
        if sqlite:
            conn.exec_driver_sql("PRAGMA foreign_keys=ON")
            conn.commit()
