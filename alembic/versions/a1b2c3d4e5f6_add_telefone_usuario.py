"""add telefone usuario

Revision ID: a1b2c3d4e5f6
Revises: 850667bcae51
Create Date: 2026-05-29

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "850667bcae51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("telefone", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "telefone")
