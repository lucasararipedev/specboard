"""Esquema da v1 (antes do Alembic era criado por create_all).

Bancos criados antes do Alembic já têm estas tabelas: db.run_migrations marca esta revisão sem rodá-la.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("spec", sa.Text(), nullable=False),
        sa.Column("repo", sa.String(500), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)

    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("position", sa.Float(), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("spec_ref", sa.String(200), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("done_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_cards_project_id", "cards", ["project_id"])
    op.create_index("ix_cards_status", "cards", ["status"])

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("asked_by", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_questions_project_id", "questions", ["project_id"])
    op.create_index("ix_questions_status", "questions", ["status"])

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_activities_project_id", "activities", ["project_id"])
    op.create_index("ix_activities_created_at", "activities", ["created_at"])


def downgrade() -> None:
    for table in ("activities", "questions", "cards", "projects"):
        op.drop_table(table)
