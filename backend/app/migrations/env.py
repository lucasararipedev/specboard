"""Ambiente do Alembic sem alembic.ini: a conexão vem de db.run_migrations (config.attributes["connection"])."""

from alembic import context

from app.db import Base

connection = context.config.attributes["connection"]
context.configure(connection=connection, target_metadata=Base.metadata)
with context.begin_transaction():
    context.run_migrations()
