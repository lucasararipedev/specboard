"""Versões (releases + cards.release_id), sessões de agente (painel Agora) e perfil do usuário.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "releases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("position", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "name"),
    )
    op.create_index("ix_releases_project_id", "releases", ["project_id"])

    # Coluna nova em tabela existente. No SQLite, ADD COLUMN com REFERENCES funciona direto; o modo "batch"
    # recriaria a tabela cards e, com foreign_keys=ON, o DROP anularia o card_id de perguntas e atividades.
    if op.get_context().dialect.name == "sqlite":
        op.execute("ALTER TABLE cards ADD COLUMN release_id INTEGER REFERENCES releases(id) ON DELETE SET NULL")
    else:
        op.add_column("cards", sa.Column("release_id", sa.Integer(), nullable=True))
        op.create_foreign_key(None, "cards", "releases", ["release_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_cards_release_id", "cards", ["release_id"])

    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("client", sa.String(64), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cwd", sa.String(500), nullable=False),
        sa.Column("doing", sa.String(300), nullable=False),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_agent_sessions_key", "agent_sessions", ["key"], unique=True)
    op.create_index("ix_agent_sessions_last_seen_at", "agent_sessions", ["last_seen_at"])

    op.create_table(
        "profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("avatar", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("profile")
    op.drop_table("agent_sessions")
    op.drop_index("ix_cards_release_id", "cards")
    with op.batch_alter_table("cards") as batch:
        batch.drop_column("release_id")
    op.drop_table("releases")
