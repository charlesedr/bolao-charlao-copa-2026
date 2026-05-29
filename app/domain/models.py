from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.domain.enums import StatusPartida, StatusUsuario


def _ts(**kwargs) -> Column:
    """Coluna datetime timezone-aware (TIMESTAMPTZ)."""
    return Column(DateTime(timezone=True), **kwargs)


# ---------------------------------------------------------------------------
# Estrutura da Copa
# ---------------------------------------------------------------------------
class Grupo(SQLModel, table=True):
    __tablename__ = "grupos"
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(sa_column=Column(String(1), unique=True, nullable=False))  # A..L


class Selecao(SQLModel, table=True):
    __tablename__ = "selecoes"
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    codigo_fifa: str = Field(sa_column=Column(String(3), unique=True, nullable=False, index=True))
    nome: str = Field(sa_column=Column(String(80), unique=True, nullable=False))
    nome_pt: str = Field(max_length=80)
    grupo_id: int | None = Field(default=None, foreign_key="grupos.id", index=True)
    confederacao: str | None = Field(default=None, max_length=20)
    bandeira_url: str | None = None


class Partida(SQLModel, table=True):
    __tablename__ = "partidas"
    __table_args__ = (
        CheckConstraint(
            "placar_mandante IS NULL OR (placar_mandante >= 0 AND placar_mandante <= 30)",
            name="ck_partida_placar_mand",
        ),
        CheckConstraint(
            "placar_visitante IS NULL OR (placar_visitante >= 0 AND placar_visitante <= 30)",
            name="ck_partida_placar_vis",
        ),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(sa_column=Column(String(20), unique=True, nullable=False, index=True))
    fase: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    grupo_id: int | None = Field(default=None, foreign_key="grupos.id", index=True)

    # Seleções — NULL até o slot do mata-mata ser preenchido
    mandante_id: int | None = Field(default=None, foreign_key="selecoes.id", index=True)
    visitante_id: int | None = Field(default=None, foreign_key="selecoes.id", index=True)

    # Descrição do slot (ex.: "1A", "2B", "3:C/E/F/H/I", "V74", "P101")
    slot_mandante: str | None = Field(default=None, max_length=20)
    slot_visitante: str | None = Field(default=None, max_length=20)

    # Linhagem para avanço automático no mata-mata
    origem_mandante_id: int | None = Field(default=None, foreign_key="partidas.id")
    origem_mandante_tipo: str | None = Field(default=None, max_length=10)  # vencedor|perdedor
    origem_visitante_id: int | None = Field(default=None, foreign_key="partidas.id")
    origem_visitante_tipo: str | None = Field(default=None, max_length=10)

    data_hora: datetime = Field(sa_column=_ts(nullable=False, index=True))

    status: str = Field(
        sa_column=Column(
            String(20),
            nullable=False,
            server_default=StatusPartida.NAO_INICIADO.value,
            index=True,
        )
    )
    placar_mandante: int | None = None
    placar_visitante: int | None = None
    classificado_id: int | None = Field(default=None, foreign_key="selecoes.id")

    # Fair play (critério 7 de desempate) — admin preenche; default 0
    fp_amarelos_mandante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_verm_2amarelo_mandante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_verm_direto_mandante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_amarelo_verm_mandante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_amarelos_visitante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_verm_2amarelo_visitante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_verm_direto_visitante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))
    fp_amarelo_verm_visitante: int = Field(default=0, sa_column=Column(Integer, server_default="0"))

    estadio: str | None = Field(default=None, max_length=80)
    cidade: str | None = Field(default=None, max_length=60)
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=_ts(nullable=False, server_default=func.now(), onupdate=func.now())
    )


# ---------------------------------------------------------------------------
# Usuários e palpites
# ---------------------------------------------------------------------------
class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=80)
    apelido: str = Field(sa_column=Column(String(40), unique=True, nullable=False, index=True))
    email: str = Field(sa_column=Column(String(120), unique=True, nullable=False, index=True))
    senha_hash: str = Field(max_length=255)
    status: str = Field(
        sa_column=Column(
            String(20), nullable=False, server_default=StatusUsuario.PENDENTE.value, index=True
        )
    )
    is_admin: bool = Field(default=False)
    senha_temporaria: bool = Field(default=False)
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=_ts(nullable=False, server_default=func.now(), onupdate=func.now())
    )
    ultimo_login: datetime | None = Field(default=None, sa_column=_ts(nullable=True))


class Palpite(SQLModel, table=True):
    __tablename__ = "palpites"
    __table_args__ = (
        UniqueConstraint("usuario_id", "partida_id", name="uq_palpite_usuario_partida"),
        CheckConstraint("gols_mandante >= 0 AND gols_mandante <= 30", name="ck_palpite_gols_mand"),
        CheckConstraint("gols_visitante >= 0 AND gols_visitante <= 30", name="ck_palpite_gols_vis"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)
    partida_id: int = Field(foreign_key="partidas.id", index=True)
    gols_mandante: int
    gols_visitante: int
    classificado_id: int | None = Field(default=None, foreign_key="selecoes.id")
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=_ts(nullable=False, server_default=func.now(), onupdate=func.now())
    )


class PontuacaoPartida(SQLModel, table=True):
    __tablename__ = "pontuacao_partidas"
    __table_args__ = (
        UniqueConstraint("usuario_id", "partida_id", name="uq_pont_user_partida"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)
    partida_id: int = Field(foreign_key="partidas.id", index=True)
    pontos_gols_mandante: int = Field(default=0)
    pontos_gols_visitante: int = Field(default=0)
    pontos_resultado: int = Field(default=0)
    pontos_placar_exato: int = Field(default=0)
    pontos_classificado: int = Field(default=0)
    pontos_total: int = Field(default=0, index=True)
    calculado_em: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))


class ApostaClassificacaoFinal(SQLModel, table=True):
    __tablename__ = "aposta_classificacao_final"
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", unique=True)
    campeao_id: int | None = Field(default=None, foreign_key="selecoes.id")
    vice_id: int | None = Field(default=None, foreign_key="selecoes.id")
    terceiro_id: int | None = Field(default=None, foreign_key="selecoes.id")
    quarto_id: int | None = Field(default=None, foreign_key="selecoes.id")
    pontos_campeao: int = Field(default=0)
    pontos_vice: int = Field(default=0)
    pontos_terceiro: int = Field(default=0)
    pontos_quarto: int = Field(default=0)
    pontos_total: int = Field(default=0)
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=_ts(nullable=False, server_default=func.now(), onupdate=func.now())
    )


# ---------------------------------------------------------------------------
# Desempates
# ---------------------------------------------------------------------------
class DesempateManualGrupo(SQLModel, table=True):
    __tablename__ = "desempate_manual_grupo"
    __table_args__ = (
        UniqueConstraint("grupo_id", "posicao", name="uq_desempate_grupo_pos"),
        CheckConstraint("posicao BETWEEN 1 AND 4", name="ck_desempate_grupo_pos"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    grupo_id: int = Field(foreign_key="grupos.id", index=True)
    posicao: int
    selecao_id: int = Field(foreign_key="selecoes.id")
    motivo: str = Field(max_length=200)
    admin_id: int = Field(foreign_key="usuarios.id")
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))


class DesempateManualTerceiros(SQLModel, table=True):
    __tablename__ = "desempate_manual_terceiros"
    __table_args__ = (
        CheckConstraint("posicao BETWEEN 1 AND 12", name="ck_desempate_3os_pos"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    posicao: int = Field(unique=True)
    selecao_id: int = Field(foreign_key="selecoes.id")
    motivo: str = Field(max_length=200)
    admin_id: int = Field(foreign_key="usuarios.id")
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))


class DesempatePalpiteUsuario(SQLModel, table=True):
    __tablename__ = "desempate_palpite_usuario"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "contexto", "grupo_id", name="uq_desempate_user_ctx_grupo"
        ),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)
    contexto: str = Field(max_length=20)  # grupo | terceiros
    grupo_id: int | None = Field(default=None, foreign_key="grupos.id")
    ordem_json: list[int] = Field(sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=_ts(nullable=False, server_default=func.now(), onupdate=func.now())
    )


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------
class LogAdmin(SQLModel, table=True):
    __tablename__ = "logs_admin"
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    admin_id: int = Field(foreign_key="usuarios.id", index=True)
    acao: str = Field(sa_column=Column(String(50), nullable=False, index=True))
    entidade: str = Field(max_length=50)
    entidade_id: int | None = None
    detalhes: dict | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(sa_column=_ts(nullable=False, server_default=func.now(), index=True))
