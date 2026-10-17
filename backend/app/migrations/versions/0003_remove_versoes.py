"""Remove as versões (releases): versão virou etiqueta do card, e o board filtra por etiquetas.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Versões que existiam viram etiqueta nos cards delas, para nada se perder.
    cards = sa.table(
        "cards", sa.column("id", sa.Integer), sa.column("labels", sa.JSON), sa.column("release_id", sa.Integer)
    )
    releases = sa.table("releases", sa.column("id", sa.Integer), sa.column("name", sa.String))
    conn = op.get_bind()
    query = sa.select(cards.c.id, cards.c.labels, releases.c.name).join_from(
        cards, releases, cards.c.release_id == releases.c.id
    )
    for card_id, labels, name in conn.execute(query).all():
        labels = list(labels or [])
        if name not in labels:
            conn.execute(cards.update().where(cards.c.id == card_id).values(labels=[*labels, name]))

    op.drop_index("ix_cards_release_id", "cards")
    # Recria a tabela cards sem a coluna (o SQLite não apaga coluna com chave estrangeira). É seguro porque
    # db.run_migrations desliga foreign_keys durante as migrações.
    with op.batch_alter_table("cards") as batch:
        batch.drop_column("release_id")
    op.drop_table("releases")


def downgrade() -> None:
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
    with op.batch_alter_table("cards") as batch:
        batch.add_column(sa.Column("release_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_cards_release_id", "releases", ["release_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_cards_release_id", "cards", ["release_id"])
