"""add palpite_bracket_simulado

Tabela para guardar o bracket cascateado simulado em Minha Copa.
Não vale ponto no bolão — é só simulação visual do usuário.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "palpite_bracket_simulado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "partida_id",
            sa.Integer(),
            sa.ForeignKey("partidas.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "vencedor_id", sa.Integer(), sa.ForeignKey("selecoes.id"), nullable=False
        ),
        sa.Column("placar_vencedor", sa.Integer(), nullable=False),
        sa.Column("placar_perdedor", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "usuario_id", "partida_id", name="uq_brkt_sim_user_partida"
        ),
        sa.CheckConstraint(
            "placar_vencedor >= 0 AND placar_vencedor <= 30", name="ck_brkt_sim_pv"
        ),
        sa.CheckConstraint(
            "placar_perdedor >= 0 AND placar_perdedor <= 30", name="ck_brkt_sim_pp"
        ),
        sa.CheckConstraint(
            "placar_vencedor >= placar_perdedor", name="ck_brkt_sim_v_ge_p"
        ),
    )


def downgrade() -> None:
    op.drop_table("palpite_bracket_simulado")
