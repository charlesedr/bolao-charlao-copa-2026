"""add partida origem e espn snapshot

Adiciona 4 colunas em partidas para suportar a sincronização automática
de resultados via ESPN, mantendo a possibilidade de override manual:

- dados_origem            VARCHAR(10) NULL  -- 'auto' | 'manual' | NULL
- dados_sincronizado_em   TIMESTAMPTZ NULL  -- última vez que o sync rodou
- placar_espn_mandante    INTEGER NULL      -- snapshot ESPN (mostra divergência)
- placar_espn_visitante   INTEGER NULL      -- snapshot ESPN

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-17
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "partidas", sa.Column("dados_origem", sa.String(length=10), nullable=True)
    )
    op.add_column(
        "partidas",
        sa.Column("dados_sincronizado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "partidas", sa.Column("placar_espn_mandante", sa.Integer(), nullable=True)
    )
    op.add_column(
        "partidas", sa.Column("placar_espn_visitante", sa.Integer(), nullable=True)
    )
    # Backfill: tudo que já tem placar é "manual" (foi você que lançou)
    op.execute(
        "UPDATE partidas SET dados_origem = 'manual' "
        "WHERE placar_mandante IS NOT NULL AND dados_origem IS NULL"
    )


def downgrade() -> None:
    op.drop_column("partidas", "placar_espn_visitante")
    op.drop_column("partidas", "placar_espn_mandante")
    op.drop_column("partidas", "dados_sincronizado_em")
    op.drop_column("partidas", "dados_origem")
